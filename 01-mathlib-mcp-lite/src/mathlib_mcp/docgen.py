"""Write the tool pages from the catalog. Run: python -m mathlib_mcp.docgen"""

import json
from pathlib import Path
from typing import Any

from mathlib_mcp.catalog import CATALOG, ToolDoc

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"
HEADINGS = (
    "Purpose",
    "When to use and when not",
    "Parameters",
    "Returns",
    "Conventions",
    "Common mistakes",
    "Minimal example",
    "Related tools",
)


def full_description(doc: ToolDoc) -> str:
    """The condition-C text: conventions, mistakes, and related tools."""
    lines = [
        doc.purpose,
        "",
        f"When to use: {doc.when_to_use}",
        f"When not to use: {doc.when_not}",
        "",
        "Parameters:",
    ]
    for parameter in doc.parameters:
        default = "required" if parameter.default is None else f"default {parameter.default}"
        allowed = f", allowed {parameter.allowed}" if parameter.allowed else ""
        lines.append(
            f"- {parameter.name} ({parameter.type_name}, {default}{allowed}): "
            f"{parameter.description}"
        )
    lines.extend(["", f"Returns: {doc.returns}", "", "Conventions:"])
    lines.extend(f"- {item}" for item in doc.conventions)
    lines.extend(["", "Common mistakes:"])
    lines.extend(f"- {item}" for item in doc.common_mistakes)
    lines.extend(["", "Related tools:"])
    lines.extend(f"- {item}" for item in doc.related)
    return "\n".join(lines)


def bare_description(doc: ToolDoc) -> str:
    """The condition-B text: one sentence, with no recovery hint."""
    return doc.one_sentence


def example_output(doc: ToolDoc) -> dict[str, Any]:
    return doc.function(**doc.example_arguments)


def render_page(doc: ToolDoc) -> str:
    parameter_rows = ["| Name | Type | Default | Allowed | Description |", "|---|---|---|---|---|"]
    for parameter in doc.parameters:
        parameter_rows.append(
            "| "
            + " | ".join(
                [
                    parameter.name,
                    parameter.type_name,
                    parameter.default or "required",
                    parameter.allowed or "",
                    parameter.description,
                ]
            )
            + " |"
        )
    shown_input = json.dumps(doc.example_arguments, indent=2, sort_keys=True)
    shown_output = json.dumps(example_output(doc), indent=2, sort_keys=True)
    conventions = "\n".join(f"- {item}" for item in doc.conventions)
    mistakes = "\n".join(f"- {item}" for item in doc.common_mistakes)
    related = "\n".join(f"- {item}" for item in doc.related)
    table = "\n".join(parameter_rows)
    return (
        f"# {doc.name}\n\n"
        f"## Purpose\n\n{doc.purpose}\n\n"
        f"## When to use and when not\n\n"
        f"Use this when: {doc.when_to_use}\n\n"
        f"Do not use this when: {doc.when_not}\n\n"
        f"## Parameters\n\n{table}\n\n"
        f"## Returns\n\n{doc.returns}\n\n"
        f"## Conventions\n\n{conventions}\n\n"
        f"## Common mistakes\n\n{mistakes}\n\n"
        f"## Minimal example\n\n"
        f"```json\n{shown_input}\n```\n\n"
        f"```json\n{shown_output}\n```\n\n"
        f"## Related tools\n\n{related}\n"
    )


def render_manifest() -> str:
    tools = []
    for doc in CATALOG:
        tools.append(
            {
                "name": doc.name,
                "one_sentence": doc.one_sentence,
                "purpose": doc.purpose,
                "when_to_use": doc.when_to_use,
                "when_not": doc.when_not,
                "parameters": [
                    {
                        "name": parameter.name,
                        "type": parameter.type_name,
                        "description": parameter.description,
                        "default": parameter.default,
                        "allowed": parameter.allowed,
                    }
                    for parameter in doc.parameters
                ],
                "returns": doc.returns,
                "conventions": list(doc.conventions),
                "common_mistakes": list(doc.common_mistakes),
                "example": {
                    "arguments": doc.example_arguments,
                    "output": example_output(doc),
                },
                "related": list(doc.related),
            }
        )
    return json.dumps({"name": "mathlib-mcp-lite", "tools": tools}, indent=2, sort_keys=True) + "\n"


def render_llms_txt() -> str:
    lines = [
        "# mathlib-mcp-lite",
        "",
        "> Five numerical tools. Complex values are objects with re and im. "
        "Arrays are limited to 4096 elements.",
        "",
    ]
    for doc in CATALOG:
        lines.append(f"- [{doc.name}]({doc.name}.md): {doc.one_sentence}")
    return "\n".join(lines) + "\n"


def generated_files() -> dict[str, str]:
    files = {f"docs/{doc.name}.md": render_page(doc) for doc in CATALOG}
    files["docs/api_manifest.json"] = render_manifest()
    files["docs/llms.txt"] = render_llms_txt()
    return files


def write_docs(directory: Path = DOCS_DIR) -> list[Path]:
    written: list[Path] = []
    directory.mkdir(parents=True, exist_ok=True)
    for relative, text in generated_files().items():
        path = directory.parent / relative
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    return written


def main() -> None:
    for path in write_docs():
        print(path)


if __name__ == "__main__":
    main()
