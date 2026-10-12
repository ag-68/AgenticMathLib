# Project 01, mathlib-mcp

This file is the project section of the monorepo specification. The full document, including repository rules and build order, is [docs/SPEC.md](../docs/SPEC.md).

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
