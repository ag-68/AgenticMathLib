# agent-ready-libs: specification v2 (rescoped)

This version replaces the earlier four-project spec. Everything here is sized so that one person, working with Cursor, can finish each piece in one to three days, and so that every claim in the repository is true.

## Contents

- Part 0: Rules for Cursor, claims policy, glossary
- Part 1: Repository structure and conventions
- Part 2: Shared evaluation harness (about 1-1.25 days)
- Part 3: Project 01, `mathlib-mcp-lite` (about 1.5-2 days)
- Part 4: Project 02, `sionna-agent-kit` (about 3 days, the flagship)
- Part 5: Roadmap, plus the optional Phase 2 fine-tuning experiment (planned, not on the CV until done)
- Part 6: Build order, estimates, submission gates

---

## Part 0: Rules for Cursor, claims policy, glossary

### Rules (apply to everything)

1. Work milestone by milestone. Finish, test and commit each one before the next.
2. Write tests first where practical. Run them and show the output.
3. **Never invent results.** Every number in any README comes from a real run whose raw log is committed. If something was not run, write "not run".
4. **Never rely on memory of a library's API.** For Sionna and any other library, read the installed version's actual documentation and signatures (introspection) and derive names from them. Record exact versions.
5. **Respect human review gates.** Where this spec says the owner reviews something (the Sionna slice list, the "pitfalls" sections), stop and ask before building on it.
6. Ask before adding a dependency that is not listed.
7. Never commit API keys. Read them from environment variables; provide `.env.example`.
8. Never hardcode a model name; it comes from config or an environment variable.
9. Keep code small and readable. Fixed random seeds. Tests run offline in under 60 seconds (the Sionna example tests may use small, clearly marked slower tests that are skipped by default).

### Claims policy (important)

The repository describes only what exists in it.

- Say "an agent-ready layer and evaluation for a **slice** of Sionna" and name the slice. Never say "agent-friendly Sionna".
- Every project README has a **Scope** block with two lists: "Covers" and "Does not cover".
- Status labels are Planned, In progress, Working prototype, Complete. They are updated when reality changes.
- Results sections contain real runs only, and always state sample sizes and the single-model limitation.
- Never state or imply, in a README or on the CV, that fine-tuning or reinforcement learning was done, unless the Phase 2 experiment (Part 5.1) was actually run and its results are committed.

### Glossary

- **MCP (Model Context Protocol):** a standard that lets an AI agent discover and call tools offered by a separate server program.
- **Tool schema:** name, description and JSON parameters of a tool; all the model sees of it.
- **Harness (evaluation harness):** code that runs tasks through an agent in a controlled way, checks answers and records results.
- **Condition:** one experimental setup (for example "no help" or "with docs tools").
- **Trial:** one repeat of a task under a condition.
- **pass@1:** share of tasks solved correctly on the first attempt.
- **Consistency:** share of tasks solved in all trials.
- **Sandbox:** an isolated subprocess with time and memory limits for running model-written code.
- **Sionna:** NVIDIA's open-source library for communication-systems research; PHY is its link-level simulator.
- **OFDM:** a modulation scheme that splits data over many narrow frequency subcarriers.
- **MIMO:** using multiple transmit and receive antennas.
- **Channel estimation (LS, LMMSE):** estimating the radio channel from known pilot symbols; least squares and linear minimum mean squared error variants.
- **Linear detection (ZF, MMSE):** recovering transmitted symbols with a linear filter: zero-forcing or minimum mean squared error.
- **BER:** bit error rate.
- **FTS5:** SQLite's built-in full-text search; **BM25** is its keyword-ranking method.
- **Reward:** a number from 0 to 1 that says how well a run did (here: 1 if the checker passes, 0 if not).
- **Fine-tuning:** continuing a model's training on specialized data.
- **LoRA:** a cheap fine-tuning technique that trains a small add-on instead of the whole model.
- **Rejection sampling:** running an agent many times and keeping only the runs that earned full reward, to use as training data.
- **Split (`eval` / `train`):** which tasks are reserved for measuring (`eval`) and which may be used for training (`train`). They must never overlap.
- **Reinforcement learning (RL):** training a model from reward signals; Phase 2 starts with the simpler rejection-sampling form.

