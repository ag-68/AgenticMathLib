"""The two ways a model is allowed to act: call an MCP server, or run Python."""

import asyncio
import json
import threading
from typing import Any

from eval_harness.models import ToolCall
from eval_harness.sandbox import run_python

_RUN_PYTHON = {
    "name": "run_python",
    "description": "Run a Python program and return stdout, stderr, and the exit code.",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "A complete Python program."},
        },
        "required": ["code"],
    },
}


class CodeExecutor:
    def __init__(self, timeout_s: float = 20.0, memory_mb: int = 512) -> None:
        self.timeout_s = timeout_s
        self.memory_mb = memory_mb

    def list_tools(self) -> list[dict[str, Any]]:
        return [_RUN_PYTHON]

    def execute(self, call: ToolCall) -> str:
        if call.name != "run_python":
            return json.dumps(
                {
                    "error_code": "unknown_tool",
                    "message": f"Unknown tool {call.name}.",
                    "fix_hint": "Call run_python with a code string.",
                }
            )
        code = call.arguments.get("code")
        if not isinstance(code, str):
            return json.dumps(
                {
                    "error_code": "missing_code",
                    "message": "run_python requires a string argument named code.",
                    "fix_hint": "Pass the program text in the code field.",
                }
            )
        return run_python(code, timeout_s=self.timeout_s, memory_mb=self.memory_mb)


class McpExecutor:
    """One MCP server over stdio, kept open so each tool call reuses the session."""

    def __init__(self, command: str, args: list[str] | None = None) -> None:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        self._stdio_client = stdio_client
        self._client_session = ClientSession
        self._params = StdioServerParameters(command=command, args=args or [])
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._error: BaseException | None = None
        self._session: Any = None
        self._stopped: asyncio.Event | None = None
        self._closed = False
        self._thread = threading.Thread(target=self._thread_main, name="mcp-executor", daemon=True)
        self._thread.start()
        if not self._ready.wait(30):
            detail = self._error or "timed out"
            raise TimeoutError(f"MCP server did not become ready: {detail}")
        if self._error is not None:
            raise RuntimeError(f"MCP server failed to start: {self._error}")

    def _thread_main(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._session_main())
        except Exception as exc:
            self._error = exc
            self._ready.set()
        finally:
            self._loop.close()

    async def _session_main(self) -> None:
        async with self._stdio_client(self._params) as (read, write):
            async with self._client_session(read, write) as session:
                await session.initialize()
                self._session = session
                self._stopped = asyncio.Event()
                self._ready.set()
                await self._stopped.wait()

    def _call(self, coroutine: Any, timeout: float = 20.0) -> Any:
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        return future.result(timeout=timeout)

    def list_tools(self) -> list[dict[str, Any]]:
        listed = self._call(self._session.list_tools())
        tools: list[dict[str, Any]] = []
        for tool in listed.tools:
            schema = tool.input_schema
            if hasattr(schema, "model_dump"):
                schema = schema.model_dump()
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": schema,
                }
            )
        return tools

    def execute(self, call: ToolCall) -> str:
        result = self._call(self._session.call_tool(call.name, call.arguments))
        texts = [block.text for block in result.content if getattr(block, "text", None)]
        body = "\n".join(texts)
        if result.is_error:
            return json.dumps(
                {
                    "error_code": "tool_error",
                    "message": body,
                    "fix_hint": "Read the message and correct the arguments.",
                }
            )
        return body

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._stopped is not None and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._stopped.set)
        self._thread.join(timeout=10)

    def __enter__(self) -> "McpExecutor":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
