# Roadmap

Everything on this page is **Planned**. None of it is started, and none of it belongs on a CV until it is built and its results are in the repository. There are no project folders for these items.

## Generic API-to-LLM converter

**Why:** turn the Sionna kit's documentation pipeline into something that can read any Python library.

Introspect a module, emit tool schemas, pages, and `llms.txt`, and score how ready the API is for an agent.

## Documentation retrieval comparison

**Why:** measure whether keyword search is enough once the corpus is larger than a dozen pages.

Compare BM25, embeddings, and a hybrid ranker on corpora such as NumPy, SciPy, or CuPy docs.

## Standalone communications benchmark

**Why:** test channel estimation and MIMO detection without depending on Sionna.

A small NumPy benchmark, with beamforming left as a possible later addition.

## Synthetic unfamiliar-API test

**Why:** separate the effect of documentation from what a model already memorized.

A small invented library, evaluated with and without its docs.

## Backend variants for project 01

**Why:** show that the same tool descriptions can sit on more than one numeric engine.

Optional PyTorch and CuPy backends behind the five `mathlib-mcp-lite` tools.

## Verifiable-reward fine-tuning experiment

**Why:** test whether the harness checkers, used as rewards, improve a small open-weight model on the Sionna slice.

**Status: Planned.** Do not start before project 02's evaluation gate and an explicit approval. It is a LoRA fine-tune on runs with reward 1, with training tasks kept disjoint from evaluation tasks. It is not mentioned as done work until the before-and-after logs are committed.
