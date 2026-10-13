"""H1: fake client, agent loop, run log, and checkers. No network."""

import json

import pytest

from eval_harness import (
    Condition,
    DiscreteChecker,
    FakeClient,
    IntervalChecker,
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
        "check": "numeric",
        "tolerance": 1e-6,
        "split": "eval",
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


def test_numeric_checker_uses_relative_tolerance_and_reward() -> None:
    close = NumericChecker().check(_task(reference=100.0, tolerance=0.02), 101.0)
    far = NumericChecker().check(_task(reference=100.0, tolerance=0.02), 103.0)
    zero = NumericChecker().check(_task(reference=0.0, tolerance=0.1), 0.05)
    assert close.passed and close.reward == 1.0
    assert far.passed is False and far.reward == 0.0
    assert far.error_kind == "mismatch"
    assert zero.passed


def test_numeric_checker_reports_shape_errors() -> None:
    shape = NumericChecker().check(_task(reference=[1, 2]), [1])
    missing = NumericChecker().check(_task(), None)
    assert shape.error_kind == "format"
    assert missing.error_kind == "format"
    assert missing.reward == 0.0


def test_discrete_checker_matches_values_and_rejects_bool_as_int() -> None:
    checker = DiscreteChecker()
    assert checker.check(_task(reference="ls", check="discrete"), "ls").passed
    assert checker.check(_task(reference=1, check="discrete"), 1.0).passed
    boolean = checker.check(_task(reference=1, check="discrete"), True)
    assert boolean.passed is False
    assert boolean.error_kind == "mismatch"


def test_interval_checker_accepts_a_value_inside_the_range() -> None:
    task = _task(reference={"low": 0.01, "high": 0.03}, check="interval")
    inside = IntervalChecker().check(task, 0.02)
    outside = IntervalChecker().check(task, 0.05)
    assert inside.passed and inside.reward == 1.0
    assert outside.error_kind == "mismatch" and outside.reward == 0.0


def test_task_rejects_an_unknown_split() -> None:
    with pytest.raises(ValueError, match="split"):
        _task(split="holdout")


def test_loop_records_a_direct_answer_from_the_fake_client() -> None:
    client = FakeClient([ModelResponse(content="FINAL_ANSWER: 3", input_tokens=5, output_tokens=2)])
    log = run_trial(_task(), Condition("A", "be exact"), client, trial=0)

    assert log.verdict.passed
    assert log.reward == 1.0
    assert log.error_kind is None
    assert log.split == "eval"
    assert log.final_answer == 3
    assert log.condition == "A"
    assert log.trial == 0
    assert log.input_tokens == 5
    assert log.output_tokens == 2
    assert log.tool_calls == []
    assert [message["role"] for message in log.messages] == ["system", "user", "assistant"]
    payload = json.loads(json.dumps(log.to_dict()))
    assert payload["verdict"]["passed"] is True
    assert payload["reward"] == 1.0
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
    log = run_trial(_task(split="train"), condition, client, trial=2)

    assert log.verdict.passed
    assert log.split == "train"
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
        trial=1,
        max_tool_calls=1,
    )
    assert log.verdict.passed is False
    assert log.verdict.error_kind == "format"
    assert log.reward == 0.0
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
    log = run_trial(_task(), Condition("B", "use tools", executor=Broken()), client, trial=0)
    payload = json.loads(log.tool_calls[0].result)
    assert payload["error"] == "TimeoutError"
    assert log.verdict.passed


def test_fake_client_refuses_to_invent_a_response() -> None:
    client = FakeClient([])
    with pytest.raises(RuntimeError, match="script is empty"):
        client.complete([], None)
