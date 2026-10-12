# Project 04, mimo-agent-bench

This file is the project section of the monorepo specification. The full document, including repository rules and build order, is [docs/SPEC.md](../docs/SPEC.md).

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