---

## Part 1: Repository structure and conventions

### 1.1 Purpose

A small portfolio repository showing a method: make numerical-library APIs easier for AI agents to use, then **measure** whether it helped. It has two worked examples: a tiny math-library server (the method in its simplest form) and a slice of NVIDIA Sionna (the method on real, changing, domain-specific software).

### 1.2 Design goals

- Reviewable in two minutes: one link, one status table, honest scope.
- Reproducible: clone, run tests offline, rebuild result tables from committed logs.
- Shared measurement code, so the two projects are evaluated the same way.
- Small enough to be believable and finishable.

### 1.3 Layout

```
agent-ready-libs/
  README.md                 # pitch, status table, scope, how to run
  LICENSE                   # MIT
  pyproject.toml            # uv workspace root
  Makefile                  # make test | lint | dryrun
  .env.example
  .github/workflows/ci.yml  # ruff + pytest + dry-run eval; no network, no keys
  docs/
    SPEC.md                 # this file
    ROADMAP.md              # Part 5 items, all marked Planned
  shared/
    eval_harness/           # Part 2 (own pyproject and tests)
  01-mathlib-mcp-lite/      # Part 3
  02-sionna-agent-kit/      # Part 4
```

Each project folder contains `README.md`, `SPEC.md`, `pyproject.toml`, `src/`, `tests/`, `eval/`, and a `docs/` folder where relevant.

### 1.4 Status table (root README)

| Project | What it does | Status | Evidence |
|---|---|---|---|
| 01 mathlib-mcp-lite | Five numerical tools as an MCP server, with generated docs and an evaluation | ... | link |
| 02 sionna-agent-kit | Agent-ready layer and evaluation for a slice of Sionna PHY | ... | link |

Every project README starts with: **Status**, **Scope** (Covers / Does not cover), **What works**, **What does not work yet**, **Results (real runs only)**.

### 1.5 Technical conventions

- Python 3.11+ (also required by current Sionna), `uv` workspace, `ruff`, `pytest`, type hints, `pydantic`.
- Packages: `eval_harness`, `mathlib_mcp`, `sionna_agent_kit`.
- Raw run logs as JSON Lines under each project's `eval/results/`. Tables are generated from logs by a script, never typed by hand.
- Commit after each milestone.

### 1.6 Initial design choices

| Choice | Decision | Reason |
|---|---|---|
| Number of projects | Two committed, rest in roadmap | Believable and finishable |
| Repo type | Monorepo | One link; shared harness |
| Planned work | `ROADMAP.md` only, no empty folders | Avoids looking like a pile of promises |
| CI | Lint, tests, dry-run evaluation, no keys | Proves it works offline |
| License | MIT for this repo | Sionna is Apache-2.0; keep its notices if any of its text is included |

---

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

## Part 3: Project 01, `mathlib-mcp-lite`, about 1.5-2 days

### 3.1 Purpose

The method in its simplest form, and the closest match to the job's subject: expose a few math-library functions to agents with clear interfaces and documentation, and measure the effect. It stands in for the pattern behind libraries such as cuFFT (FFT), cuBLAS and cuSOLVER (linear algebra).

### 3.2 Design goals

- Correct use is easy; misuse produces an error the agent can recover from.
- Everything an agent needs (shapes, units, conventions) is in the tool description.
- Documentation is generated from the code and verified by tests.
- Small enough to finish and evaluate in two days.

### 3.3 Scope

- **Covers:** five tools, inline arrays up to 4,096 elements, real and complex data, generated docs, a 12-task evaluation.
- **Does not cover:** GPU execution, sparse matrices, array handles for large data, a general converter, or any NVIDIA library.

### 3.4 Tools (5)

