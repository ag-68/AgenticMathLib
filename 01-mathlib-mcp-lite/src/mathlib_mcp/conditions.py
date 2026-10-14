"""Condition B: the five tools with short descriptions and a generic error.

The numerical functions are the same as the full server. The caller closes the executor.
"""

import sys

from eval_harness import Condition, McpExecutor

BARE_PROMPT = (
    "You have five math tools. Each description is one sentence. "
    "A failed call says only that the arguments were not accepted."
)


def open_server(*, bare: bool) -> McpExecutor:
    args = ["-m", "mathlib_mcp.server"]
    if bare:
        args.append("--bare")
    return McpExecutor(sys.executable, args)


def condition_b() -> Condition:
    return Condition("B", BARE_PROMPT, executor=open_server(bare=True))
