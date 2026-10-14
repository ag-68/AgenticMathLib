"""A two-condition task set used to dry-run the CLI. It is not a research result."""

from pathlib import Path
from typing import Any

from eval_harness.config import EvalConfig
from eval_harness.fake import FakeClient
from eval_harness.models import Condition, ModelResponse, Task, ToolCall

CONFIG_PATH = Path("shared/eval_harness/eval/eval_config.yaml")
RESULTS_DIR = Path("shared/eval_harness/eval/results")

# Budget guess printed before a paid run. It is not a measured token count.
ASSUMED_TOKENS_PER_TRIAL = 500


class _Add:
    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "add", "description": "Add two numbers.", "parameters": {"type": "object"}}
        ]

    def execute(self, call: ToolCall) -> str:
        return "3"


def toy_tasks() -> list[Task]:
    common = {"category": "sums", "tolerance": 0.0, "check": "numeric", "split": "eval"}
    return [
        Task(
            id="easy",
            prompt="Add 1 and 2.\nFINAL_ANSWER: <json>",
            inputs={"seed": 0},
            reference=3,
            **common,
        ),
        Task(
            id="trap",
            prompt="Add 1 and 2, but the obvious shortcut is wrong.\nFINAL_ANSWER: <json>",
            inputs={"seed": 0},
            reference=3,
            **common,
        ),
    ]


def toy_conditions() -> dict[str, Condition]:
    return {
        "A": Condition("A", "Answer with no tools."),
        "B": Condition("B", "Use the add tool.", executor=_Add()),
    }


def toy_client(task: Task, condition: Condition, trial: int) -> FakeClient:
    del trial
    if condition.name == "A":
        answer = task.reference if task.id == "easy" else 0
        return FakeClient(
            [ModelResponse(content=f"FINAL_ANSWER: {answer}", input_tokens=10, output_tokens=4)]
        )
    return FakeClient(
        [
            ModelResponse(
                tool_calls=[ToolCall("c1", "add", {"a": 1, "b": 2})],
                input_tokens=8,
                output_tokens=3,
            ),
            ModelResponse(
                content=f"FINAL_ANSWER: {task.reference}", input_tokens=6, output_tokens=2
            ),
        ]
    )


def estimate_tokens(n_runs: int) -> str:
    total = n_runs * ASSUMED_TOKENS_PER_TRIAL
    return (
        f"Assumed budget, not a measurement: {ASSUMED_TOKENS_PER_TRIAL} tokens "
        f"per trial, {n_runs} trials, about {total} tokens."
    )


def make_provider(config: EvalConfig) -> Any:
    from eval_harness.provider import ProviderClient

    if config.model:
        return ProviderClient(config.provider, model=config.model)
    return ProviderClient(config.provider, model_env=config.model_env or "EVAL_MODEL")