| Tool | Purpose | Notes |
|---|---|---|
| `fft` | Discrete Fourier transform (forward or inverse via a `direction` field) | 1-D; `norm` option; complex input and output |
| `power_spectrum` | Power spectrum of a real signal | Input: samples, sample rate in Hz; returns frequencies and power |
| `convolve` | Linear convolution | `mode`: full, same, valid |
| `solve_linear_system` | Solve Ax = b | Real and complex; checks squareness; returns residual |
| `least_squares` | Minimize the norm of Ax − b | Real and complex; returns solution, residual norm, rank |

### 3.5 Design rules

1. Typed schema for every parameter, with description, allowed values and default.
2. Conventions stated in the description: shape order, complex encoding `{"re": [...], "im": [...]}`, units, normalization.
3. Arrays above the size limit are rejected with a clear message.
4. Errors are `{"error_code", "message", "fix_hint"}`; for example, a non-square matrix passed to `solve_linear_system` suggests `least_squares`.
5. Self-check fields: residuals for solvers, shape and dtype of every output.
6. Each tool names related tools and when to prefer them.

### 3.6 Generated documentation

`docgen.py` introspects the tool definitions and writes `docs/api_manifest.json`, one Markdown page per tool (Purpose, When to use and when not, Parameters, Returns, Conventions, Common mistakes, Minimal example, Related tools) and `docs/llms.txt`. Tests fail if generated files drift from the code or if any documented example does not run and give the shown output.

### 3.7 Evaluation

**Question:** does the LLM-first design change agent reliability compared with weaker descriptions?

**Conditions**

- **A:** no tools; the model writes NumPy/SciPy code in the sandbox.
- **B:** the five tools with one-sentence descriptions and generic errors.
- **C:** the five tools with the full design.

B and C use identical numerical code.

**Tasks (12):** spectral analysis (3), convolution (2), linear systems (3, including a wrong-tool case and an ill-conditioned case), complex-data tasks (2), multi-step (2). Include three deliberate traps: FFT normalization, frequency-bin ordering, valid versus same mode.

**Error kinds:** convention error, wrong tool, invalid arguments, wrong result, formatting error.

### 3.8 Initial design choices

| Choice | Decision | Reason |
|---|---|---|
| Numerics | NumPy/SciPy underneath | The point is interface and measurement |
| Server | Official `mcp` Python SDK (FastMCP) | Standard, minimal code |
| Large data | Reject above limit | Avoids building a handle system |
| Complex numbers | `{"re","im"}` objects | JSON has no complex type |
| Condition B | Same code, bare text | Isolates the effect of descriptions |

### 3.9 Milestones and acceptance

- **M1 (0.5-1 day):** five tools, structured errors (at least five cases), tests against NumPy/SciPy.
- **M2 (0.5 day):** `docgen.py`, doc tests, condition B.
- **M3 (0.5 day):** 12 tasks, checkers, real run, `results.md`, README.

Acceptance: tests pass; server runs; results table comes from committed logs.

**Stopping rule:** if time is short, finish M1-M2 and run a reduced evaluation (6 tasks, 1 trial), and say so in the README.

### 3.10 Risks

- Modern models may do well in every condition. The traps are there to expose differences, and "no clear difference on familiar libraries" is a legitimate, reportable finding. Project 02 is the stronger test.

---

## Part 4: Project 02, `sionna-agent-kit`, about 3 days (flagship)

### 4.1 Purpose

Apply the method to a slice of real, domain-specific, changing software: NVIDIA Sionna. Provide an agent-ready layer for one end-to-end task, an OFDM MIMO link with channel estimation and linear detection, and measure whether it helps agents compared with writing Sionna code from memory.

### 4.2 Why Sionna, and what makes it a fair test

- Its API changed substantially across releases: earlier releases were TensorFlow-based and the current 2.x line is PyTorch-based (Python 3.11+ and PyTorch 2.9+ per its PyPI page at the time of writing; Cursor re-verifies). Agents trained on older material may write outdated code. This is a real corner case where documentation and tools could matter.
- It is NVIDIA's open-source software and is Apache-2.0 licensed, so building on it and quoting small documentation excerpts with attribution is permitted. Cursor re-checks the license file of the pinned version.
- It sits in the owner's field, so the owner can judge correctness and write the pitfalls.

### 4.3 Design goals

