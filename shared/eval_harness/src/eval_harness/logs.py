"""JSON Lines logs: one run per line."""

import json
from pathlib import Path

from eval_harness.models import RunLog


def write_logs(path: Path, logs: list[RunLog], *, fresh: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if fresh or not path.exists() else "a"
    with path.open(mode, encoding="utf-8") as handle:
        for log in logs:
            handle.write(json.dumps(log.to_dict()) + "\n")


def read_logs(path: Path) -> list[RunLog]:
    if not path.exists():
        return []
    logs: list[RunLog] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            logs.append(RunLog.from_dict(json.loads(line)))
    return logs
