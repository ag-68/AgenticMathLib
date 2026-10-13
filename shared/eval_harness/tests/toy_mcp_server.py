"""A one-tool MCP server used only by the executor test."""

from mcp.server.mcpserver import MCPServer

server = MCPServer("toy")


@server.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


if __name__ == "__main__":
    server.run(transport="stdio")