- **Honest scope:** a slice, named explicitly, with "Does not cover" listed.
- **Task-level, not function-level:** Sionna is built from configurable objects connected into pipelines, so one-tool-per-function does not fit. Tools describe tasks (run this link simulation), backed by a tested pipeline template.
- **Verified documentation:** every example in the docs runs against the pinned Sionna version.
- **Domain knowledge visible:** the "pitfalls" content is written or reviewed by the owner.
- **Measured:** evaluation compares an agent without help, with documentation access, and with the task-level tools.

### 4.4 Scope

- **Covers:** one OFDM MIMO link scenario family: a small set of modulation orders, one or two channel models, perfect-CSI versus LS versus LMMSE channel estimation, linear (LMMSE) detection or equalization, and BER versus SNR. About 10-12 documented components.
- **Does not cover:** ray tracing (Sionna RT), system-level simulation (SYS), channel coding (LDPC, Polar), neural receivers, training, or any other part of Sionna. No claim of general Sionna coverage.

### 4.5 Slice definition (human review gate)

1. Cursor installs the pinned Sionna, reads its documentation and signatures, and proposes `slice.yaml`: the 10-12 components it would document (name, import path, one-line purpose, why it is in the slice).
2. **Stop. The owner reviews and edits `slice.yaml`** before anything else is built. Wrong or missing components here would undermine the whole project.
3. Everything below derives from the approved `slice.yaml`.

### 4.6 Deliverables

1. **Component pages (10-12):** per component: Purpose; Key parameters (from the introspected signature); **Conventions and pitfalls** (drafted by Cursor, reviewed and corrected by the owner: for example, SNR definition conventions, normalization, tensor shapes); Minimal verified example; Version notes (see 4.8).
2. **Pipeline template (`slice_runner.py`):** one tested function that builds the link from a validated configuration and returns BER per SNR point, run time and the Sionna version. Configuration fields: number of transmit and receive antennas, modulation, channel model, estimator (perfect, LS, LMMSE), detector, SNR list, number of batches, seed. Size limits keep CPU runs short (for example under 60 seconds).
3. **MCP server with four tools:**
   - `list_components()`: slice components with one-line purposes.
   - `get_component_doc(name)`: the verified page.
   - `search_docs(query, k=5)`: keyword search (SQLite FTS5 with BM25) over the pages, results capped in size, with versions shown.
   - `run_link_simulation(config)`: runs the template. Invalid configurations return `{"error_code","message","fix_hint"}`, for example listing the allowed estimator names.
4. **Evaluation** (4.9) and README with real results.

### 4.7 Initial design choices

| Choice | Decision | Reason |
|---|---|---|
| Granularity of tools | Task-level (`run_link_simulation`) plus docs tools | Sionna is object-graph based |
| Exposure | Fixed tested template with options, not arbitrary object construction | Reliable, finishable, honest |
| Docs source | Introspected signatures plus owner-reviewed pitfalls | Accuracy where it matters |
| Search | SQLite FTS5 (BM25) only | Enough for about 12 pages; no embeddings needed |
| Version handling | Pin one exact Sionna version, record it everywhere | Reproducibility |
| Hardware | CPU-first with small sizes; GPU optional | Reachable on a laptop |
| Docs examples | Executed in tests | Prevents drift and wrong examples |

### 4.8 Version notes (the corner case)

- `docs/version_notes.md` lists differences between earlier TensorFlow-based releases and the current PyTorch-based line **only where Cursor verified them** from official documentation or changelogs, citing the source for each.
- Anything not verified is omitted. Do not write migration advice from memory.
- The evaluation counts "outdated API" failures separately (4.9).

### 4.9 Evaluation

**Question:** does an agent-ready layer help agents complete Sionna-based link tasks, compared with writing Sionna code unaided?

**Conditions**

- **A:** code-writing agent with Sionna installed in the sandbox, no help.
- **B:** same, plus read-only docs tools (`list_components`, `get_component_doc`, `search_docs`).
- **C:** no code execution; the agent uses all four MCP tools.

**Tasks (about 12):** each asks for a result a domain expert could verify, for example:

