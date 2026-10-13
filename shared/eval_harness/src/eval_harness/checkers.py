"""Check final answers. Each verdict carries a reward from 0 to 1."""

from typing import Any

from eval_harness.models import Task, Verdict, make_verdict


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _missing(final_answer: Any) -> Verdict | None:
    if final_answer is None:
        return make_verdict(False, "format", "missing FINAL_ANSWER")
    return None


def _relative_match(got: float, expected: float, tolerance: float | None) -> tuple[bool, str]:
    """Relative error. A zero reference uses an absolute comparison."""
    if tolerance is None or expected == 0.0:
        limit = 0.0 if tolerance is None else tolerance
        ok = abs(got - expected) <= limit
    else:
        ok = abs(got - expected) / abs(expected) <= tolerance
    if ok:
        return True, "within tolerance"
    return False, f"got {got}, expected {expected}"


def _values_match(got: Any, expected: Any, tolerance: float | None) -> tuple[bool, str, str]:
    """Return passed, error_kind, detail. error_kind is empty when passed."""
    if _is_number(expected):
        if not _is_number(got):
            return False, "format", f"expected a number, got {type(got).__name__}"
        ok, detail = _relative_match(float(got), float(expected), tolerance)
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
        missing = _missing(final_answer)
        if missing is not None:
            return missing
        ok, kind, detail = _values_match(final_answer, task.reference, task.tolerance)
        if ok:
            return make_verdict(True, None, detail)
        return make_verdict(False, kind, detail)


def _exact(got: Any, expected: Any) -> bool:
    if isinstance(got, bool) or isinstance(expected, bool):
        return type(got) is type(expected) and got == expected
    if _is_number(got) and _is_number(expected):
        return float(got) == float(expected)
    if isinstance(got, list) and isinstance(expected, list):
        return len(got) == len(expected) and all(
            _exact(item, target) for item, target in zip(got, expected, strict=True)
        )
    if isinstance(got, dict) and isinstance(expected, dict):
        return got.keys() == expected.keys() and all(
            _exact(got[key], expected[key]) for key in expected
        )
    return type(got) is type(expected) and got == expected


class DiscreteChecker:
    def check(self, task: Task, final_answer: Any) -> Verdict:
        missing = _missing(final_answer)
        if missing is not None:
            return missing
        if _exact(final_answer, task.reference):
            return make_verdict(True, None, "exact match")
        return make_verdict(False, "mismatch", f"got {final_answer!r}, expected {task.reference!r}")


def _inside(got: Any, low: Any, high: Any) -> tuple[bool, str, str]:
    if _is_number(low) and _is_number(high):
        if not _is_number(got):
            return False, "format", f"expected a number, got {type(got).__name__}"
        if float(low) <= float(got) <= float(high):
            return True, "", "inside interval"
        return False, "mismatch", f"got {got}, interval [{low}, {high}]"
    if isinstance(low, list) and isinstance(high, list):
        if not isinstance(got, list) or len(got) != len(low) or len(got) != len(high):
            return False, "format", "interval length mismatch"
        for index, (item, lower, upper) in enumerate(zip(got, low, high, strict=True)):
            ok, kind, detail = _inside(item, lower, upper)
            if not ok:
                return False, kind, f"[{index}] {detail}"
        return True, "", "inside interval"
    return False, "format", "interval bounds must be numbers or lists"


class IntervalChecker:
    def check(self, task: Task, final_answer: Any) -> Verdict:
        missing = _missing(final_answer)
        if missing is not None:
            return missing
        reference = task.reference
        if not isinstance(reference, dict) or set(reference) != {"low", "high"}:
            return make_verdict(False, "format", "interval reference must contain low and high")
        ok, kind, detail = _inside(final_answer, reference["low"], reference["high"])
        if ok:
            return make_verdict(True, None, detail)
        return make_verdict(False, kind, detail)


def get_checker(name: str) -> NumericChecker | DiscreteChecker | IntervalChecker:
    if name == "numeric":
        return NumericChecker()
    if name == "discrete":
        return DiscreteChecker()
    if name == "interval":
        return IntervalChecker()
    raise ValueError(f"unknown checker {name!r}")
