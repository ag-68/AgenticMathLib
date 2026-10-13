"""Shared evaluation harness: run tasks, check answers, and log the full conversation."""

from eval_harness.answers import ParsedAnswer, parse_final_answer
from eval_harness.checkers import DiscreteChecker, IntervalChecker, NumericChecker, get_checker
from eval_harness.executors import CodeExecutor, McpExecutor
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
    make_verdict,
)
from eval_harness.provider import ProviderClient

__all__ = [
    "Checker",
    "CodeExecutor",
    "Condition",
    "DiscreteChecker",
    "Executor",
    "FakeClient",
    "IntervalChecker",
    "McpExecutor",
    "ModelClient",
    "ModelResponse",
    "NumericChecker",
    "ParsedAnswer",
    "ProviderClient",
    "RunLog",
    "Task",
    "ToolCall",
    "ToolRecord",
    "Verdict",
    "get_checker",
    "make_verdict",
    "parse_final_answer",
    "run_trial",
]