- BER at a given SNR for a stated configuration (interval check against a reference computed with many batches),
- which of two estimators gives lower BER at a stated SNR (discrete answer),
- the effect of changing antenna count or modulation order (discrete or interval),
- configuration questions answerable from the docs (for example, which estimator options are available in the slice),
- two multi-step tasks (compare perfect CSI with LS estimation across an SNR range and report the SNR where the gap is largest, within a tolerance).

Reference values come from the pipeline template run with many batches, with interval widths chosen from observed run-to-run variation (documented per task).

**Prepared for later reuse (no training in this version):** write each task as a parameterized template (configuration fields plus a seed) so more variants can be generated later. The 12 evaluation tasks are a fixed set in the `eval` split. Keep a short comment per template stating which parameters may vary.

**Error kinds:** **outdated API** (import error, missing attribute, or TensorFlow-style usage), invalid configuration, convention error (for example SNR definition), wrong result, formatting error, timeout. Rule-based labels from exception types first; the owner reviews and corrects them. Save labels to `eval/results/failure_labels.csv`.

**Metrics:** pass@1, consistency, outdated-API error rate, tool-call count, tokens, wall time. Optionally repeat with a smaller model tier.

**Runtime:** about 12 tasks × 3 trials × 3 conditions = 108 runs, each with a short simulation. Print the estimate and ask for confirmation before real runs.

### 4.10 Milestones and acceptance

- **S1 (0.5 day):** pin and install Sionna, propose `slice.yaml`. Owner reviews.
- **S2 (0.5-1 day):** `slice_runner.py` with tests (the pipeline produces plausible BER, estimator order is sensible, seeds are reproducible), config validation with fix hints.
- **S3 (0.5 day):** component pages with verified examples; owner reviews pitfalls; `version_notes.md`.
- **S4 (0.5 day):** MCP server with four tools and the search index; smoke tests.
- **S5 (1 day):** tasks, reference values, checkers, dry run, real runs, labels, `results.md`, README.

Acceptance: slice list approved by the owner; tests pass; docs examples run; server answers all four tools; results table and failure table come from committed logs, or the README states exactly what was not run.

**Stopping rule:** if time is short, finish S1-S4 (a working prototype layer) and run a reduced evaluation (6 tasks, 1 trial) or mark the evaluation "not run". Never fill gaps with unmeasured claims.

### 4.11 Risks

- **Environment:** Sionna 2.x needs Python 3.11+ and PyTorch 2.9+; installation and CPU speed may take time. Budget extra time in S1 and keep simulations small.
- **Slice drift:** if the owner changes `slice.yaml` after S3, pages and tasks must be revisited. Settle it early.
- **Noisy references:** BER is statistical; use enough batches and interval checks rather than exact matches.
- **Possible null result:** a capable model may do well in all conditions. Report it, with the failure taxonomy as the main contribution.
- **Prior art:** other parties may already offer documentation search for Sionna. State in the README what this project adds: the task-level tool, the verified pitfalls and the measured comparison.

---

## Part 5: Roadmap (`docs/ROADMAP.md`; all Planned; not on the CV until built)

- **Generic API-to-LLM converter** (introspection to tool schemas, pages and `llms.txt`, plus a readiness score), generalizing project 02's documentation pipeline.
- **Documentation retrieval comparison** (BM25 versus embeddings versus hybrid) over larger corpora, such as NumPy, SciPy or CuPy docs.
- **Standalone communications benchmark** (channel estimation, MIMO detection, possibly beamforming) without Sionna.
- **Synthetic unfamiliar-API test:** a small invented library, to isolate documentation effects from memorization.
- **Backend variants** for project 01 (PyTorch, CuPy) to show the same tool descriptions over different engines.
- **Verifiable-reward fine-tuning experiment** (Part 5.1).

Each item is one short paragraph with a one-line "why" and no status beyond Planned.

### 5.1 Phase 2 (optional): verifiable-reward fine-tuning experiment

**Do not start before Gate 4 and the owner's approval. Status: Planned. Not mentioned on the CV until done.**

