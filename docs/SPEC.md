# agentic-math-tools: monorepo specification

This document specifies one GitHub repository containing four related projects plus a shared evaluation harness. Put this file at `docs/SPEC.md`, and copy each project's part into that project's own `SPEC.md`.

## Contents

- Part 0: Rules for Cursor, glossary
- Part 1: Repository structure and conventions
- Part 2: Shared evaluation harness
- Part 3: Project 01, `mathlib-mcp`
- Part 4: Project 02, `api2llm` (API-to-LLM-friendly converter)
- Part 5: Project 03, `docs-rag-mcp` (documentation retrieval server)
- Part 6: Project 04, `mimo-agent-bench` (small communications benchmark)
- Part 7: Build order, time estimates, submission gates

---

## Part 0: Rules for Cursor and glossary

### Rules (apply to everything)

1. Work milestone by milestone. Finish, test and commit each milestone before starting the next.
2. Write tests first where practical. Run them and show the output.
3. **Never invent results.** Every number in any README must come from a real run whose raw log is committed. If something was not run, write "not run".
4. **Never overstate status.** Each project README has a status label (Part 1.4). Update it whenever reality changes.
5. Ask before adding a dependency that is not listed in this spec.
6. Never commit API keys. Read them from environment variables. Provide `.env.example`.
7. Never hardcode a model name. It comes from the config file or an environment variable.
8. Keep code small and readable. Prefer plain functions and dataclasses over frameworks.
9. All randomness uses fixed seeds. All tests pass offline in under 60 seconds.

### Glossary

- **MCP (Model Context Protocol):** a standard for letting an AI agent discover and call tools offered by a separate server program.
- **Host / client:** the agent application (for example Cursor) that connects to MCP servers and forwards tool calls.
- **Tool schema:** the name, description and JSON parameter definition of one tool. It is all the model sees of a tool.
- **Harness (evaluation harness):** the code that runs tasks through an agent in a controlled way, checks the answers and records results.
- **Condition:** one experimental setup, for example "no tools" or "tools with full docs".
- **Trial:** one repeated run of the same task under the same condition.
- **pass@1:** share of tasks solved correctly on the first attempt.
- **RAG (retrieval-augmented generation):** the model looks up relevant documents before answering.
- **BM25:** a classic keyword-ranking method for search.
- **Embedding:** a vector of numbers representing the meaning of a text; similar texts get similar vectors.
- **FTS5:** SQLite's built-in full-text search module.
- **recall@k:** share of queries where the correct item appears in the top k search results.
- **IR (intermediate representation):** the internal, structured description of an API that the converter builds before generating outputs.
- **Sandbox:** an isolated subprocess with time and memory limits, used to run model-written code.
- **NMSE (normalized mean squared error):** estimation error divided by the signal energy, usually reported in dB.
- **ZF / MMSE detector:** two linear receivers for MIMO (multiple antennas): zero-forcing and minimum mean squared error.

---

## Part 1: Repository structure and conventions

### 1.1 Purpose

A single portfolio repository showing how numerical-library APIs can be made usable by AI agents: through interface design (01), automated conversion (02), documentation retrieval (03) and rigorous measurement (all, with a domain-specific case in 04).

### 1.2 Design goals

- **One place to look.** A reviewer opens one link and understands the whole body of work in two minutes.
- **Honest by construction.** Status and results are visible and verifiable, not claimed.
- **Reusable core.** One evaluation harness serves all projects, so results are comparable.
- **Reproducible.** Anyone can clone, run tests offline, and rebuild result tables from committed logs.
- **Independent projects.** Each project runs on its own. Dependencies between projects are explicit (Part 7).

### 1.3 Layout

