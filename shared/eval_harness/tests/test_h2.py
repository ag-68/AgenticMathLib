"""H2: code sandbox, MCP executor, and provider client. No network and no API key."""

import json
import sys
from pathlib import Path

import pytest

from eval_harness import (
    CodeExecutor,
    Condition,
    FakeClient,
    McpExecutor,
    ModelResponse,
    ProviderClient,
    Task,
    ToolCall,
    run_trial,
)

_TOY_SERVER = Path(__file__).with_name("toy_mcp_server.py")


def _task() -> Task:
    return Task(
        id="h2",
        category="numeric",
        prompt="Compute 40 + 2.\nFINAL_ANSWER: <json>",
        inputs={"seed": 0},
        reference=42,
        check="numeric",
        tolerance=0.0,
    )


def test_code_executor_runs_python_and_hides_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "secret-value")
    executor = CodeExecutor(timeout_s=10)
    result = json.loads(
        executor.execute(ToolCall("c1", "run_python", {"code": "import os\nprint(40 + 2)\n"}))
    )
    assert result["exit_code"] == 0
    assert "42" in result["stdout"]
    leaked = json.loads(
        executor.execute(
            ToolCall(
                "c2", "run_python", {"code": "import os\nprint(os.environ.get('OPENAI_API_KEY'))\n"}
            )
        )
    )
    assert "secret-value" not in leaked["stdout"]


def test_code_executor_reports_timeout_and_unknown_tools() -> None:
    executor = CodeExecutor(timeout_s=0.5)
    timeout = json.loads(
        executor.execute(ToolCall("c1", "run_python", {"code": "import time\ntime.sleep(30)\n"}))
    )
    unknown = json.loads(executor.execute(ToolCall("c2", "fft", {})))
    missing = json.loads(executor.execute(ToolCall("c3", "run_python", {})))
    assert timeout["error_code"] == "timeout"
    assert unknown["error_code"] == "unknown_tool"
    assert missing["error_code"] == "missing_code"


def test_loop_uses_the_sandbox_result() -> None:
    executor = CodeExecutor(timeout_s=10)
    client = FakeClient(
        [
            ModelResponse(
                tool_calls=[ToolCall("c1", "run_python", {"code": "print(40 + 2)\n"})],
            ),
            ModelResponse(content="FINAL_ANSWER: 42"),
        ]
    )
    log = run_trial(_task(), Condition("A", "write code", executor=executor), client, trial=0)
    assert log.verdict.passed
    assert "42" in log.tool_calls[0].result


def test_mcp_executor_lists_and_calls_a_tool() -> None:
    with McpExecutor(sys.executable, [str(_TOY_SERVER)]) as executor:
        names = [tool["name"] for tool in executor.list_tools()]
        result = executor.execute(ToolCall("c1", "add", {"a": 2, "b": 3}))
    assert names == ["add"]
    assert result == "5"


def test_provider_reads_the_model_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVAL_MODEL", "configured-model")
    seen: dict[str, object] = {}

    def transport(url: str, api_key: str, payload: dict) -> dict:
        seen["url"] = url
        seen["api_key"] = api_key
        seen["model"] = payload["model"]
        seen["tools"] = payload["tools"]
        return {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "function": {"name": "add", "arguments": '{"a": 1, "b": 2}'},
                            }
                        ],
                    }
                }
            ],
            "usage": {"prompt_tokens": 3, "completion_tokens": 4},
        }

    client = ProviderClient("openai", model_env="EVAL_MODEL", transport=transport)
    response = client.complete(
        [{"role": "user", "content": "add"}],
        [{"name": "add", "description": "Add.", "parameters": {"type": "object"}}],
    )
    assert client.model == "configured-model"
    assert seen["model"] == "configured-model"
    assert seen["api_key"] == ""
    assert seen["url"] == "https://api.openai.com/v1/chat/completions"
    assert response.tool_calls[0].arguments == {"a": 1, "b": 2}
    assert response.input_tokens == 3
    assert response.output_tokens == 4


def test_provider_refuses_a_real_call_without_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = ProviderClient("openai", model="from-config")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        client.complete([], None)


def test_provider_requires_an_explicit_model() -> None:
    with pytest.raises(RuntimeError, match="model must come from"):
        ProviderClient("openai")
