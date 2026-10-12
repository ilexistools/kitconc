# Kitconc Agent Actions Contract

This document defines the current internal action-layer contract exposed by `KitconcActions` in `kitconc/agent/actions.py`.

## MCP Tool Surface

`kitconc-mcp` exposes a curated, agent-oriented tool set by default (`kitconc/agent/tools.py` and the
modules it composes). The previous behaviour (one tool per public `KitconcActions` method) remains
available with `--tool-set legacy` / `build_server(tool_set="legacy")`.

The full reference is [docs/MCP.md](../../docs/MCP.md); the guides served to agents are in
`kitconc/agent/guides/`. Summary:

| Group | Tools |
|---|---|
| Workspace | `workspace_info`, `workspace_set`, `guide_read` |
| Corpora | `corpus_list`, `corpus_info`, `corpus_files`, `corpus_read_file`, `corpus_tagset`, `corpus_qa`, `corpus_create`, `subcorpus_create`, `corpus_delete`, `corpus_import`, `corpus_export` |
| Analyses | `analyze_wordlist`, `analyze_keywords`, `analyze_kwic`, `analyze_concordance`, `analyze_collocates`, `analyze_clusters`, `analyze_ngrams`, `analyze_pframes`, `analyze_lemmas`, `analyze_dispersion`, `analyze_dispersion_measures`, `analyze_keywords_dispersion`, `analyze_word_tag_freq`, `analyze_word_freq_by_file`, `term_candidates`, `context_mine`, `text_stats`, `plot_wordcloud` |
| Semantic | `semantic_index_status`, `semantic_index_build`, `semantic_search` |
| Results | `result_list`, `result_page`, `result_create`, `result_filter`, `result_derive`, `result_join`, `result_combine`, `result_aggregate`, `result_enrich`, `result_export`, `result_delete` |
| Composition | `pipeline_validate`, `pipeline_run`, `recipe_list`, `recipe_show`, `recipe_run`, `recipe_save` |
| Jobs | `job_start`, `job_status`, `job_cancel` |

Conventions:

- Stateless: every corpus-scoped tool takes an explicit `corpus` id; `corpus_in_use` is not used.
- Tabular tools store the full result (memory + `<workspace>/.kitconc_results/`) and return one
  page: `{result_id, analysis, corpus, total, offset, returned, next_offset, columns, rows}` plus
  extras. `limit` defaults to 50 (max 1000); `format="records"` returns objects.
- Tabular `KitconcActions` methods also return `columns`, so empty results keep their schema.
- Errors return `isError=true` with `{"error": {"code", "message", "hint"?, "candidates"?}}`.
- `corpus_delete` requires `confirm=true`; pipelines, recipes and jobs cannot call destructive
  tools, `workspace_set` or other composition/job tools.
- Handlers run in worker threads and forward MCP progress notifications.
- The server also registers resources (`kitconc://...`), one prompt per recipe plus
  `plan-analysis`, and argument completion.

## Scope

- Target class: `KitconcActions`
- Coverage goal: 1:1 parity with all `do_*` commands in `kitconc/kit_cmd.py`
- Current parity: 36 / 36 commands
- Typed schemas module: `kitconc/agent/schemas.py`
- MCP runtime entrypoint: `kitconc/agent/mcp_server.py` (`kitconc-mcp`)

## State Model

- `KitconcActions` keeps two state fields:
- `_workspace: str` (absolute path)
- `corpus_in_use: str | None`

Selection behavior:
- Methods that receive `corpus_name: str | None` use the explicit value when provided.
- If not provided, they use `corpus_in_use`.
- If neither is available, `StateError` is raised.

## Error Model

- `ValidationError`: invalid input values or malformed paths.
- `NotFoundError`: missing corpus/file/command.
- `StateError`: required state not selected (for example, no current corpus).
- `SystemExit`: raised by `exit()` and `quit()`.

## Command Parity Matrix