```
agentic-math-tools/
  README.md                  # overview, status table, how to navigate
  LICENSE                    # MIT
  pyproject.toml             # uv workspace root (lists all members)
  Makefile                   # make test | lint | dryrun | docs
  .env.example               # variable names only, no values
  .github/workflows/ci.yml   # ruff + pytest + dry-run eval; no network, no keys
  docs/
    SPEC.md                  # this document
    architecture.md          # one diagram + 1 page: how the projects relate
  shared/
    eval_harness/            # Part 2 (own pyproject, own tests)
  01-mathlib-mcp/            # Part 3
    README.md  SPEC.md  pyproject.toml  src/  tests/  eval/  docs/
  02-api2llm/                # Part 4
    README.md  SPEC.md  pyproject.toml  src/  tests/  configs/  eval/
  03-docs-rag-mcp/           # Part 5
    README.md  SPEC.md  pyproject.toml  src/  tests/  eval/  data/
  04-mimo-agent-bench/       # Part 6
    README.md  SPEC.md  pyproject.toml  src/  tests/  eval/
```

Create all four project folders at the start, each with a README and SPEC, even if only one has code. Their READMEs state the status honestly.

### 1.4 Status convention

Allowed labels, in order: **Planned**, **In progress**, **Working prototype**, **Complete**.

The root README contains this table, kept up to date:

| Project | What it does | Status | Evidence |
|---|---|---|---|
| 01 mathlib-mcp | ... | ... | link to results or tests |
| 02 api2llm | ... | ... | ... |
| 03 docs-rag-mcp | ... | ... | ... |
| 04 mimo-agent-bench | ... | ... | ... |

Every project README starts with the same four blocks, in this order: **Status** (label and date), **What works**, **What does not work yet**, **Results (real runs only)**.

### 1.5 Technical conventions

- Python 3.11+, `uv` workspaces, `ruff` for linting and formatting, `pytest`, type hints everywhere, `pydantic` for data models.
- Package names: `eval_harness`, `mathlib_mcp`, `api2llm`, `docs_rag_mcp`, `mimo_agent_bench`.
- Each project depends on `eval_harness` through the workspace, never by copying its code.
- Raw run logs are committed under each project's `eval/results/` as JSON Lines (one JSON object per line, one line per run).
- Result tables are generated from logs by a script, never typed by hand.
- Commit after each milestone with a clear message.

### 1.6 Initial design choices (repository level)

| Choice | Decision | Reason |
|---|---|---|
| Monorepo vs separate repos | Monorepo | Shared harness, one link for the CV, easier navigation |
| Workspace tool | `uv` workspace | Fast, single lockfile, simple member linking |
| Docs for readers | One README per project plus root overview | Reviewers read READMEs first |
| CI | GitHub Actions: lint, tests, dry-run eval | Proves the repo works offline; no secrets in CI |
| License | MIT | Permissive and common |
| Where results live | Committed raw logs plus generated tables | Reproducibility and honesty |

---

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

## Part 3: Project 01, `mathlib-mcp`

### 3.1 Purpose

Show that numerical-library functions can be offered to AI agents in a way that makes correct use easy, and measure that claim. It is a small stand-in for what a team would do for libraries such as cuFFT, cuBLAS, cuSOLVER and cuSPARSE.

### 3.2 Design goals

- The agent should rarely misuse a tool, and when it does, the error message should let it recover.
- Everything an agent needs (conventions, units, shapes, pitfalls) is stated in the tool description, not left to guessing.
- Documentation is generated from code and verified by tests.
- Quality of the design is measured, with conditions that isolate the effect of descriptions and docs.

### 3.3 Tools (8, plus 2 helpers)

