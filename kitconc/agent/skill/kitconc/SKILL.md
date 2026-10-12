---
name: kitconc
description: Corpus linguistics with Kitconc - build text corpora and analyze them with word lists, keywords, concordances (KWIC), collocations, clusters and n-grams, dispersion, term/glossary extraction, corpus comparison, lexical bundles and corpus quality checks. Use when the user wants to analyze a collection of texts, study how a word or term is used, compare corpora, genres or periods, extract terminology or build a glossary, or mentions Kitconc, a corpus, concordance, collocates or keywords. Works through the Kitconc MCP server or the kitconc-tool CLI.
---

# Kitconc corpus analysis

Kitconc turns folders of texts (TXT, PDF, DOCX, ODT, EPUB, HTML, XML) into indexed corpora and
analyzes them. You answer corpus questions by **composing tools**: analyses store their tables on the
Kitconc side and return a `result_id`; you filter, join, score and enrich those results, run
pipelines or ready-made recipes, and report the evidence.

## 1. Get access

Use the first option that works:

1. **MCP tools** — if tools such as `workspace_info`, `analyze_kwic`, `recipe_run` are available
   (possibly prefixed, e.g. `mcp__kitconc__workspace_info`), use them directly.
2. **CLI** — run the same tools from the shell; output is JSON:
   ```bash
   kitconc-tool --workspace /path/to/workspace workspace_info
   kitconc-tool --workspace /path/to/workspace analyze_kwic '{"corpus": "ads", "node": "experience", "sample": 10}'
   ```
   If `kitconc-tool` is not installed: `uvx --from kitconc kitconc-tool ...` (or `uv run kitconc-tool ...`
   inside a Kitconc checkout). On Windows or with complex JSON, pass arguments on stdin with `-`:
   `kitconc-tool corpus_qa - <<'EOF'` ... `EOF`. `kitconc-tool --list` lists the tools. The CLI runs
   synchronously (no `job_start`); results persist in the workspace, so `result_id`s work across calls.
3. **Set up MCP** (offer it to the user for repeated work):
   - Claude Code: `claude mcp add kitconc -- uvx --from kitconc kitconc-mcp --workspace /path/to/workspace`
   - Codex (`~/.codex/config.toml`):
     ```toml
     [mcp_servers.kitconc]
     command = "uvx"
     args = ["--from", "kitconc", "kitconc-mcp", "--workspace", "/path/to/workspace"]
     ```

Ask the user for the workspace folder if it is not obvious (default: `./kitconc_workspace`).

## 2. Workflow

1. **Orient**: `workspace_info` (corpus ids, sizes, reference languages). To create a corpus:
   `corpus_create {"name", "source_folder", "language"}` (`english`, `portuguese`, or `no-tagging`
   for other languages).
2. **Check quality** of corpora you have not used before: `corpus_qa` (duplicates, binary or
   garbled files, outliers, encoding). Report problems before analyzing.
3. **Use a recipe when one fits** (table below): `recipe_run {"name": ..., "params": {...}}`. Read the
   `interpretation` it returns. Adapt recipes freely: `recipe_show` → edit → `pipeline_run`.
4. **Otherwise compose**: primitives → result operations (see section 4). Multi-step plans go in one
   `pipeline_run` (see `references/pipelines.md`).
5. **Long work** (large corpora, enriching hundreds of rows, `corpus_create`): with MCP use
   `job_start` and poll `job_status`; with the CLI just run it and wait.
6. **Verify** surprising numbers by reading KWIC lines or texts (`analyze_kwic` with `sample`,
   `corpus_read_file`). Watch range/DP: a "keyword" from one text is not a finding.
7. **Report** in the user's language: corpus sizes, measures and thresholds used, the key numbers,
   quoted examples with file names, and limitations. Offer `result_export` for full tables
   (`.xlsx`, `.tsv`).

## 3. Recipes

