# Kitconc MCP server

The Kitconc MCP server lets any MCP client (Claude Code, Claude Desktop, Cursor, VS Code, custom
agents) run corpus linguistics studies on a Kitconc workspace. Instead of a fixed set of reports it
offers **composable building blocks**: primitive analyses whose results stay on the server, an
algebra of operations over those results, declarative pipelines, editable recipes and background
jobs. Short questions take one or two calls; long studies (glossaries, corpus comparisons over
large corpora) run as pipelines or jobs.

- [Running the server](#running-the-server)
- [Architecture](#architecture)
- [Tool catalog](#tool-catalog)
- [Results](#results)
- [Expressions](#expressions)
- [Pipelines](#pipelines)
- [Recipes](#recipes)
- [Jobs and progress](#jobs-and-progress)
- [POS tagsets](#pos-tagsets)
- [Resources, prompts and completion](#resources-prompts-and-completion)
- [Errors](#errors)
- [Safety](#safety)
- [Extending](#extending)
- [Legacy tool set](#legacy-tool-set)
- [Tests](#tests)

## Running the server

```bash
kitconc-mcp --transport stdio --workspace /data/kitconc_workspace
kitconc-mcp --transport streamable-http --host 127.0.0.1 --port 8001 --workspace /data/kitconc_workspace
```

| Option | Default | Meaning |
|---|---|---|
| `--workspace` | `kitconc.tmp` content, else `./kitconc_workspace` | Folder holding the corpora |
| `--workspace-file` | `kitconc.tmp` | File containing the workspace path |
| `--transport` | `stdio` | `stdio`, `streamable-http` or `sse` |
| `--host`, `--port` | `127.0.0.1`, `8001` | HTTP transports |
| `--tool-set` | `curated` | `curated` (this document) or `legacy` (one tool per `KitconcActions` method) |
| `--read-only` | off | Register only read-only tools (no corpus creation/deletion, exports, pipelines, jobs, prompts) |
| `--result-capacity` | 32 | Results kept in memory |
| `--disk-capacity` | 500 | Results kept in `<workspace>/.kitconc_results` (0 disables persistence) |
| `--job-workers` | 2 | Background jobs running concurrently |

### Client configuration

Claude Code:

```bash
claude mcp add kitconc -- uv --directory /path/to/kitconc run kitconc-mcp --workspace /data/kitconc_workspace
```

Claude Desktop, Cursor and other clients that use an `mcpServers` JSON block:

```json
{
  "mcpServers": {
    "kitconc": {
      "command": "uv",
      "args": ["--directory", "/path/to/kitconc", "run", "kitconc-mcp",
               "--workspace", "/data/kitconc_workspace"]
    }
  }
}
```

VS Code (`.vscode/mcp.json`):

```json
{
  "servers": {
    "kitconc": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/path/to/kitconc", "run", "kitconc-mcp",
               "--workspace", "/data/kitconc_workspace"]
    }
  }
}
```

HTTP clients connect to `http://127.0.0.1:8001/mcp` after starting the server with
`--transport streamable-http`.

## Architecture

```
kitconc/agent/
├── actions.py       KitconcActions: stable Python action layer over Kitconc (also used by the legacy tool set)
├── mcp_server.py    build_server() / kitconc-mcp entry point
├── tools.py         KitconcTools: curated tools, TOOL_SPECS, MCP registration, progress forwarding
├── results.py       ResultStore (memory + disk), paging, ToolFailure
├── result_ops.py    result_* algebra (filter, derive, join, combine, aggregate, enrich, create)
├── expressions.py   safe expression language and statistics (LL, log-ratio, C-value...)
├── corpus_tools.py  corpus_tagset, term_candidates, context_mine, text_stats, corpus_qa, subcorpus_create
├── tagsets.py       tagset detection, tag -> category mapping, token pattern parser
├── pipeline.py      pipeline_run / pipeline_validate
├── recipes.py       recipe_list / show / run / save
├── recipes/*.json   built-in recipes
├── jobs.py          JobManager, job_start / job_status / job_cancel
├── progress.py      progress reporting and cooperative cancellation
├── resources.py     MCP resources, recipe prompts, argument completion
└── guides/*.md      guides served by guide_read and kitconc://guide/<name>
```

Every tool is a method of `KitconcTools`. `register_tools` wraps each one in an async handler that
runs it in a worker thread (the server stays responsive), forwards progress notifications to the
client and turns every failure into a structured error. Pipelines and jobs call the same methods,
validated with the same argument schema, so a tool behaves identically whether it is called
directly, from a pipeline, from a recipe or from a job.

## Tool catalog

**Workspace and corpora**

| Tool | Purpose |
|---|---|
| `workspace_info` | Start here: workspace, version, corpora (ids and sizes), reference languages |
| `workspace_set` | Switch workspace |
| `guide_read` | Built-in documentation (overview, expressions, pipelines, recipes, measures, terminology) |
| `corpus_list`, `corpus_info` | Corpora and their metadata (TTR is a percentage) |
| `corpus_files`, `corpus_read_file` | Text file names; one text, paginated by line, with hits marked |
| `corpus_tagset` | Raw POS tags with frequency, examples and inferred category |
| `corpus_qa` | Duplicates, binary/garbled files, short/long outliers, encoding, metadata |
| `corpus_create`, `subcorpus_create` | Create a corpus from a folder, or from a selection of another corpus' texts |
| `corpus_delete` | Irreversible; requires `confirm=true` |
| `corpus_import`, `corpus_export` | Zip archives |

**Analyses** (all store their result and return a page)

| Tool | Purpose |
|---|---|
| `analyze_wordlist`, `analyze_lemmas` | Frequency lists |
| `analyze_keywords` | Keyness against the bundled reference list or another corpus; effect sizes, p-values, Bonferroni |
| `analyze_kwic`, `analyze_concordance` | Concordances (wildcards, regex, context filters, samples, KWIC pattern frequency) |
| `analyze_collocates` | 14 association measures |
| `analyze_clusters`, `analyze_ngrams`, `analyze_pframes` | Phraseology |
| `analyze_dispersion`, `analyze_dispersion_measures`, `analyze_keywords_dispersion` | Dispersion |
| `analyze_word_tag_freq`, `analyze_word_freq_by_file` | Word/tag and per-file frequencies |
| `term_candidates` | Tagset-agnostic term extraction by POS patterns, or stopword-bounded n-grams |
| `context_mine` | Definitional or custom-regex contexts of a term |
| `text_stats` | Per-text statistics |
| `plot_wordcloud` | PNG word cloud |
| `semantic_index_build`, `semantic_index_status`, `semantic_search` | Embedding search (optional extra) |

**Results**

| Tool | Purpose |
|---|---|
| `result_page` | Another page, re-sorted or with selected columns |
| `result_filter` | Filter (expression), sort, keep top N, select and rename columns |
| `result_derive` | Computed columns (expressions) |
| `result_join` | Join two results by key (left/inner/outer, case-insensitive, zero-fill) |
| `result_combine` | Union (deduplicated or stacked with labels), intersection, difference |
| `result_aggregate` | Group by and aggregate (count, sum, mean, median, min, max, nunique, first, last, list) |
| `result_enrich` | Per-row corpus evidence: hits, dispersion, example sentence, definition, collocates |
| `result_create` | Store a table you provide (seed terms, stoplists, translation tables) |
| `result_export` | Write all rows to `.xlsx`, `.tsv` or `.tab` |
| `result_list`, `result_delete` | Inspect lineage; remove a stored result |

**Composition and jobs**: `pipeline_run`, `pipeline_validate`, `recipe_list`, `recipe_show`,
`recipe_run`, `recipe_save`, `job_start`, `job_status`, `job_cancel`.

Every tool publishes MCP annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) and
described parameters with enums for measures and options.

## Results

Analyses never return whole tables. They store the table and return:

```json
{"result_id": "r-1a2b3c4d", "analysis": "collocates", "corpus": "JobAds", "total": 289,
 "offset": 0, "returned": 50, "next_offset": 50,
 "columns": ["N", "WORD", "FREQUENCY", "LEFT", "RIGHT", "ASSOCIATION"],
 "rows": [[1, "strong", 45, 40, 5, 12.73], ...]}
```

- `limit` controls the page (default 50, max 1000; `0` returns only metadata).
- `format: "records"` returns rows as objects.
- Some analyses add extras (`stats` and `totals` for dispersion, `tagset_family` for tagsets).
- Results are cached in memory and persisted as JSON in `<workspace>/.kitconc_results/`; they
  survive restarts and are pruned oldest-first beyond `--disk-capacity`.
- Each result records its `params` and `parents` (`result_list` shows the lineage).
- Empty results keep their columns, so pipelines continue with empty tables instead of failing.

## Expressions

`result_filter(where=...)` and `result_derive(columns=...)` use a safe, AST-whitelisted expression
language (no `eval`, attributes, imports or comprehensions). See
[`guides/expressions.md`](../kitconc/agent/guides/expressions.md). Highlights:

```text
FREQUENCY >= 3 and RANGE >= 2 and not is_stopword(WORD)
per_million(FREQUENCY, corpus_tokens('JobAds'))
log_likelihood(FREQUENCY, corpus_tokens('A'), FREQUENCY_R, corpus_tokens('B'))
log_ratio(...), percent_diff(...), c_value(TERM, FREQUENCY), matches(TERM, '^data ')
```

## Pipelines

A pipeline is JSON with `params`, `steps` and `output`. Steps reference params and earlier outputs
(`"$params.corpus"`, `"$terms.result_id"`, `"${params.corpus}.xlsx"`), can loop (`foreach`, `as`,
`$index`), be conditional (`when`) or tolerate errors (`continue_on_error`). Composition, job and
destructive tools are not allowed inside pipelines. Full reference:
[`guides/pipelines.md`](../kitconc/agent/guides/pipelines.md).

Example — two-word terms specific to corpus A, with examples:

```json
{
  "params": {"a": {"required": true}, "b": {"required": true}},
  "steps": [
    {"id": "ta", "tool": "term_candidates", "args": {"corpus": "$params.a", "min_freq": 2, "limit": 0}},
    {"id": "tb", "tool": "term_candidates", "args": {"corpus": "$params.b", "min_freq": 1, "limit": 0}},
    {"id": "only_a", "tool": "result_combine",
     "args": {"result_ids": ["$ta.result_id", "$tb.result_id"], "operation": "difference", "key": "TERM", "limit": 0}},
    {"id": "two_words", "tool": "result_filter",
     "args": {"result_id": "$only_a.result_id", "where": "LENGTH == 2", "sort_by": "FREQUENCY", "keep": 20, "limit": 0}},
    {"id": "evidence", "tool": "result_enrich",
     "args": {"result_id": "$two_words.result_id", "column": "TERM", "corpus": "$params.a", "add": ["example"]}}
  ]
}
```

## Recipes

Recipes are documented pipelines. Built-ins live in `kitconc/agent/recipes/`, user recipes in
`<workspace>/recipes/` (same name = override). Each has `title`, `description`, `tags`, `params`,
`steps`, `output` and `interpretation` (guidance for reading and reporting the results).

| Recipe | Question |
|---|---|
| `corpus-qa` | Is the corpus clean? |
| `corpus-profile` | What is this corpus like? |
| `word-profile` | How is this word used? |
| `synonym-comparison` | How do these near-synonyms differ? |
| `collocation-entry` | Collocation-dictionary entry by part of speech |
| `keyword-report` | What is typical of this corpus? |
| `compare-corpora` | What distinguishes A from B? |
| `word-frequency-comparison` | How frequent are these words across corpora? |
| `lexical-bundles` | Which recurrent sequences and frames characterize it? |
| `glossary-candidates` | Which terms belong in a glossary? |
| `glossary-contrastive` | Which terms are specific to this domain? |

Agents can adapt any recipe: `recipe_show` → edit → `pipeline_run`, or `recipe_save` to keep it.
See [`guides/recipes.md`](../kitconc/agent/guides/recipes.md).

## Jobs and progress

`job_start(tool=... | pipeline=... | recipe=..., params=...)` returns a `job_id` immediately;
`job_status(job_id)` reports `status` (`queued`, `running`, `succeeded`, `failed`, `cancelled`,
`interrupted`), `progress.fraction`, the current step and result ids; `include_output=true` returns
the output; `job_status()` lists recent jobs. Records are stored in `<workspace>/.kitconc_jobs/`.
`job_cancel` stops a job at its next checkpoint (between files, rows, items or steps).

Direct tool calls also send MCP progress notifications when the client provides a progress token.

## POS tagsets

`kitconc/agent/tagsets.py` detects the tagset family of a corpus from its tags — Penn/Brown (with
Brown suffixes such as `NN-TL`, `JJ-HL`), Universal POS (spaCy), Mac-Morpho (built-in Portuguese
tagger), untagged (`*`) or unknown — and maps raw tags to coarse categories (`NOUN`, `PROPN`,
`ADJ`, `VERB`, `ADV`, `ADP`, `DET`, `PRON`, `NUM`, `CONJ`, `PART`, `PUNCT`, `X`). Term patterns use
categories, so the same pattern works on every corpus; `tag_map` overrides mappings (globs allowed)
and `tag:`/`word:` elements reach raw tags and literal words. `analyze_*` tools keep using raw tags
in their `pos` arguments. See [`guides/terminology.md`](../kitconc/agent/guides/terminology.md).

## Resources, prompts and completion

Resources (for clients that let users attach context):

| URI | Content |
|---|---|
| `kitconc://corpora` | Corpora with sizes |
| `kitconc://corpus/{corpus}` | Corpus metadata |
| `kitconc://corpus/{corpus}/files` | Text file names |
| `kitconc://corpus/{corpus}/files/{filename}` | Text of one file |
| `kitconc://results/{result_id}` | A stored result as TSV |
| `kitconc://recipes`, `kitconc://recipes/{name}` | Recipes |
| `kitconc://jobs/{job_id}` | Job status and output |
| `kitconc://guide/{name}` | Guides |

Prompts: one per recipe (same name and parameters; list parameters accept comma-separated values or
JSON) plus `plan-analysis(question, corpus?)`, which guides the agent to design its own pipeline.
Prompts tell the agent to report in the user's language and cite measures, thresholds and evidence.

Completion: corpus ids for `corpus`-like prompt arguments and resource parameters; result ids, job
ids, recipe names and file names for the matching resource templates.

## Errors

Failures return `isError: true` with:

```json
{"error": {"code": "CORPUS_NOT_FOUND", "message": "Corpus not found: adz",
           "hint": "Use one of the candidate corpus ids, or create one with corpus_create.",
           "candidates": ["JobAds"]}}
```

| Code | When |
|---|---|
| `CORPUS_NOT_FOUND`, `RESULT_NOT_FOUND`, `RECIPE_NOT_FOUND`, `JOB_NOT_FOUND`, `NOT_FOUND` | Missing objects (candidates listed) |
| `INVALID_ARGUMENT`, `INVALID_EXPRESSION`, `INVALID_REFERENCE` | Bad values, expressions or `$references` |
| `INVALID_PIPELINE`, `MISSING_PARAMS`, `INVALID_RECIPE`, `ALREADY_EXISTS` | Composition problems |
| `CONFIRMATION_REQUIRED` | `corpus_delete` without `confirm=true` |
| `DEPENDENCY_MISSING` | Optional extras not installed |
| `STATE_ERROR`, `ANALYSIS_FAILED`, `JOB_FAILED`, `CANCELLED` | Runtime failures |

Schema violations (unknown enum value, wrong type) are rejected by the MCP layer before execution,
with the allowed values in the message.

## Safety

- `corpus_delete` and `result_delete` are annotated destructive; `corpus_delete` needs `confirm=true`.
- Pipelines, recipes and jobs cannot call destructive tools, `workspace_set`, or other
  pipeline/recipe/job tools.
- `--read-only` registers only read-only tools.
- Expressions cannot execute code; regexes are compiled with Python's `re`.
- Exports and corpus creation write where the client asks; run the server under an account whose
  file permissions match what agents may touch.
- Changing the workspace while jobs run affects those jobs; avoid `workspace_set` during jobs.

## Extending

- **New tool**: add a method to `KitconcTools` (or a mixin) with `Annotated[..., Field(description=...)]`
  parameters and a docstring written for the model, then add a row to `_SPEC_ROWS` in `tools.py`
  (annotations, title, group). It is automatically available to pipelines unless it belongs to the
  `composition`/`jobs` groups or is destructive. Return a JSON-serializable dict; tabular tools
  should store a result with `self._save(...)`.
- **New recipe**: add `kitconc/agent/recipes/<name>.json` (validated and run by the test suite —
  add an entry to `RECIPE_RUNS` in `tests/test_agent_workflows.py`).
- **New expression function**: add it to `_make_functions` and `FUNCTION_DOCS` in `expressions.py`.
- **New tagset**: add rules to `tagsets.py` (`detect_family`, `categorize`) and a test in
  `tests/test_agent_workflows.py`.
- **New guide**: add `kitconc/agent/guides/<name>.md`; it becomes `guide_read("<name>")` and
  `kitconc://guide/<name>`.

## Legacy tool set

`--tool-set legacy` restores the previous behaviour: one tool per public `KitconcActions` method
(`wordlist`, `kwic`, `use`, ...), with the selected-corpus state. It exists for clients configured
before the curated tool set; new integrations should use the default.

## Tests

```bash
uv run pytest tests/test_agent_mcp_server.py tests/test_agent_workflows.py
```

They cover tagset detection, expressions (including rejection of unsafe code), every result
operation, term extraction on Universal POS, Mac-Morpho and untagged corpora, corpus QA,
subcorpora, pipelines (references, `foreach`, `when`, errors), every built-in recipe, jobs
(persistence, cancellation, failures), progress notifications and the MCP prompts, resources and
completion.
