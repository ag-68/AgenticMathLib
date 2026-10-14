# mathlib-mcp-lite

Five numerical tools offered to AI agents, with descriptions and errors designed for correct use. A small stand-in for the same pattern on libraries such as cuFFT, cuBLAS, and cuSOLVER.

## Status

**In progress** (2026-10-15). Milestones M1 and M2 are implemented: the five tools, generated pages, and condition B. M3 has not started.

## Scope

**Covers:** five tools (`fft`, `power_spectrum`, `convolve`, `solve_linear_system`, `least_squares`), inline arrays up to 4,096 elements, real and complex data, generated docs, and a 12-task evaluation.

**Does not cover:** GPU execution, sparse matrices, array handles for large data, a general converter, or any NVIDIA library.

## What works

The five tools run on NumPy and SciPy: `fft`, `power_spectrum`, `convolve`, `solve_linear_system`, and `least_squares`. They accept real lists and complex `{"re", "im"}` values, reject arrays larger than 4,096 elements, and return `error_code`, `message`, and `fix_hint` for bad inputs. A non-square solve points at `least_squares`. An MCP server exposes the same five tools. Tests compare the numeric results with SciPy.

`python -m mathlib_mcp.docgen` writes one page per tool, `docs/api_manifest.json`, and `docs/llms.txt` from the catalog in code. Tests fail if those files drift, and they run each documented example.

Condition B is `python -m mathlib_mcp.server --bare`. It calls the same five functions, but each description is one sentence and a failed call returns only a generic invalid-arguments error. The default server is the full text, including the recovery hint.

## What does not work yet

The 12 tasks, condition A (write NumPy or SciPy in the sandbox), and the evaluation are not implemented.

## Results (real runs only)

not run