| Tool | Purpose | Notes |
|---|---|---|
| `fft` | Forward discrete Fourier transform | 1-D and N-D; `norm` option; complex output |
| `ifft` | Inverse transform | Must round-trip with `fft` |
| `power_spectrum` | Power spectrum of a real signal | Inputs: signal, sample rate (Hz); returns frequencies and power |
| `convolve` | Linear convolution via FFT | `mode`: full/same/valid |
| `solve_linear_system` | Solve Ax = b | Real **and complex**; checks squareness, reports residual and conditioning |
| `least_squares` | Minimize the norm of Ax − b | Real **and complex**; returns solution, residual norm, rank |
| `truncated_svd` | Low-rank approximation | Input: matrix, rank k; returns factors and relative error |
| `sparse_matvec` | Sparse matrix times vector | COO input (row, col, value lists) |
| `store_array` / `get_array` | Create and read array handles | Helpers for large data |

Complex support in the two solvers is required because project 04 uses them.

### 3.4 Design rules (the "LLM-first" principles)

1. **Typed schema.** Every parameter has type, description, allowed values and default.
2. **Explicit conventions.** State shape order, complex encoding `{"re": [...], "im": [...]}`, units and normalization in the description.
3. **Inline for small, handles for large.** Arrays up to 10,000 elements inline; larger ones by handle. Large outputs return a handle plus a summary (shape, dtype, min, max, norm).
4. **Errors that teach.** Every error is `{"error_code", "message", "fix_hint"}`.
5. **Self-check outputs.** Residuals for solvers, reconstruction error for the SVD, shape and dtype for every output.
6. **No hidden state** except explicit handles, which expire when the server restarts (documented).
7. **Cross-references.** Each tool names related tools and when to prefer them.

### 3.5 Generated documentation

`docgen.py` introspects the tool definitions and writes:

- `docs/api_manifest.json` (validated against a JSON schema you also write),
- `docs/tools/<tool>.md` with fixed sections: Purpose, When to use and when not, Parameters, Returns, Conventions, Common mistakes, Minimal example, Related tools,
- `docs/llms.txt` (a short plain-text index for AI models).

Tests fail if generated files drift from the code, if a tool has no example, or if any documented example does not run and produce the shown output.

### 3.6 Evaluation

**Question:** does LLM-first design measurably improve agent reliability?

**Conditions**

- **A:** no tools; the model writes NumPy/SciPy code in the sandbox.
- **B:** the 8 tools with minimal one-sentence descriptions and generic errors.
- **C:** the 8 tools with the full LLM-first design.

B and C use identical numerical code. Only descriptions, schemas, docs and error messages differ.

**Tasks (20, in `eval/tasks.yaml`)**

- Spectral analysis (5), convolution and filtering (3), linear systems (4, including a wrong-tool error and an ill-conditioned case), low rank (3), sparse (2), multi-step (3).
- Include 3-4 deliberate traps: FFT normalization, frequency-bin ordering, valid vs same convolution mode, non-square matrix passed to the wrong tool.

**Metrics:** from Part 2.3, all measured over 3 trials per task and condition.

### 3.7 Initial design choices

| Choice | Decision | Reason |
|---|---|---|
| Numerics | NumPy/SciPy underneath | The point is interface and measurement, not speed |
| Server framework | Official `mcp` Python SDK (FastMCP) | Standard, minimal code |
| Array transport | Inline small, handle large | Keeps the model's context small |
| Complex numbers | `{"re","im"}` objects | JSON has no complex type; explicit and unambiguous |
| Condition B | Same code, bare text | Isolates the effect of descriptions and docs |
| GPU | Optional CuPy backend, stretch only | Needs an NVIDIA GPU; not essential |

### 3.8 Milestones and acceptance

- **M1 (tools):** `core.py`, `server.py`, structured errors (at least 6 cases), tests against NumPy/SciPy. Done when `pytest` passes and the server runs locally.
- **M2 (docs):** `docgen.py` and doc tests passing; condition B implemented.
- **M3 (tasks):** 20 tasks with checkers; dry run passes for A, B, C.
- **M4 (real runs):** full run, logs committed, `results.md` generated, README written from real numbers.

**Stopping rule:** if time is short, finish M1-M3 and run a reduced evaluation (10 tasks, 1 trial). Say so in the README.

