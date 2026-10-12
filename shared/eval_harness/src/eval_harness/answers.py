"""Extract the single FINAL_ANSWER line. The checker uses only that JSON."""

import json
import re
from dataclasses import dataclass
from typing import Any

_FINAL_ANSWER = re.compile(r"(?m)^[ \t]*FINAL_ANSWER:[ \t]*(.*)$")


@dataclass(frozen=True)
class ParsedAnswer:
    ok: bool
    value: Any = None
    detail: str = ""


def parse_final_answer(text: str | None) -> ParsedAnswer:
    if not text or not text.strip():
        return ParsedAnswer(False, detail="missing FINAL_ANSWER")
    matches = _FINAL_ANSWER.findall(text)
    if not matches:
        return ParsedAnswer(False, detail="missing FINAL_ANSWER")
    raw = matches[-1].strip()
    try:
        return ParsedAnswer(True, value=json.loads(raw))
    except json.JSONDecodeError as exc:
        return ParsedAnswer(False, detail=f"FINAL_ANSWER is not valid JSON: {exc.msg}")