| `kit_cmd` command | `KitconcActions` method | Input summary | Return summary |
|---|---|---|---|
| `help` | `help(command=None)` | optional command name | `str` help text |
| `exit` | `exit()` | none | raises `SystemExit` |
| `quit` | `quit()` | none | raises `SystemExit` |
| `version` | `version()` | none | `str` version |
| `cls` | `cls()` | none | `None` |
| `clear` | `clear()` | none | `None` |
| `ls` | `ls(corpus_name=None)` | optional corpus | `dict(mode, rows, total)` |
| `home` | `home()` | none | `None` |
| `delete` | `delete(corpus_name)` | corpus name | `None` |
| `cleanse` | `cleanse(corpus_name=None)` | optional corpus | `list[str]` removed files |
| `open` | `open(filename, corpus_name=None, launch=False)` | output filename | `str` absolute file path |
| `workspace` | `workspace(path=None)` | optional new workspace path | `str` workspace |
| `create` | `create(name, source, language, tagged=False, verbose=False)` | corpus metadata + source | `dict` corpus info |
| `use` | `use(corpus_name)` | corpus name | `dict` corpus info |
| `wordlist` | `wordlist(corpus_name=None, lowercase=True, limit=None, min_freq=1, min_range=1, search=None, regexp=False, stoplist=None, allowlist=None, dispersion=False)` | options | `dict(rows,total)` |
| `keywords` | `keywords(corpus_name=None, measure='log-likelihood', stoplist=None, ref_language=None, ignore_numbers=True, ignore_strange=True, min_chars=2, limit=None, ref_corpus=None, effect=None, polarity='all', p_value=None, bonferroni=False, min_freq=1, min_range=1, allowlist=None, sort_by='keyness')` | options | `dict(rows,total)` |
| `kwic` | `kwic(node, corpus_name=None, pos=None, case_sensitive=False, regexp=False, horizon=10, limit=None, wildcards=False, context=None, context_left=5, context_right=5, context_mode='or', context_exclude=False, sample=None, seed=None, kpf=None)` | options | `dict(rows,total)` |
| `concordance` | `concordance(node, corpus_name=None, pos=None, case_sensitive=False, regexp=False, limit=None, wildcards=False, sample=None, seed=None)` | options | `dict(rows,total)` |
| `collocates` | `collocates(node, corpus_name=None, pos=None, coll_pos=None, case_sensitive=False, regexp=False, left_span=5, right_span=5, lowercase=True, measure='mutual information', limit=None, extra_measures=None, min_freq=1, stoplist=None, allowlist=None, wildcards=False)` | options | `dict(rows,total)` |
| `collgraph` | `collgraph(node, corpus_name=None, pos=None, coll_pos=None, case_sensitive=False, regexp=False, left_span=5, right_span=5, measure='mutual information', plot=False)` | options | `dict(rows,total)` |
| `wtfreq` | `wtfreq(corpus_name=None, lowercase=True, limit=None)` | options | `dict(rows,total)` |
| `wfreqinfiles` | `wfreqinfiles(corpus_name=None, lowercase=True, limit=None)` | options | `dict(rows,total)` |
| `clusters` | `clusters(word, corpus_name=None, pos=None, size=3, minfreq=1, minrange=1, lowercase=True, limit=None, position='both', case_sensitive=False, regexp=False, wildcards=False, stoplist=None, allowlist=None)` | options | `dict(rows,total)` |
| `ngrams` | `ngrams(corpus_name=None, pos=None, size=3, minfreq=1, minrange=1, lowercase=True, limit=None, search=None, regexp=False, stoplist=None, allowlist=None)` | options | `dict(rows,total)` |
| `pframes` | `pframes(corpus_name=None, size=4, slots=1, pos=None, minfreq=2, minrange=1, min_variants=2, lowercase=True, stoplist=None, limit=100)` | options | `dict(rows,total)` |
| `lemmalist` | `lemmalist(corpus_name=None, lemma_file=None, lemma_format='auto', min_freq=1, min_range=1, stoplist=None, limit=None)` | options | `dict(rows,total)` |
| `dispersion_measures` | `dispersion_measures(corpus_name=None, words=None, min_freq=1, lowercase=True, limit=None)` | options | `dict(rows,total)` |
| `fileview` | `fileview(filename, corpus_name=None, node=None, case_sensitive=False, regexp=False, wildcards=False, marker='[[{}]]')` | file + optional search | `dict(filename,text,hits,tokens,types,rows,total)` |
| `wordcloud` | `wordcloud(output_path, corpus_name=None, source='wordlist', max_words=150, width=1200, height=800, colormap='viridis', stoplist='default')` | PNG path + options | `dict(output_path,source)` |
| `dispersion` | `dispersion(node, corpus_name=None, pos=None, case_sensitive=False, regexp=False, limit=None, wildcards=False)` | options | `dict(rows,total,stats,totals)` |
| `keywords_dispersion` | `keywords_dispersion(corpus_name=None, lowercase=True, limit=25, keywords_measure='log-likelihood')` | options | `dict(rows,total,totals)` |
| `text2utf8` | `text2utf8(source, target, source_encoding='mbcs', verbose=False)` | source/target folders | `dict(source,target,files,total)` |
| `examples` | `examples(dest_path=None)` | optional destination | `str` destination path |
| `export_corpus` | `export_corpus(dest_path, corpus_name=None)` | target folder + corpus | `str` zip absolute path |
| `import_corpus` | `import_corpus(filename)` | zip path | `str` imported zip path |
| `train_model` | `train_model(source, language, reflist=None, stoplist=None, verbose=False)` | training source + language | `dict` training payload |

## Additional Utility Methods (Not CLI commands)