### 3.9 Risks

- Modern models may do well in all conditions, so differences can be small. Report that honestly; the trap tasks exist to make differences visible.
- 20 tasks and 3 trials is a small sample. State that results are indicative.

---

## Part 4: Project 02, `api2llm`

### 4.1 Purpose

Automate what project 01 does by hand: read a library and generate agent-ready artifacts, plus a readiness score showing where a library is not yet agent-friendly. This corresponds to the need to turn library APIs into LLM-friendly representations at scale.

### 4.2 Design goals

- **Deterministic core.** With no LLM involved, the same input always yields the same output.
- **Verified enrichment.** Any LLM-written content is optional, and every code example it produces is executed and checked before being kept.
- **General.** Works on any importable Python module given a short config, not just project 01.
- **Explanatory.** The readiness score tells a library maintainer exactly what to fix.
- **Measurable.** Generated artifacts are evaluated with the shared harness.

### 4.3 Pipeline

1. **Discover:** from a config (module path plus allowlist of function names), find the public functions.
2. **Extract:** read signature, type hints and docstring (using `inspect` and a docstring parser that understands the NumPy docstring style).
3. **Normalize to IR:** build a typed intermediate representation.
4. **Score:** compute the readiness score from the IR.
5. **Emit:** generate outputs (4.5) from the IR using templates.
6. **Enrich (optional):** an LLM writes "common mistakes" and examples; every example runs in the sandbox and is kept only if it executes and matches expected output.
7. **Verify:** tests check the outputs against the IR and the library.

### 4.4 IR (intermediate representation) design

`Function`: `qualified_name`, `summary`, `description`, `params` (list), `returns`, `raises`, `examples`, `related`, `notes`.
`Param`: `name`, `type`, `default`, `description`, `constraints` (shape, allowed values, units where stated).

Pydantic models, serialized to JSON so the IR itself can be inspected and diffed.

### 4.5 Outputs

- **MCP server code** exposing the selected functions as tools (using the same inline-versus-handle array convention as project 01, implemented via a template).
- **Tool schemas** in the generic JSON function-calling format.
- **Per-function Markdown pages** with fixed sections.
- **`llms.txt`** index.
- **Agent rules file** (a plain Markdown file with usage rules that coding agents such as Cursor can read).
- **Readiness report** (Markdown plus JSON).

### 4.6 Readiness score

Per function, 10 checks, each pass or fail, equally weighted unless stated:

1. Has a one-line summary.
2. All parameters have type hints or documented types.
3. All parameters have descriptions.
4. Return value is described.
5. Array shape conventions are stated.
6. Units are stated where applicable.
7. Error conditions are documented.
8. At least one example exists and runs.
9. Related functions are listed.
10. No ambiguous parameters (untyped `**kwargs`, bare `*args`).

Report a score from 0 to 100 per function and the average per library, plus the list of failed checks. Keep the rubric in one file so it is easy to change and discuss.

### 4.7 Targets

- Sanity target: the functions of project 01 (generated output can be compared against the hand-written docs).
- Generalization target: about 10 functions from `scipy.fft` and `scipy.linalg`.

### 4.8 Evaluation

Uses the shared harness on a task subset built from the SciPy target functions.

**Conditions**

- **A:** raw function signatures only.
- **B:** auto-generated tools without enrichment.
- **C:** auto-generated tools with enrichment.
- **D (reference, only where functions overlap with project 01):** the hand-written project 01 docs, as an upper bound.

**Extra analysis:** relationship between a function's readiness score and the agent's success on tasks using it (a simple scatter plus rank correlation; state that the sample is small).

### 4.9 Initial design choices

