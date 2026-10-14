"""MCP server for the five math tools.

The full server is condition C. `python -m mathlib_mcp.server --bare` is condition B:
the same functions, one-sentence descriptions, and a generic error.
"""

import argparse
import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from mathlib_mcp.catalog import CATALOG
from mathlib_mcp.docgen import bare_description, full_description
from mathlib_mcp.errors import ToolError
from mathlib_mcp.tools import TOOLS

GENERIC_ERROR = {
    "error_code": "invalid_arguments",
    "message": "The arguments were not accepted.",
    "fix_hint": "Check the arguments.",
}


def call_tool(name: str, arguments: dict[str, Any], *, bare: bool) -> str:
    try:
        return json.dumps(TOOLS[name](**arguments))
    except ToolError as exc:
        if bare:
            return json.dumps(GENERIC_ERROR)
        return json.dumps(exc.to_dict())


def build_server(bare: bool) -> MCPServer:
    app = MCPServer("mathlib-mcp-lite")
    description = bare_description if bare else full_description

    @app.tool(description=description(CATALOG[0]))
    def fft(x: list | dict, direction: str = "forward", norm: str = "backward") -> str:
        return call_tool("fft", {"x": x, "direction": direction, "norm": norm}, bare=bare)

    @app.tool(description=description(CATALOG[1]))
    def power_spectrum(samples: list, sample_rate_hz: float) -> str:
        return call_tool(
            "power_spectrum",
            {"samples": samples, "sample_rate_hz": sample_rate_hz},
            bare=bare,
        )

    @app.tool(description=description(CATALOG[2]))
    def convolve(a: list | dict, b: list | dict, mode: str = "full") -> str:
        return call_tool("convolve", {"a": a, "b": b, "mode": mode}, bare=bare)

    @app.tool(description=description(CATALOG[3]))
    def solve_linear_system(a: list | dict, b: list | dict) -> str:
        return call_tool("solve_linear_system", {"a": a, "b": b}, bare=bare)

    @app.tool(description=description(CATALOG[4]))
    def least_squares(a: list | dict, b: list | dict) -> str:
        return call_tool("least_squares", {"a": a, "b": b}, bare=bare)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the five math tools over MCP.")
    parser.add_argument(
        "--bare",
        action="store_true",
        help="Condition B: one-sentence descriptions and a generic error.",
    )
    args = parser.parse_args()
    build_server(bare=args.bare).run(transport="stdio")


if __name__ == "__main__":
    main()
