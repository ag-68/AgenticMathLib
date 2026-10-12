"""Shared evaluation harness: run tasks, check answers, and log the full conversation."""

from eval_harness.answers import ParsedAnswer, parse_final_answer
from eval_harness.checkers import NumericChecker
from eval_harness.fake import FakeClient
from eval_harness.loop import run_trial
from eval_harness.models import (
    Checker,
    Condition,
    Executor,
    ModelClient,
    ModelResponse,
    RunLog,
    Task,
    ToolCall,
    ToolRecord,
    Verdict,
)

__all__ = [
    "Checker",
    "Condition",
    "Executor",
    "FakeClient",
    "ModelClient",
    "ModelResponse",
    "NumericChecker",
    "ParsedAnswer",
    "RunLog",
    "Task",
    "ToolCall",
    "ToolRecord",
    "Verdict",
    "parse_final_answer",
    "run_trial",
]
