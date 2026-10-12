"""H1: fake client, agent loop, run log, and numeric checking. No network."""

import json

import pytest

from eval_harness import (
    Condition,
    FakeClient,
    ModelResponse,
    NumericChecker,
    Task,
    ToolCall,
    parse_final_answer,
    run_trial,
)


class ScriptedExecutor:
    def __init__(self, tools: list[dict], results: dict[str, str]) -> None:
        self._tools = tools
        self._results = results
        self.calls: list[ToolCall] = []

    def list_tools(self) -> list[dict]:
        return self._tools

    def execute(self, call: ToolCall) -> str:
        self.calls.append(call)
        return self._results[call.name]


def _task(**overrides: object) -> Task:
    data: dict = {
        "id": "t1",
        "category": "numeric",
        "prompt": "Add the numbers.\nFINAL_ANSWER: <json>",
        "inputs": {"seed": 1, "values": [1, 2]},
        "reference": 3,
        "tolerance": 1e-6,
        "answer_format": "number",
    }
    data.update(overrides)
    return Task(**data)


def test_parse_final_answer_uses_only_the_last_json_line() -> None:
    text = 'working...\nFINAL_ANSWER: [1]\nFINAL_ANSWER: {"value": 3}\n'
    parsed = parse_final_answer(text)
    assert parsed.ok
    assert parsed.value == {"value": 3}


def test_parse_final_answer_rejects_missing_and_invalid_json() -> None:
    missing = parse_final_answer("the answer is 3")
    invalid = parse_final_answer("FINAL_ANSWER: {")
    assert not missing.ok
    assert missing.detail == "missing FINAL_ANSWER"
    assert not invalid.ok
    assert "not valid JSON" in invalid.detail


def test_numeric_checker_accepts_a_value_inside_tolerance() -> None:
    verdict = NumericChecker().check(_task(reference=1.0, tolerance=0.1), 1.05)
    assert verdict.passed
    assert verdict.error_kind is None


def test_numeric_checker_reports_mismatch_and_shape_errors() -> None:
    checker = NumericChecker()
    mismatch = checker.check(_task(reference=3, tolerance=0.0), 4)
    shape = checker.check(_task(reference=[1, 2], answer_format="vector"), [1])
    missing = checker.check(_task(), None)
    assert mismatch.passed is False
    assert mismatch.error_kind == "mismatch"
    assert shape.error_kind == "format"
    assert missing.error_kind == "format"


def test_loop_records_a_direct_answer_from_the_fake_client() -> None:
    client = FakeClient([ModelResponse(content="FINAL_ANSWER: 3", input_tokens=5, output_tokens=2)])
    log = run_trial(_task(), Condition("A", "be exact"), client, NumericChecker(), trial=0)

    assert log.verdict.passed
    assert log.final_answer == 3
    assert log.condition == "A"
    assert log.trial == 0
    assert log.input_tokens == 5
    assert log.output_tokens == 2
    assert log.tool_calls == []
    assert [message["role"] for message in log.messages] == ["system", "user", "assistant"]
    assert json.loads(json.dumps(log.to_dict()))["verdict"]["passed"] is True
    assert client.seen[0][1] is None


def test_loop_executes_a_tool_then_checks_the_final_answer() -> None:
    executor = ScriptedExecutor(
        tools=[{"name": "add"}],
        results={"add": "3"},
    )
    client = FakeClient(
        [
            ModelResponse(
                content=None,
                tool_calls=[ToolCall("c1", "add", {"a": 1, "b": 2})],
                input_tokens=4,
                output_tokens=1,
            ),
            ModelResponse(content="FINAL_ANSWER: 3", input_tokens=6, output_tokens=2),
        ]
    )
    condition = Condition("C", "use tools", executor=executor, extra_context="units: none")
    log = run_trial(_task(), condition, client, NumericChecker(), trial=2)

    assert log.verdict.passed
    assert log.input_tokens == 10
    assert log.output_tokens == 3
    assert log.tool_calls[0].name == "add"
    assert log.tool_calls[0].result == "3"
    assert executor.calls[0].arguments == {"a": 1, "b": 2}
    roles = [message["role"] for message in log.messages]
    assert roles == ["system", "user", "user", "assistant", "tool", "assistant"]
    assert log.messages[1]["content"] == "units: none"
    assert client.seen[1][1] == [{"name": "add"}]


def test_loop_stops_at_max_tool_calls_without_a_final_answer() -> None:
    executor = ScriptedExecutor(tools=[{"name": "add"}], results={"add": "3"})
    calls = [ToolCall("c1", "add", {}), ToolCall("c2", "add", {})]
    client = FakeClient([ModelResponse(content="still working", tool_calls=calls)])
    log = run_trial(
        _task(),
        Condition("B", "use tools", executor=executor),
        client,
        NumericChecker(),
        trial=1,
        max_tool_calls=1,
    )
    assert log.verdict.passed is False
    assert log.verdict.error_kind == "format"
    assert len(log.tool_calls) == 1
    assert len(executor.calls) == 1
    assert len(client.seen) == 1


def test_loop_turns_executor_errors_into_tool_results() -> None:
    class Broken:
        def list_tools(self) -> list[dict]:
            return []

        def execute(self, call: ToolCall) -> str:
            raise TimeoutError("too slow")

    client = FakeClient(
        [
            ModelResponse(tool_calls=[ToolCall("c1", "add", {})]),
            ModelResponse(content="FINAL_ANSWER: 3"),
        ]
    )
    log = run_trial(
        _task(), Condition("B", "use tools", executor=Broken()), client, NumericChecker(), trial=0
    )
    payload = json.loads(log.tool_calls[0].result)
    assert payload["error"] == "TimeoutError"
    assert log.verdict.passed


def test_fake_client_refuses_to_invent_a_response() -> None:
    client = FakeClient([])
    with pytest.raises(RuntimeError, match="script is empty"):
        client.complete([], None)