**Purpose.** Test whether the harness's checkers, used as reward signals, can improve a small open-weight model on tasks from the Sionna slice, compared with the same model before training.

**Design goals.** Small and finishable (about 2-3 days plus a rented GPU); free of leakage between training and evaluation tasks; honest about negative or null results.

**Steps.**

1. **Generate training variants.** From the parameterized task templates (4.9), produce at least 200 `train`-split variants (different antenna counts, modulation orders, SNR points, estimator pairs). References come from the pipeline template. A test must prove that no training variant shares its configuration with any `eval` task.
2. **Collect data by rejection sampling.** Run an agent several times (4-8) per variant in condition B or C, and keep only runs with reward 1. Print a cost estimate and ask for confirmation first.
3. **Fine-tune.** Train a small open-weight model with LoRA on the exported runs, using TRL with PEFT or a comparable library. Record the model name, seed, hyperparameters and GPU hours.
4. **Evaluate.** Compare the base and fine-tuned model on the `eval` split with the same harness, conditions and trials, plus a held-out set of unseen variants. Report pass@1, consistency, mean reward and the outdated-API error rate.
5. **Report.** State sample sizes, that there was a single training seed, and that no significance is claimed. Include negative results.

**Initial design choices.**

| Choice | Decision | Reason |
|---|---|---|
| Method | Rejection-sampling fine-tuning first; a GRPO-style RL method only if time remains | Simple, robust, reuses the existing logs |
| Libraries | TRL and PEFT (to be confirmed by Cursor against current versions) | Common, documented tooling |
| Model | A small open-weight model sized to the GPU | Cheap enough to train and evaluate |
| Compute | Rented cloud GPU | No local GPU needed |
| Data format | Chat-format JSON Lines with tool calls and results | Produced by `eval export` |

**Training data source (important).** Check the model provider's terms before using a hosted model's outputs to train another model. The safe default is to generate training runs with the same open-weight model that is being trained, or to use the template-computed reference solutions as targets, and to document the choice in the README.

**Risks.** Leakage (guarded by the split field, the export guard and the disjointness test); too little data; a weak base model whose gains are small; possible null result.

**Acceptance.** Disjointness test passes; training data and configuration are committed or documented; before/after results come from committed logs; the README states exactly what was and was not done.

---

## Part 6: Build order, estimates, submission gates

### 6.1 Dependencies

- Harness first. Both projects use it.
- Projects 01 and 02 are independent; do 01 first because it is smaller and proves the pipeline.

### 6.2 Estimates (one person with Cursor)

| Step | Estimate |
|---|---|
| Harness H1-H3 (including reward field and export) | 1-1.25 days |
| Project 01 | 1.5-2 days |
| Project 02 | about 3 days |
| Repo polish (root README, roadmap, CI) | 0.5 day |
| Total | about 6-6.75 days |

Estimates are rough; installation problems and API cost are the main unknowns.

### 6.3 Submission gates

- **Gate 1 (can apply):** repository skeleton, root README with status table and scope, harness in dry-run mode, project 01 at "Working prototype". Project 02 is described in the roadmap or marked "In progress" only if work has really started.
- **Gate 2:** project 01 Complete with real results; project 02 slice approved and `slice_runner.py` tested.
- **Gate 3:** project 02 at "Working prototype" (tools and docs working).
- **Gate 4:** project 02 evaluation complete, or honestly marked as not run.

Before each submission, update the status table. The CV line names only what the repository shows at that moment.

### 6.4 CV wording guide

One line with the link, no status labels, describing only built parts. Example when both projects work: "Agent-ready numerical tooling: MCP servers, generated documentation and an evaluation harness, applied to a math-library toolkit and to a slice of NVIDIA Sionna (OFDM/MIMO link simulation); measures agent success, consistency and failure types." Remove any clause that the repository does not yet support.

### 6.5 Root README outline

1. One-paragraph pitch and the method.
2. Status table and scope statement.
3. How the two projects relate (one diagram).
4. Quick start (install, run tests, dry-run evaluation).
5. Real results so far, with links.
6. Honest limitations (small samples, one model, CPU-sized simulations).
7. Roadmap link.
