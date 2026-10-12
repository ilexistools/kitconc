# Kitconc MCP overview

Kitconc is a corpus linguistics toolkit. This server exposes it as composable building blocks so
that an agent can answer open-ended questions about corpora — not only run fixed reports.

## Layers

| Layer | Tools | Use for |
|---|---|---|
| Workspace & corpora | `workspace_info`, `corpus_*`, `subcorpus_create`, `corpus_tagset`, `corpus_qa` | Finding, creating, inspecting and checking corpora |
| Primitives | `analyze_*`, `term_candidates`, `context_mine`, `text_stats`, `semantic_*` | One analysis each; results are stored on the server |
| Result algebra | `result_filter`, `result_derive`, `result_join`, `result_combine`, `result_aggregate`, `result_enrich`, `result_create`, `result_page`, `result_export` | Turning analyses into answers without moving rows through the conversation |
| Composition | `pipeline_run`, `pipeline_validate`, `recipe_list/show/run/save` | Multi-step studies in one call; reusable, editable workflows |
| Long work | `job_start`, `job_status`, `job_cancel` | Anything that may take minutes |

## Core conventions

- **Explicit corpus.** Every corpus-scoped tool takes `corpus` (the id from `workspace_info`).
- **Results, not rows.** Analyses store the full table and return `result_id`, `columns`, `total`
  and one page (default 50 rows; `limit: 0` returns no rows — useful inside pipelines). Results
  persist in `<workspace>/.kitconc_results/` and survive restarts; old ones are pruned.
- **Compact rows.** `format: "table"` returns `{"columns": [...], "rows": [[...]]}`;
  `format: "records"` returns objects.
- **Lineage.** Every derived result records its `parents`, so a chain of operations can be traced
  with `result_list`.
- **Structured errors.** `{"error": {"code", "message", "hint", "candidates"}}`. Codes include
  `CORPUS_NOT_FOUND`, `RESULT_NOT_FOUND`, `INVALID_ARGUMENT`, `INVALID_EXPRESSION`,
  `INVALID_PIPELINE`, `MISSING_PARAMS`, `CONFIRMATION_REQUIRED`, `JOB_NOT_FOUND`, `ANALYSIS_FAILED`.

## Short, medium and long work

| Size | How |
|---|---|
| Seconds | Call primitives and result tools directly |
| Several steps | `pipeline_run` or `recipe_run` (progress is reported per step) |
| Minutes (large corpora, `result_enrich` over hundreds of rows, `corpus_create`, `semantic_index_build`) | `job_start` with a `tool`, `pipeline` or `recipe`, then `job_status` |

## Part-of-speech tagsets

Corpora may be tagged by the built-in English tagger (Brown tags with suffixes such as `NN-TL`),
the built-in Portuguese tagger (Mac-Morpho style: `N`, `ADJ`, `PREP+ART`), spaCy (Universal POS:
`NOUN`, `ADP`), pre-tagged texts or a user-trained model. `corpus_tagset` lists the raw tags, their
frequency, examples and the inferred coarse category (`NOUN`, `PROPN`, `ADJ`, `VERB`, `ADV`, `ADP`,
`DET`, `PRON`, `NUM`, `CONJ`, `PART`, `PUNCT`, `X`).

- `pos` / `coll_pos` arguments of `analyze_*` tools take **raw tags** of that corpus.
- `term_candidates` patterns take **categories** (plus `tag:<raw>`, `word:<word>`, `*`), so the same
  pattern works on every tagset. Fix wrong mappings with `tag_map` (globs allowed).

## Typical starting points

- New corpus: `recipe_run("corpus-qa")`, then `recipe_run("corpus-profile")`.
- One word: `recipe_run("word-profile")`; near-synonyms: `synonym-comparison`.
- Two corpora or periods: `subcorpus_create` + `compare-corpora`.
- Terminology: `glossary-candidates` or `glossary-contrastive` (see guide `terminology`).
- Anything else: design a pipeline (guide `pipelines`) from the primitives and result tools.

Other guides: `expressions`, `pipelines`, `recipes`, `measures`, `terminology`.
