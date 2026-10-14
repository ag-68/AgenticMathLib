# eval_harness

Shared test rig that runs tasks through an agent under different conditions, checks the answers, and records comparable metrics. Both projects use it.

## Status

**In progress** (2026-10-14). Milestones H1, H2, and H3 are implemented. No real model run has been done.

## What works

- `Task`, `Condition`, `RunLog`, and `Verdict`. A task is `eval` or `train`. Each verdict has a reward from 0 to 1.
- `FakeClient` replays scripted responses and makes no network call.
- The agent loop sends the system prompt, optional extra context, and task prompt, executes tool calls, and stops on `FINAL_ANSWER:` or after `max_tool_calls` (default 8).
- Checkers: numeric (relative tolerance), discrete (exact match), and interval (a value inside a low/high range).
- Every run log records the messages, tool calls, parsed answer, verdict, reward, error kind, split, token counts, and wall time.
- `CodeExecutor` runs model-written Python in a subprocess with a timeout and a temporary directory. On Unix it also sets a memory limit. API keys are not copied into that process.
- `McpExecutor` starts an MCP server over stdio, lists its tools, and forwards calls.
- `ProviderClient` calls an OpenAI-compatible chat endpoint. The model name comes from config or `EVAL_MODEL`. Unit tests inject a fake transport and do not open a network connection.
- `eval run --dry-run` replays a toy task set for two conditions and writes `runs.jsonl`. `eval analyze` builds `results.md` from those logs. `eval export` writes passing `train`-split runs and leaves `eval`-split runs out unless `--allow-eval-split` is set.

The sandbox stops a program that runs too long. It does not contain hostile code. Only model output from a trusted run should be executed. Network access is not blocked. The memory limit is not applied on Windows.

## What does not work yet

Providers that do not speak the OpenAI chat-completions format are not implemented. `model_tier` is accepted in the config and does not launch a second model. The toy dry-run is a software check, not a measured result.

## Results (real runs only)

not run