| Choice | Decision | Reason |
|---|---|---|
| Reading the library | Runtime introspection (`inspect`) | Simple and reliable for Python |
| Docstring parsing | A NumPy-style docstring parser library | SciPy and NumPy use that style |
| LLM in the core path | No; optional enrichment only | Deterministic and free by default |
| Verifying enriched examples | Run every example in the sandbox | Prevents plausible but wrong docs |
| Templates | Jinja2 | Standard, readable |
| CLI | `api2llm generate --config configs/<name>.yaml --out out/` | Simple to run and demo |

### 4.10 Milestones and acceptance

- **M1:** discovery, extraction, IR, tests on a toy module.
- **M2:** emitters (server code, schemas, pages, `llms.txt`, rules file); generated server runs.
- **M3:** readiness score and report; run on project 01 and on the SciPy target.
- **M4:** optional enrichment with verified examples.
- **M5:** evaluation runs and README.

Acceptance: `api2llm generate` on the SciPy target produces a working MCP server whose tools pass a smoke test, and a readiness report.

### 4.11 Notes and stretch

- The real CUDA-X libraries are C APIs. As a documented design note (not required code), describe how the extractor would read C headers via Doxygen XML or libclang into the same IR.

### 4.12 Risks

- Docstring quality varies, so some generated pages will be thin. That is a finding, and the readiness report shows it.

---

## Part 5: Project 03, `docs-rag-mcp`

### 5.1 Purpose

Give agents on-demand access to accurate library documentation through an MCP server, and measure whether lookup reduces made-up arguments and outdated API use.

### 5.2 Design goals

- **Precise results.** A search returns complete, correctly scoped function entries, not arbitrary text fragments.
- **Small tool surface.** Few tools with predictable outputs, to keep agent behavior reliable.
- **Reproducible corpus.** The indexed documentation is tied to exact library versions.
- **Cheap to evaluate.** Retrieval quality is measured without any model cost, before agent runs.
- **Honest about benefit.** Report when retrieval does not help.

### 5.3 Corpus

- **Primary:** documentation built from the docstrings of installed packages (`numpy`, `scipy.fft`, `scipy.linalg`, `scipy.sparse.linalg`) by introspection. This pins the version and avoids scraping.
- **Optional second corpus:** the CuPy documentation sources from its open-source repository (cloned locally, MIT licensed), indexed for the retrieval-only evaluation. This ties to the GPU ecosystem and needs no GPU, since only text is indexed.
- Each corpus records the library version and build date in its metadata.

### 5.4 Chunking

- One chunk per API entry (function, class, method) with metadata: module, name, signature, version, summary.
- Long entries split by section (Parameters, Returns, Examples, Notes), each section chunk keeping a pointer to its parent entry.

### 5.5 Index and retrieval

Three retrievers, all implemented and compared:

1. **BM25:** SQLite FTS5 full-text search.
2. **Embeddings:** a small local embedding model (configurable), vectors stored in a NumPy file, cosine similarity.
3. **Hybrid:** combine the two rankings with reciprocal rank fusion (a simple rule that rewards items ranked high in either list).

### 5.6 MCP tools

- `search_docs(query, k=5, module=None)`: ranked entries with signature, one-line summary and a short snippet.
- `get_function_doc(qualified_name)`: the full entry for one function.
- `list_modules()`: available modules and versions.

Output rules: signature first, hard cap on characters per result, always include library version and source.

### 5.7 Evaluation

**Stage 1: retrieval only (no model cost).** About 40 hand-written queries, each mapped to the correct entry, such as "inverse real FFT output length" or "solve a triangular system". Metric: recall@1, recall@3, recall@5 for BM25, embeddings and hybrid.

**Stage 2: agent runs.** About 15 code-writing tasks on less-obvious API details (return value order, rarely used parameters, exact names such as the helper that picks efficient FFT sizes). The agent writes code, which runs in the sandbox.

Conditions:

- **A:** no documentation access.
- **B:** documentation through the MCP server (best retriever).
- **C:** full relevant module docs pasted into the prompt (upper bound, expensive in tokens).
- **D (optional):** only the correct function's entry (oracle).

