# Project 02, api2llm

This file is the project section of the monorepo specification. The full document, including repository rules and build order, is [docs/SPEC.md](../docs/SPEC.md).

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
