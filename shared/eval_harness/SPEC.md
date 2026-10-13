# Shared evaluation harness

This file is the project section of the monorepo specification. The full document is [docs/SPEC.md](../../docs/SPEC.md).

## Part 2: Shared evaluation harness (`shared/eval_harness`), about 1-1.25 days

### 2.1 Purpose

A small, provider-independent rig that runs tasks through an agent under different conditions, checks answers and produces comparable metrics for both projects.

### 2.2 Design goals

- Fair: conditions differ only in what is being tested.
- Cheap to test: a fake model makes the whole pipeline testable offline.
- Auditable: every run is fully logged.
- Minimal: no features beyond what the two projects need.

### 2.3 Components

- **`Task`:** `id`, `category`, `prompt`, `inputs`, `reference`, `check` (which checker to use), `tolerance`, `split` (`eval` by default; `train` is reserved for the optional Phase 2).
- **`Condition`:** `name`, `system_prompt`, `executor`, `extra_context`.
- **Executors:** `McpExecutor` (starts an MCP server over stdio, lists its tools, forwards calls) and `CodeExecutor` (runs model-written Python in the sandbox).
- **`ModelClient`:** interface with a `ProviderClient` (real API; provider and model from config) and a `FakeClient` (scripted, for tests and dry runs).
- **Checkers:** numeric (relative tolerance), discrete (exact match), interval (value inside a given range, for noisy simulation results). Every checker returns a verdict with `passed` and a numeric `reward` between 0 and 1 (1 for pass, 0 for fail; partial credit only where a project explicitly defines it).
- **`RunLog`:** all messages, tool calls and results, final answer, verdict, reward, error kind, task split, tokens, wall time. Stored so it can later be exported as training data (see 2.7).

### 2.4 Agent loop

Send prompt; execute tool calls or code; repeat; stop at a final answer or after `max_tool_calls` (default 8). The prompt asks the model to end with `FINAL_ANSWER: <json>`; only that is checked.

### 2.5 Sandbox

Subprocess with timeout, memory limit, temporary working directory, no network. Limitation to state in READMEs: protects against runaway code, not hostile code.

### 2.6 Metrics

- pass@1 and **consistency** (all trials pass).
- Mean reward, tool-call count, argument validity rate (share of tool calls without a validation error), tokens, wall time.
- **Error kind** counts per condition (each project defines its own labels; see Parts 3 and 4).
- Not-applicable metrics are shown as "n/a", never as zero.

### 2.7 Configuration and CLI

`eval_config.yaml`: `provider`, `model` (or the environment variable that holds it), `trials` (default 3), `max_tool_calls`, `seed`, `timeout_s`. A `model_tier` option lets the same run be repeated with a smaller model.

- `eval run --project <name> --conditions A,B,C` prints a token estimate and asks for confirmation.
- `eval run ... --dry-run` uses the fake client.
- `eval analyze --project <name>` builds `results.md` from the logs.
- `eval export --project <name> --only-passed --out runs.jsonl` writes the logs of passing runs as JSON Lines in chat format (messages, tool calls, tool results) with task id, split and reward. **Leakage guard:** it exports only runs from `train`-split tasks. Runs from `eval`-split tasks are refused unless `--allow-eval-split` is given, and then a clear contamination warning is printed. In this version there are no `train` tasks, so the export produces an empty file; it exists so Phase 2 does not require harness changes.

### 2.8 Initial design choices

| Choice | Decision | Reason |
|---|---|---|
| Provider coupling | Behind a `ModelClient` interface | Testable; models can be swapped |
| Log format | JSON Lines, one run per line | Easy to append and re-analyze |
| Answer extraction | One `FINAL_ANSWER:` line with JSON | Unambiguous checking |
| Statistics | Mean and min-max over trials; no significance claims | Samples are small |
| Cache, parallelism | None | Simplicity |

### 2.9 Milestones and acceptance

- H1: task and condition types, fake client, loop, logging, checkers; tests pass.
- H2: both executors with sandbox, provider client.
- H3: analysis script, CLI (including `export` with the leakage guard), dry run in CI.

Acceptance: a dry run on a toy task set completes for two conditions and writes a results table; the checkers return rewards; a test with the fake client shows that `export` refuses `eval`-split runs and exports `train`-split runs correctly.

---
