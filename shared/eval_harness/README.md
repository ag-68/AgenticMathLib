# eval_harness

Shared test rig that runs tasks through an agent under different conditions, checks the answers, and records comparable metrics. Both projects use it.

## Status

**In progress** (2026-10-14). Milestones H1 and H2 are implemented and covered by unit tests. H3 has not started.

## What works

- `Task`, `Condition`, `RunLog`, and `Verdict`. A task is `eval` or `train`. Each verdict has a reward from 0 to 1.
- `FakeClient` replays scripted responses and makes no network call.
- The agent loop sends the system prompt, optional extra context, and task prompt, executes tool calls, and stops on `FINAL_ANSWER:` or after `max_tool_calls` (default 8).
- Checkers: numeric (relative tolerance), discrete (exact match), and interval (a value inside a low/high range).
- Every run log records the messages, tool calls, parsed answer, verdict, reward, error kind, split, token counts, and wall time.
- `CodeExecutor` runs model-written Python in a subprocess with a timeout and a temporary directory. On Unix it also sets a memory limit. API keys are not copied into that process.
- `McpExecutor` starts an MCP server over stdio, lists its tools, and forwards calls.
- `ProviderClient` calls an OpenAI-compatible chat endpoint. The model name comes from config or `EVAL_MODEL`. Unit tests inject a fake transport and do not open a network connection.

The sandbox stops a program that runs too long. It does not contain hostile code. Only model output from a trusted run should be executed. Network access is not blocked. The memory limit is not applied on Windows.

## What does not work yet

The CLI, analysis tables, dry-run command, and `eval export` leakage guard are not implemented. Providers that do not speak the OpenAI chat-completions format are not implemented.

## Results (real runs only)

not run