- `from_workspace_file(filename='kitconc.tmp') -> KitconcActions`
- `save_workspace_file(filename='kitconc.tmp') -> str`
- `set_workspace(workspace) -> str`
- `workspace_status() -> dict`
- `list_commands() -> list[str]`
- `tool_catalog() -> list[dict]`
- `mcp_tool_catalog() -> list[dict]`
- `command_help(command=None) -> str`
- `app_version() -> str`
- `list_corpora() -> list[dict]`
- `corpus_exists(corpus_name) -> bool`
- `get_corpus_info(corpus_name) -> dict`
- `create_corpus(...) -> dict`
- `delete_corpus(corpus_name) -> None`
- `list_output_files(corpus_name=None) -> list[str]`
- `list_ref_languages() -> list[str]`
- `semantic_search(query, top_k=5, db_path=None, model_name=None, corpus_name=None) -> dict`
- `index_corpus(corpus_name, source_folder=None, db_path=None, model_name=None, chunk_size=500, chunk_overlap=50, batch_size=64, rebuild=False) -> dict`
- `semantic_index_status(corpus_name=None, db_path=None) -> dict`
- `export_analysis_result(analysis_result, output_path, sheet_name="Results") -> dict`
- Typed wrappers (migration started):
- `workspace_typed(request: WorkspaceRequest) -> WorkspaceResult`
- `create_typed(request: CreateCorpusRequest) -> CorpusInfo`
- `keywords_typed(request: KeywordsRequest) -> TabularResult`
- `kwic_typed(request: KwicRequest) -> TabularResult`
- `collgraph_typed(request: CollgraphRequest) -> TabularResult`
- `dispersion_typed(request: DispersionRequest) -> TabularResult`
- `keywords_dispersion_typed(request: KeywordsDispersionRequest) -> TabularResult`
- `text2utf8_typed(request: Text2Utf8Request) -> Text2Utf8Result`
- `train_model_typed(request: TrainModelRequest) -> TrainModelResult`
- `semantic_search_typed(request: SemanticSearchRequest) -> SemanticSearchResult`

## Typed Schema Classes

Defined in `kitconc/agent/schemas.py`:

- `WorkspaceRequest`
- `WorkspaceResult`
- `CreateCorpusRequest`
- `CorpusInfo`
- `KeywordsRequest`
- `KwicRequest`
- `TabularResult`
- `CollgraphRequest`
- `DispersionRequest`
- `KeywordsDispersionRequest`
- `Text2Utf8Request`
- `Text2Utf8Result`
- `ExportCorpusRequest`
- `ImportCorpusRequest`
- `TrainModelRequest`
- `TrainModelResult`
- `SemanticSearchRequest`
- `SemanticSearchResult`

## Semantic Index Workflow

- `index_corpus` reads TXT, Markdown, RST, and PDF files recursively from `source_folder`, or from the `Source` entry in the corpus `info.tab`.
- Its default index path is `<workspace>/.semantic_indexes/<corpus_name>.sqlite3`. Use `db_path` to choose another location.
- Existing indexes are not replaced unless `rebuild=True`. Rebuilds are written to a temporary database and installed only after successful indexing.
- `semantic_index_status` returns the database path, existence flag, and indexed chunk count.
- `semantic_search` uses the selected or explicit `corpus_name` index by default. An explicit `db_path` takes precedence. With no selected corpus it retains the workspace-level `semantic_index.sqlite3` fallback.
- The model and `sqlite-vec` dependencies are optional; install them with `uv sync --extra full`.

## Analysis Result Export

- Pass the complete `{ "rows": [...], "total": n }` response from an analysis action as `analysis_result`.
- Only `rows` are written to the file. Metadata such as `total` or `totals` is not exported.
- Set `output_path` to a filename ending in `.tab`, `.tsv`, or `.xlsx`; the suffix selects the format.
- TAB and TSV files are UTF-8 with tab delimiters. XLSX accepts an optional worksheet `sheet_name` (1–31 characters; `[]:*?/\\` are not allowed).
- Parent directories are created as needed. The destination is replaced only after a successful temporary-file write.
- The response includes `output_path`, `format`, `rows_written`, and `columns_written`.

Example call after `wordlist(corpus_name="ads")`:

```json
{
  "analysis_result": {"rows": [{"word": "example", "freq": 12}], "total": 1},
  "output_path": "C:/exports/wordlist.xlsx",
  "sheet_name": "Wordlist"
}
```

## Output Conventions

- Tabular results are returned as JSON-serializable dictionaries:
- `{ "rows": [ ... ], "total": <int>, "columns": [ ... ] }`
- Some analyses add totals metadata:
- `{ "rows": [ ... ], "total": <int>, "columns": [ ... ], "totals": { ... } }`

Dataframe values are normalized to Python primitive types where possible.

## Compatibility Notes

- The action layer intentionally avoids interactive prompts.
- Destructive actions (`delete`, `cleanse`) execute immediately.
- `open(..., launch=False)` resolves and validates output paths without launching external apps by default.
- `collgraph(..., plot=False)` returns collocate data without plotting by default.
- With `--tool-set legacy`, the MCP server auto-registers tools from `KitconcActions.mcp_tool_catalog()`.
- Tabular methods return `columns` alongside `rows` and `total`.
