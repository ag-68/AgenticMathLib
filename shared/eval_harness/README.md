# eval_harness

Shared test rig that runs tasks through an agent under different conditions, checks the answers, and records comparable metrics. All four projects use it.

## Status

**In progress** (2026-10-12). Milestone H1 is implemented and covered by unit tests. H2 and H3 have not started.

## What works

- `Task`, `Condition`, `RunLog`, and `Verdict`.
- `FakeClient` replays scripted responses and makes no network call.
- The agent loop sends the system prompt, optional extra context, and task prompt, executes tool calls, and stops on `FINAL_ANSWER:` or after `max_tool_calls` (default 8).
- `NumericChecker` compares scalars and nested lists within a tolerance.
- Every run log records the messages, tool calls, parsed answer, verdict, token counts, and wall time.

## What does not work yet

`McpExecutor`, `CodeExecutor`, and `ProviderClient` are not implemented. The CLI, analysis tables, and dry-run command are not implemented.

## Results (real runs only)

not run
