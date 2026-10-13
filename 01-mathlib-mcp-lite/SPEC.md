# Project 01, mathlib-mcp-lite

This file is the project section of the monorepo specification. The full document is [docs/SPEC.md](../docs/SPEC.md).

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
