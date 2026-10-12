# Project 03, docs-rag-mcp

This file is the project section of the monorepo specification. The full document, including repository rules and build order, is [docs/SPEC.md](../docs/SPEC.md).

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
