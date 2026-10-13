# mathlib-mcp-lite

Five numerical tools offered to AI agents, with descriptions and errors designed for correct use. A small stand-in for the same pattern on libraries such as cuFFT, cuBLAS, and cuSOLVER.

## Status

**In progress** (2026-10-13). Repository skeleton only. Milestones M1, M2, and M3 have not started.

## Scope

**Covers:** five tools (`fft`, `power_spectrum`, `convolve`, `solve_linear_system`, `least_squares`), inline arrays up to 4,096 elements, real and complex data, generated docs, and a 12-task evaluation.

**Does not cover:** GPU execution, sparse matrices, array handles for large data, a general converter, or any NVIDIA library.

## What works

The package `mathlib_mcp` imports. The project specification is in `SPEC.md`.

## What does not work yet

The five tools, structured errors, generated documentation, the 12 tasks, and conditions A, B, and C are not implemented.

## Results (real runs only)

not run