Metrics: task success, invalid-API-use rate (code failing with attribute or argument errors), lookups per task, whether the correct entry was retrieved, tokens per task.

### 5.8 Initial design choices

| Choice | Decision | Reason |
|---|---|---|
| Corpus source | Installed-package docstrings | Version-pinned, no scraping |
| Chunking | Per API entry, split by section if long | Complete results |
| Keyword index | SQLite FTS5 | No server to install |
| Vector index | NumPy array and cosine search | Simple and enough for a few thousand chunks |
| Retriever comparison | BM25 vs embeddings vs hybrid | Informative and cheap |
| Tool count | 3 | Predictable agent behavior |
| Reuse | Entry extraction may reuse project 02's extractor; else a minimal local one | Avoid duplicate work |

### 5.9 Milestones and acceptance

- **M1:** corpus builder and chunking with tests.
- **M2:** three retrievers and the retrieval-only evaluation with a results table.
- **M3:** MCP server with three tools, smoke-tested.
- **M4:** agent tasks, runs through the shared harness, README.

Acceptance: retrieval table from real runs exists; server answers the three tools; agent evaluation run or clearly marked as not run.

### 5.10 Risks

- Models already know SciPy well, so the agent benefit may be small. This is why the tasks target obscure details, and why the retrieval-only stage matters as an independent result.

---

## Part 6: Project 04, `mimo-agent-bench`

### 6.1 Purpose

A small benchmark that tests how well AI agents handle a real signal-processing domain: MIMO (multiple-antenna) receive processing. It uses your domain expertise to design tasks with realistic traps and to classify why agents fail.

### 6.2 Why this domain (and not the alternatives)

- **Chosen: channel estimation and linear MIMO detection.** It is built on linear algebra (solve, least squares, regularized inverse) that maps directly onto the tools of project 01. Answers are deterministic for a fixed random realization, so checking is automatic. Typical mistakes (conjugate transpose, noise scaling, dB vs linear) are well known to you and easy to create traps from.
- **Not chosen: WMMSE beamforming.** It is iterative and non-convex, so the "right answer" depends on initialization and stopping rules, which makes automatic checking unreliable. Mention it as future work.
- **Included only inside the chosen domain:** a few least-squares and LMMSE channel-estimation tasks, because they share the same linear algebra.

### 6.3 Design goals

- **Small but sharp.** About 15 carefully verified tasks beat 100 sloppy ones.
- **Checkable.** Every task has a reference solved independently and an automatic checker.
- **Resistant to memorization.** Task data come from seeded random generators with fresh parameters.
- **Diagnostic.** Failures are classified, not just counted.
- **Connected.** One condition uses the tools from project 01, tying the projects together.

### 6.4 Tasks (about 15)

Each task is generated from a seed: channel matrix H, transmitted symbols x, noise n, received y.

- **Channel estimation (4):** least-squares estimate from orthogonal pilots; LMMSE estimate given the channel covariance and noise variance; NMSE of an estimate in dB; pilot design with a DFT matrix.
- **Linear detection (7):** zero-forcing detection; MMSE detection with proper noise-variance scaling; per-stream post-detection SINR; QPSK hard demapping; bit error count for a fixed realization; ZF vs MMSE on an ill-conditioned channel; effect of a given SNR in dB.
- **Multi-step (4):** estimate the channel, then detect, then count errors; compare detection with perfect versus estimated channel; select the better detector at a given SNR; compute the error rate over a small fixed batch.

### 6.5 Planned traps

- Conjugate (Hermitian) transpose versus plain transpose.
- SNR in dB versus linear scale.
- Noise variance per complex sample versus per real dimension.
- Symbol energy normalization in the MMSE regularization term.
- Complex Gaussian generation: unit total variance, not per component.
- Stream ordering and index conventions.
- Pilot scaling in the least-squares estimate.

