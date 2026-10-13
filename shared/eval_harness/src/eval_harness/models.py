"""Dataclasses and protocols shared by every project."""

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass
class Task:
    id: str
    category: str
    prompt: str
    inputs: dict[str, Any]
    reference: Any
    check: str
    tolerance: float | None = None
    split: str = "eval"

    def __post_init__(self) -> None:
        if self.split not in {"eval", "train"}:
            raise ValueError(f"split must be 'eval' or 'train', got {self.split!r}")


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ModelResponse:
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class Verdict:
    passed: bool
    error_kind: str | None
    detail: str
    reward: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.reward <= 1.0:
            raise ValueError("reward must be between 0 and 1")


def make_verdict(
    passed: bool,
    error_kind: str | None,
    detail: str,
    reward: float | None = None,
) -> Verdict:
    """Build a verdict. Reward defaults to 1 on pass and 0 on fail."""
    if reward is None:
        reward = 1.0 if passed else 0.0
    return Verdict(passed=passed, error_kind=error_kind, detail=detail, reward=reward)


@dataclass
class ToolRecord:
    id: str
    name: str
    arguments: dict[str, Any]
    result: str


@dataclass
class RunLog:
    task_id: str
    prompt: str
    condition: str
    trial: int
    messages: list[dict[str, Any]]
    tool_calls: list[ToolRecord]
    final_answer: Any
    verdict: Verdict
    reward: float
    error_kind: str | None
    split: str
    input_tokens: int
    output_tokens: int
    wall_time_s: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "condition": self.condition,
            "trial": self.trial,
            "messages": self.messages,
            "tool_calls": [asdict(record) for record in self.tool_calls],
            "final_answer": self.final_answer,
            "verdict": asdict(self.verdict),
            "reward": self.reward,
            "error_kind": self.error_kind,
            "split": self.split,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "wall_time_s": self.wall_time_s,
        }


class Executor(Protocol):
    def list_tools(self) -> list[dict[str, Any]]:
        """Return the tool schemas the model is allowed to call."""

    def execute(self, call: ToolCall) -> str:
        """Run one tool call and return its result as text."""


class ModelClient(Protocol):
    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
    ) -> ModelResponse:
        """Return the next model message, including any tool calls."""


class Checker(Protocol):
    def check(self, task: Task, final_answer: Any) -> Verdict:
        """Judge a parsed final answer. `final_answer` is None when parsing failed."""


@dataclass
class Condition:
    name: str
    system_prompt: str
    executor: Executor | None = None
    extra_context: str | None = None