| Question | Recipe | Key params |
|---|---|---|
| Is the corpus clean? | `corpus-qa` | `corpus` |
| What is this corpus like? | `corpus-profile` | `corpus`, `top` |
| How is this word/term used? | `word-profile` | `corpus`, `node` |
| How do these near-synonyms differ? | `synonym-comparison` | `corpus`, `words` (list) |
| Collocation dictionary entry | `collocation-entry` | `corpus`, `node` |
| What is typical of this corpus? | `keyword-report` | `corpus`, `ref_corpus?` |
| How do A and B differ? | `compare-corpora` | `corpus_a`, `corpus_b` |
| Frequencies of words across corpora | `word-frequency-comparison` | `corpora`, `words` |
| Recurrent phrases for teaching/register | `lexical-bundles` | `corpus`, `size` |
| Glossary / term list | `glossary-candidates` | `corpus`, `export_path?` |
| Domain-specific terms vs a reference | `glossary-contrastive` | `corpus`, `ref_corpus` |

Periods, genres or authors inside one corpus: first `subcorpus_create {"corpus", "name",
"file_pattern"}` (regex on file names), then compare.

## 4. Core conventions

- Every corpus tool takes an explicit `corpus` id; there is no "current corpus".
- Tabular tools return `{"result_id", "total", "columns", "rows": [[...]], "next_offset"}` with
  `limit` rows (default 50). Use `limit: 0` for intermediate steps; `format: "records"` for objects.
- Never paste big tables back into calls: pass `result_id`s.
  - `result_filter` — `where` expression, `sort_by`, `keep`, `fields`, `rename`
  - `result_derive` — new columns from expressions (`per_million`, `log_likelihood`, `log_ratio`,
    `c_value`, `rank`, `matches`, `is_stopword`...) — see `references/expressions.md`
  - `result_join` (by key), `result_combine` (union / intersect / difference), `result_aggregate`
  - `result_enrich` — per row: `frequency`, `dispersion`, `example`, `definition`, `collocates`
  - `result_create` — a table you provide (seed terms, stoplists, word lists)
  - `result_page`, `result_export`, `result_list` (lineage)
- Errors are JSON `{"error": {"code", "message", "hint", "candidates"}}` — read the hint and
  candidates (e.g. valid corpus ids) and retry.
- `guide_read {"topic": "overview" | "expressions" | "pipelines" | "recipes" | "measures" |
  "terminology"}` returns the built-in documentation.
- `corpus_delete` is irreversible and needs `confirm: true`: only after the user explicitly agrees.

## 5. POS tags

Tagsets differ by corpus (built-in English: Brown tags like `NN`, `NN-TL`; built-in Portuguese:
Mac-Morpho like `N`, `PREP+ART`; spaCy: Universal POS like `NOUN`). Call `corpus_tagset` before
POS work.

- `pos` / `coll_pos` arguments of `analyze_*` tools take **raw tags** of that corpus.
- `term_candidates` patterns take **categories** (`NOUN`, `PROPN`, `ADJ`, `VERB`, `ADV`, `ADP`,
  `DET`...), plus `tag:<raw>`, `word:<word>`, `*` and `|`: e.g. `["ADJ NOUN", "NOUN word:of NOUN"]`.
  Fix wrong mappings with `tag_map`. Untagged corpora use `mode: "stopwords"` automatically.

## 6. Choosing measures

- Compare corpora with **per-million** frequencies, never raw counts.
- Keywords: log-likelihood for reliability (6.63 = p<0.01, 10.83 = p<0.001) **and** log-ratio for
  size (1 = twice as frequent); require `min_range` ≥ 2; check DP.
- Collocates: **log-dice** by default; MI only with `min_freq` ≥ 3-5 (favors rare words); t-score
  for frequent grammatical partners.
- Terms: C-value (`c_value(TERM, FREQUENCY)`) for termhood; keyness against a general corpus for
  domain specificity.
- TTR is a percentage and falls as corpora grow; compare TTR only between similar sizes.
- `context_mine` / `definition` contexts are heuristic: read them before calling them definitions.

## References

- `references/pipelines.md` — pipeline format and worked examples (custom glossary, period
  comparison, seed terms, variants).
- `references/expressions.md` — expression syntax and every function.
- `references/python-api.md` — using Kitconc directly from Python (`Corpus`, `KitconcTools`).
