# How the projects relate

One repository, four projects, one evaluation harness. A reviewer can open this page and see which piece produces artifacts and which piece measures them.

```mermaid
flowchart TB
  subgraph measure [Measurement]
    harness["eval_harness<br/>tasks, conditions, logs, metrics"]
  end
  subgraph make [Making libraries agent-usable]
    p01["01 mathlib-mcp<br/>hand-designed numerical tools"]
    p02["02 api2llm<br/>generate the same kind of artifacts"]
    p03["03 docs-rag-mcp<br/>look up the real documentation"]
  end
  p04["04 mimo-agent-bench<br/>MIMO estimation and detection"]
  harness --> p01
  harness --> p02
  harness --> p03
  harness --> p04
  p01 -->|"condition C uses the solvers"| p04
  p02 -->|"extractor may be reused"| p03
```

`eval_harness` runs an agent loop under named conditions, checks answers, and writes one JSON line per run. Every project depends on it. Projects do not copy its code.

Project 01 offers eight numerical tools with descriptions, schemas, and errors aimed at agents, then measures that design against weaker descriptions and against raw code. Project 02 reads an importable Python module and emits the same kind of server, schemas, and pages, plus a readiness score. Project 03 indexes installed-package docstrings and serves search through three MCP tools. Project 04 is a small MIMO benchmark whose third condition calls project 01's complex solvers.

Build order follows those arrows: harness first, then project 01, then either project 02 or project 04. Project 03 comes after project 02 when it reuses that extractor. Current status for each project is **In progress**, recorded in that project's README. No evaluation numbers exist yet.
