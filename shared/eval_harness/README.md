# eval_harness

Shared test rig that runs tasks through an agent under different conditions, checks the answers, and records comparable metrics. Both projects use it.

## Status

**In progress** (2026-10-13). Milestone H1 matches the current spec: rewards, task splits, and three checkers. H2 and H3 have not started.

## What works

- `Task`, `Condition`, `RunLog`, and `Verdict`. A task is `eval` or `train`. Each verdict has a reward from 0 to 1.
- `FakeClient` replays scripted responses and makes no network call.
- The agent loop sends the system prompt, optional extra context, and task prompt, executes tool calls, and stops on `FINAL_ANSWER:` or after `max_tool_calls` (default 8).
- Checkers: numeric (relative tolerance), discrete (exact match), and interval (a value inside a low/high range).
- Every run log records the messages, tool calls, parsed answer, verdict, reward, error kind, split, token counts, and wall time.

## What does not work yet

`McpExecutor`, `CodeExecutor`, and `ProviderClient` are not implemented. The CLI, analysis tables, dry-run command, and `eval export` leakage guard are not implemented.

## Results (real runs only)

not run
