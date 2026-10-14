"""Build results.md from run logs. Numbers are computed, never typed in."""

import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

from eval_harness.models import RunLog

_ASSUMED_TOKENS_NOTE = (
    "Token counts below are whatever the client recorded. "
    "A pre-run estimate of 500 tokens per trial is only a budget guess."
)


def render_results(logs: list[RunLog]) -> str:
    lines = [
        "# Results",
        "",
        f"Generated from {len(logs)} run logs. {_ASSUMED_TOKENS_NOTE}",
        "",
        "## By condition",
        "",
        "| Condition | pass@1 | min | max | consistency | mean reward "
        "| tool calls | argument validity | tokens | wall time s |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    conditions = _ordered(log.condition for log in logs)
    for condition in conditions:
        group = [log for log in logs if log.condition == condition]
        rates = _trial_rates(group)
        lines.append(
            "| "
            + " | ".join(
                [
                    condition,
                    _fmt(_rate(group)),
                    _fmt(min(rates) if rates else "n/a"),
                    _fmt(max(rates) if rates else "n/a"),
                    _fmt(_consistency(group)),
                    _fmt(_mean(log.reward for log in group)),
                    _tool_calls(group),
                    _argument_validity(group),
                    _fmt(_mean(log.input_tokens + log.output_tokens for log in group)),
                    _fmt(_mean(log.wall_time_s for log in group)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## By category",
            "",
            "| Condition | Category | passed | trials |",
            "|---|---|---|---|",
        ]
    )
    for condition in conditions:
        categories = _ordered(log.category for log in logs if log.condition == condition)
        for category in categories:
            group = [log for log in logs if log.condition == condition and log.category == category]
            passed = sum(1 for log in group if log.verdict.passed)
            lines.append(f"| {condition} | {category} | {passed} | {len(group)} |")
    lines.extend(
        [
            "",
            "## Error kinds",
            "",
            "| Condition | error kind | count |",
            "|---|---|---|",
        ]
    )
    for condition in conditions:
        counts: dict[str, int] = defaultdict(int)
        for log in logs:
            if log.condition == condition and log.error_kind:
                counts[log.error_kind] += 1
        if not counts:
            lines.append(f"| {condition} | none | n/a |")
            continue
        for kind, count in sorted(counts.items()):
            lines.append(f"| {condition} | {kind} | {count} |")
    lines.extend(
        ["", "## Failed runs", "", "| task | condition | trial | error kind |", "|---|---|---|---|"]
    )
    failures = [log for log in logs if not log.verdict.passed]
    if not failures:
        lines.append("| n/a | n/a | n/a | n/a |")
    for log in failures:
        lines.append(f"| {log.task_id} | {log.condition} | {log.trial} | {log.error_kind} |")
    lines.append("")
    return "\n".join(lines)


def write_results(logs: list[RunLog], path: Path) -> str:
    text = render_results(logs)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text


def _tool_calls(logs: list[RunLog]) -> str:
    if not logs or not any(log.tools_available for log in logs):
        return "n/a"
    return _fmt(_mean(len(log.tool_calls) for log in logs))


def _argument_validity(logs: list[RunLog]) -> str:
    calls = [record for log in logs if log.tools_available for record in log.tool_calls]
    if not calls:
        return "n/a"
    valid = sum(1 for record in calls if not _is_invalid(record.result))
    return _fmt(valid / len(calls))


def _is_invalid(result: str) -> bool:
    try:
        payload = json.loads(result)
    except json.JSONDecodeError:
        return False
    return isinstance(payload, dict) and "error_code" in payload


def _trial_rates(logs: list[RunLog]) -> list[float]:
    by_trial: dict[int, list[RunLog]] = defaultdict(list)
    for log in logs:
        by_trial[log.trial].append(log)
    return [_rate(group) for _, group in sorted(by_trial.items())]


def _consistency(logs: list[RunLog]) -> float:
    by_task: dict[str, list[bool]] = defaultdict(list)
    for log in logs:
        by_task[log.task_id].append(log.verdict.passed)
    if not by_task:
        return 0.0
    return sum(1 for flags in by_task.values() if all(flags)) / len(by_task)


def _rate(logs: list[RunLog]) -> float:
    if not logs:
        return 0.0
    return sum(1 for log in logs if log.verdict.passed) / len(logs)


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(items) / len(items)


def _fmt(value: float | str) -> str:
    if isinstance(value, str):
        return value
    return f"{value:.2f}"


def _ordered(items: Iterable[str]) -> list[str]:
    seen: list[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen
