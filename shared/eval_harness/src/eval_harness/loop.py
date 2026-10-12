"""One agent loop for every condition. Conditions differ in prompt, tools, and context."""

import json
import time
from typing import Any

from eval_harness.answers import parse_final_answer
from eval_harness.models import (
    Checker,
    Condition,
    ModelClient,
    RunLog,
    Task,
    ToolCall,
    ToolRecord,
    Verdict,
)


def run_trial(
    task: Task,
    condition: Condition,
    client: ModelClient,
    checker: Checker,
    *,
    trial: int,
    max_tool_calls: int = 8,
) -> RunLog:
    started = time.perf_counter()
    messages: list[dict[str, Any]] = [{"role": "system", "content": condition.system_prompt}]
    if condition.extra_context:
        messages.append({"role": "user", "content": condition.extra_context})
    messages.append({"role": "user", "content": task.prompt})
    tools = condition.executor.list_tools() if condition.executor is not None else None

    records: list[ToolRecord] = []
    input_tokens = 0
    output_tokens = 0
    final_text: str | None = None

    while True:
        response = client.complete(messages, tools)
        input_tokens += response.input_tokens
        output_tokens += response.output_tokens
        assistant: dict[str, Any] = {"role": "assistant", "content": response.content}
        if response.tool_calls:
            assistant["tool_calls"] = [
                {"id": call.id, "name": call.name, "arguments": call.arguments}
                for call in response.tool_calls
            ]
        messages.append(assistant)
        final_text = response.content

        if not response.tool_calls:
            break

        hit_limit = False
        for call in response.tool_calls:
            if len(records) >= max_tool_calls:
                hit_limit = True
                break
            result = _execute(condition, call)
            records.append(
                ToolRecord(id=call.id, name=call.name, arguments=call.arguments, result=result)
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.name,
                    "content": result,
                }
            )
        if hit_limit or len(records) >= max_tool_calls:
            break

    parsed = parse_final_answer(final_text)
    if parsed.ok:
        verdict = checker.check(task, parsed.value)
        final_answer = parsed.value
    else:
        verdict = Verdict(False, "format", parsed.detail)
        final_answer = None

    return RunLog(
        task_id=task.id,
        prompt=task.prompt,
        condition=condition.name,
        trial=trial,
        messages=messages,
        tool_calls=records,
        final_answer=final_answer,
        verdict=verdict,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        wall_time_s=time.perf_counter() - started,
    )


def _execute(condition: Condition, call: ToolCall) -> str:
    if condition.executor is None:
        return json.dumps({"error": "no executor configured"})
    try:
        return condition.executor.execute(call)
    except Exception as exc:
        return json.dumps({"error": type(exc).__name__, "message": str(exc)})
