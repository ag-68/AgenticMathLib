"""MCP server for the five math tools. Run with: python -m mathlib_mcp.server"""

import json

from mcp.server.mcpserver import MCPServer

from mathlib_mcp.errors import ToolError
from mathlib_mcp.tools import TOOLS

server = MCPServer("mathlib-mcp-lite")


def _call(name: str, **kwargs: object) -> str:
    try:
        return json.dumps(TOOLS[name](**kwargs))
    except ToolError as exc:
        return json.dumps(exc.to_dict())


@server.tool(description=TOOLS["fft"].__doc__)
def fft(x: list | dict, direction: str = "forward", norm: str = "backward") -> str:
    return _call("fft", x=x, direction=direction, norm=norm)


@server.tool(description=TOOLS["power_spectrum"].__doc__)
def power_spectrum(samples: list, sample_rate_hz: float) -> str:
    return _call("power_spectrum", samples=samples, sample_rate_hz=sample_rate_hz)


@server.tool(description=TOOLS["convolve"].__doc__)
def convolve(a: list | dict, b: list | dict, mode: str = "full") -> str:
    return _call("convolve", a=a, b=b, mode=mode)


@server.tool(description=TOOLS["solve_linear_system"].__doc__)
def solve_linear_system(a: list | dict, b: list | dict) -> str:
    return _call("solve_linear_system", a=a, b=b)


@server.tool(description=TOOLS["least_squares"].__doc__)
def least_squares(a: list | dict, b: list | dict) -> str:
    return _call("least_squares", a=a, b=b)


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
