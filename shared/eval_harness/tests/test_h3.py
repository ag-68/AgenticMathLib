"""H3: dry-run two conditions, write a results table, and guard the training export."""

import json
from pathlib import Path

import pytest

from eval_harness.cli import main
from eval_harness.export import CONTAMINATION_WARNING, EXCLUDED_EVAL
from eval_harness.fake import FakeClient
from eval_harness.logs import write_logs
from eval_harness.loop import run_trial
from eval_harness.models import Condition, ModelResponse, Task


def _run_dry(tmp_path: Path) -> str:
    code = main(
        [
            "run",
            "--project",
            "toy",
            "--conditions",
            "A,B",
            "--dry-run",
            "--results-dir",
            str(tmp_path),
        ]
    )
    assert code == 0
    analyze = main(["analyze", "--project", "toy", "--results-dir", str(tmp_path)])
    assert analyze == 0
    return (tmp_path / "results.md").read_text(encoding="utf-8")


def test_dry_run_writes_a_table_for_two_conditions(tmp_path: Path) -> None:
    table = _run_dry(tmp_path)
    assert "| A | 0.50 | 0.50 | 0.50 | 0.50 |" in table
    assert "| B | 1.00 | 1.00 | 1.00 | 1.00 |" in table
    assert "| n/a | n/a |" in table
    assert "trap" in table
    logs = (tmp_path / "runs.jsonl").read_text(encoding="utf-8").splitlines()
    rewards = [json.loads(line)["reward"] for line in logs]
    assert set(rewards) == {0.0, 1.0}


def test_export_of_the_toy_run_is_empty(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run_dry(tmp_path)
    out = tmp_path / "export.jsonl"
    code = main(
        [
            "export",
            "--project",
            "toy",
            "--results-dir",
            str(tmp_path),
            "--only-passed",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    assert out.read_text(encoding="utf-8") == ""
    assert EXCLUDED_EVAL in capsys.readouterr().err


def test_export_keeps_train_runs_and_blocks_eval_runs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    task = Task(
        "t", "sums", "Answer.\nFINAL_ANSWER: <json>", {"seed": 1}, 1, "numeric", 0.0, "train"
    )
    eval_task = Task(
        "e", "sums", "Answer.\nFINAL_ANSWER: <json>", {"seed": 1}, 1, "numeric", 0.0, "eval"
    )
    client = FakeClient([ModelResponse(content="FINAL_ANSWER: 1")])
    logs = [
        run_trial(task, Condition("A", "be exact"), client, trial=0),
        run_trial(
            eval_task,
            Condition("A", "be exact"),
            FakeClient([ModelResponse(content="FINAL_ANSWER: 1")]),
            trial=0,
        ),
    ]
    write_logs(tmp_path / "runs.jsonl", logs, fresh=True)
    out = tmp_path / "export.jsonl"
    code = main(
        [
            "export",
            "--project",
            "toy",
            "--results-dir",
            str(tmp_path),
            "--only-passed",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [row["task_id"] for row in rows] == ["t"]
    assert rows[0]["split"] == "train"
    assert rows[0]["reward"] == 1.0
    assert EXCLUDED_EVAL in capsys.readouterr().err


def test_allow_eval_split_warns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run_dry(tmp_path)
    out = tmp_path / "export.jsonl"
    code = main(
        [
            "export",
            "--project",
            "toy",
            "--results-dir",
            str(tmp_path),
            "--only-passed",
            "--allow-eval-split",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    assert CONTAMINATION_WARNING in capsys.readouterr().err
    assert out.read_text(encoding="utf-8").strip() != ""


def test_real_run_asks_before_calling_a_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "n")
    code = main(["run", "--project", "toy", "--conditions", "A", "--results-dir", str(tmp_path)])
    assert code == 1
    assert not (tmp_path / "runs.jsonl").exists()
