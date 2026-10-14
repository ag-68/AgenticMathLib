"""M2: generated pages match the code, and condition B hides the recovery hints."""

import json
import re

from eval_harness import ToolCall
from mathlib_mcp.catalog import CATALOG, by_name
from mathlib_mcp.conditions import condition_b
from mathlib_mcp.docgen import DOCS_DIR, HEADINGS, example_output, generated_files
from mathlib_mcp.server import call_tool

_EXAMPLE = re.compile(r"```json\n(.*?)\n```\n\n```json\n(.*?)\n```", re.S)


def test_generated_files_match_what_docgen_writes() -> None:
    for relative, text in generated_files().items():
        path = DOCS_DIR.parent / relative
        assert path.read_text(encoding="utf-8") == text


def test_documented_examples_match_the_tools() -> None:
    for doc in CATALOG:
        page = (DOCS_DIR / f"{doc.name}.md").read_text(encoding="utf-8")
        for heading in HEADINGS:
            assert f"## {heading}" in page
        match = _EXAMPLE.search(page)
        assert match is not None
        arguments = json.loads(match.group(1))
        shown = json.loads(match.group(2))
        assert arguments == doc.example_arguments
        assert shown == example_output(doc)
        assert shown == doc.function(**arguments)


def test_bare_call_hides_the_fix_the_full_call_names() -> None:
    arguments = {"a": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], "b": [1.0, 2.0]}
    bare = json.loads(call_tool("solve_linear_system", arguments, bare=True))
    full = json.loads(call_tool("solve_linear_system", arguments, bare=False))
    assert bare == {
        "error_code": "invalid_arguments",
        "message": "The arguments were not accepted.",
        "fix_hint": "Check the arguments.",
    }
    assert "least_squares" not in json.dumps(bare)
    assert full["error_code"] == "not_square"
    assert "least_squares" in full["fix_hint"]
    same = {"x": [1.0, 0.0, 0.0, 0.0]}
    assert call_tool("fft", same, bare=True) == call_tool("fft", same, bare=False)


def test_condition_b_server_lists_one_sentence_and_a_generic_error() -> None:
    condition = condition_b()
    try:
        executor = condition.executor
        assert executor is not None
        described = {tool["name"]: tool["description"] for tool in executor.list_tools()}
        assert described["solve_linear_system"] == by_name("solve_linear_system").one_sentence
        assert "least_squares" not in described["solve_linear_system"]
        failed = json.loads(
            executor.execute(
                ToolCall(
                    "c1",
                    "solve_linear_system",
                    {"a": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], "b": [1.0, 2.0]},
                )
            )
        )
        assert failed["error_code"] == "invalid_arguments"
        assert "least_squares" not in json.dumps(failed)
    finally:
        assert condition.executor is not None
        condition.executor.close()