Each trap must be documented in the task file (what the wrong answer would be and why), so failures can be classified.

### 6.6 Checking

- Matrix or vector answers: relative error against the reference below a tolerance.
- Discrete answers (bit errors, decisions): exact match for the fixed realization.
- Scalar metrics (NMSE, SINR): tolerance in dB.
- References are computed by a straightforward NumPy implementation, then re-verified by a second independent formulation (for example direct inverse versus a linear solve) in a test.

### 6.7 Conditions

- **A:** code-writing agent, no help.
- **B:** code-writing agent plus a one-page cheat sheet of the relevant formulas and conventions.
- **C:** agent with the project 01 MCP tools (solver tools handle complex data) and no code execution.

### 6.8 Metrics and failure taxonomy

- Task success (pass@1) by category and condition, over 3 trials.
- Failure classes: **convention error** (conjugation, dB, scaling), **shape or indexing error**, **numerical issue**, **wrong algorithm**, **formatting error**.
- Rule-based labels first, then you review and correct them manually. Save labels in `eval/results/failure_labels.csv`. With roughly 135 runs this is feasible and is the most original part of the project.

### 6.9 Initial design choices

| Choice | Decision | Reason |
|---|---|---|
| Task count | About 15 | Quality over quantity; low cost |
| Data | Seeded generators in `generators.py` | Reproducible and memorization-resistant |
| Answer types | Matrices, discrete decisions, scalars | Easy automatic checking |
| Condition C | Reuses project 01 tools | Connects the projects |
| Failure labels | Rule-based first, then manual review | Accuracy without heavy tooling |
| Scope | Estimation and linear detection only | Checkable; WMMSE left as future work |

### 6.10 Milestones and acceptance

- **M1:** generators, references and checkers with tests (including the independent re-verification).
- **M2:** all tasks written with documented traps.
- **M3:** dry run for A, B, C.
- **M4:** real runs, failure labelling, results table, README.

Acceptance: every task has a verified reference and a documented trap or rationale; results table and failure table come from committed logs.

### 6.11 Risks

- Condition C depends on project 01's complex-number support; if that is missing, mark condition C as not run.
- Small task set: report as indicative, with the failure taxonomy as the main contribution.

---

## Part 7: Build order, estimates, submission gates

### 7.1 Dependencies

- Harness (Part 2) first. Project 01 needs it.
- 01 before 04 (condition C uses its tools).
- 02 before 03 (03 may reuse the extractor; a minimal local extractor is the fallback).
- 02 and 04 are independent of each other.

### 7.2 Estimates (one person using Cursor)

| Step | Estimate |
|---|---|
| Harness H1-H3 | 1-1.5 days |
| Project 01 M1-M4 | 2-3 days |
| Project 02 | 2-3 days |
| Project 03 | 2-3 days |
| Project 04 | 2 days |
| Repo polish (root README, architecture page, CI) | 0.5 day |

Total about 10-13 days. These are rough; debugging the protocol setup and API cost are the main unknowns.

### 7.3 Submission gates

- **Gate 1 (can apply):** repository skeleton with the root README and status table, harness working in dry-run mode, and project 01 at "Working prototype" (tools and tests pass). The other three folders contain READMEs marked Planned.
- **Gate 2 (stronger):** project 01 Complete with a real results table.
- **Gate 3:** add 02 or 04, whichever is further along, at "Working prototype" or better.
- **Gate 4:** all four at their true status.

At each gate, update the root status table before submitting. The CV should name only what the repository shows at that moment.

### 7.4 Root README outline

1. One-paragraph pitch.
2. Status table (Part 1.4).
3. How the projects relate (one diagram).
4. Quick start (install, run tests, run a dry-run evaluation).
5. Summary of real results so far, with links to each project's results.
6. Honest limitations (small samples, NumPy-based, one model at a time).
7. How the work extends to GPU math libraries.
