"""Export passing runs for a later training step, without mixing in the measurement set."""

import json
from pathlib import Path

from eval_harness.models import RunLog

EXCLUDED_EVAL = "excluded eval-split runs from export"
CONTAMINATION_WARNING = "WARNING: exporting eval-split runs contaminates the measurement set."


def export_runs(
    logs: list[RunLog],
    path: Path,
    *,
    only_passed: bool,
    allow_eval_split: bool,
) -> str:
    chosen = [log for log in logs if log.verdict.passed] if only_passed else list(logs)
    eval_logs = [log for log in chosen if log.split == "eval"]
    if eval_logs and not allow_eval_split:
        chosen = [log for log in chosen if log.split == "train"]
        notice = f"{EXCLUDED_EVAL}: {len(eval_logs)}"
    elif eval_logs and allow_eval_split:
        notice = CONTAMINATION_WARNING
    else:
        notice = ""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for log in chosen:
            handle.write(json.dumps(_chat_record(log)) + "\n")
    return notice


def _chat_record(log: RunLog) -> dict[str, object]:
    return {
        "task_id": log.task_id,
        "split": log.split,
        "reward": log.reward,
        "messages": log.messages,
        "tool_calls": [
            {"id": call.id, "name": call.name, "arguments": call.arguments, "result": call.result}
            for call in log.tool_calls
        ],
    }
