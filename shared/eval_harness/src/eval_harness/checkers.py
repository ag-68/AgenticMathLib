"""Check numeric answers against a task reference."""

from typing import Any

from eval_harness.models import Task, Verdict


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _numbers_match(got: float, expected: float, tolerance: float | None) -> tuple[bool, str]:
    if tolerance is None:
        ok = got == expected
    else:
        ok = abs(got - expected) <= tolerance
    if ok:
        return True, "within tolerance"
    return False, f"got {got}, expected {expected}"


def _values_match(got: Any, expected: Any, tolerance: float | None) -> tuple[bool, str, str]:
    """Return passed, error_kind, detail. error_kind is empty when passed."""
    if _is_number(expected):
        if not _is_number(got):
            return False, "format", f"expected a number, got {type(got).__name__}"
        ok, detail = _numbers_match(float(got), float(expected), tolerance)
        return ok, "" if ok else "mismatch", detail
    if isinstance(expected, list):
        if not isinstance(got, list):
            return False, "format", f"expected a list, got {type(got).__name__}"
        if len(got) != len(expected):
            return False, "format", f"length {len(got)} != {len(expected)}"
        for index, (item, target) in enumerate(zip(got, expected, strict=True)):
            ok, kind, detail = _values_match(item, target, tolerance)
            if not ok:
                return False, kind, f"[{index}] {detail}"
        return True, "", "within tolerance"
    return False, "format", f"unsupported reference type {type(expected).__name__}"


class NumericChecker:
    def check(self, task: Task, final_answer: Any) -> Verdict:
        if final_answer is None:
            return Verdict(False, "format", "missing FINAL_ANSWER")
        if task.answer_format == "number" and not _is_number(task.reference):
            return Verdict(False, "format", "task reference is not a number")
        if task.answer_format == "vector" and not isinstance(task.reference, list):
            return Verdict(False, "format", "task reference is not a list")
        if task.answer_format not in {"number", "vector"}:
            return Verdict(False, "format", f"unsupported answer_format {task.answer_format}")
        ok, kind, detail = _values_match(final_answer, task.reference, task.tolerance)
        if ok:
            return Verdict(True, None, detail)
        return Verdict(False, kind, detail)
