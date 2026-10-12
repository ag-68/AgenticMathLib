# Shared evaluation harness

This file is the project section of the monorepo specification. The full document, including repository rules and build order, is [docs/SPEC.md](../../docs/SPEC.md).

## Part 2: Shared evaluation harness (`shared/eval_harness`)

### 2.1 Purpose

A small, provider-independent test rig that runs tasks through an AI agent under different conditions, checks the answers, and produces comparable metrics. All four projects use it.

### 2.2 Design goals

- **Fair comparisons.** Conditions differ only in what is being tested (docs, tools, retrieval), never in the loop around them.
- **Cheap to test.** A fake model makes the full pipeline testable offline at zero cost.
- **Auditable.** Every run is logged in full, so any number can be traced to the exact conversation behind it.
- **Pluggable.** Each project supplies its own tasks, tools and checkers through small interfaces.
- **Cost-aware.** Estimates budget before a real run and asks for confirmation.

### 2.3 Core concepts and interfaces

Implement as dataclasses and `typing.Protocol` classes.

- **`Task`:** `id`, `category`, `prompt`, `inputs` (generated from a seed), `reference` (expected answer), `tolerance`, `answer_format`.
- **`Condition`:** `name`, `system_prompt`, `executor` (what happens when the model acts), `extra_context` (optional text such as docs or a cheat sheet).
- **`Executor` (protocol):** two implementations.
  - `McpExecutor`: starts an MCP server over stdio, lists its tools, forwards tool calls.
  - `CodeExecutor`: runs model-written Python in the sandbox and returns output.
- **`ModelClient` (protocol):** `complete(messages, tools) -> response`. Implementations: `ProviderClient` (real API; provider and model from config) and `FakeClient` (scripted responses for tests and dry runs).
- **`Checker` (protocol):** `check(task, final_answer) -> Verdict` with fields `passed`, `error_kind`, `detail`.
- **`RunLog`:** prompt, condition, trial, every message, every tool call and result, final answer, verdict, token counts, wall time.
- **`Metrics`:** pass@1, tool-selection accuracy, argument validity rate, error recovery rate, tool calls per task, tokens per task. Metrics that do not apply to a condition (for example tool selection with no tools) are reported as "n/a", not zero.

### 2.4 Agent loop

1. Send system prompt, extra context and task prompt.
2. If the model returns tool calls, execute them through the executor and append results. Repeat.
3. Stop when the model gives a final answer or after `max_tool_calls` (default 8).
4. The task prompt asks the model to end with `FINAL_ANSWER: <json>`. The checker parses only that.
5. Log everything, then run the checker.

### 2.5 Sandbox (for `CodeExecutor`)

- Separate subprocess with timeout (default 20 s), memory limit, temporary working directory, no network.
- Limitation to state in the README: this protects against runaway code, not against hostile code. Only model output from trusted runs is executed.

### 2.6 Configuration (`eval_config.yaml`)

`provider`, `model` (or name of the environment variable holding it), `trials` (default 3), `max_tool_calls` (default 8), `seed`, `timeout_s`, `cache` (default off).

### 2.7 CLI

- `eval run --project <name> --conditions A,B,C --trials 3` (prints token estimate first and asks for confirmation).
- `eval run ... --dry-run` (uses `FakeClient`; no cost).
- `eval analyze --project <name>` (builds the tables from logs).

### 2.8 Analysis output

For each project: overall table (metrics by condition, mean and spread over trials), per-category success table, and a list of failed runs with their error kind. Written to `eval/results/results.md`.

### 2.9 Initial design choices

| Choice | Decision | Reason |
|---|---|---|
| Provider coupling | Behind a `ModelClient` protocol | Can compare models later; testable with a fake |
| Log format | JSON Lines, one run per line | Easy to append, diff and re-analyze |
| Answer extraction | Single `FINAL_ANSWER:` line with JSON | Simple, unambiguous checking |
| Statistics | Mean and min-max over trials; no significance claims | Samples are small; do not overclaim |
| Response cache | Optional, off by default | Saves cost during development; off so reported runs are real |
| Parallelism | None in v1 | Simplicity; runs are small |

### 2.10 Milestones

- H1: dataclasses, protocols, `FakeClient`, loop, `RunLog`, checkers for numeric answers. Tests pass with the fake client.
- H2: `McpExecutor`, `CodeExecutor` with sandbox, `ProviderClient`.
- H3: analysis script, CLI, dry-run in CI.

Acceptance: a dry run over a toy task set completes for two conditions and produces a results table.

---
