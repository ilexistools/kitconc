# Kitconc Agent Actions Contract

This document defines the current internal action-layer contract exposed by `KitconcActions` in `kitconc/agent/actions.py`.

## Scope

- Target class: `KitconcActions`
- Coverage goal: 1:1 parity with all `do_*` commands in `kitconc/kit_cmd.py`
- Current parity: 31 / 31 commands
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
| `wordlist` | `wordlist(corpus_name=None, lowercase=True, limit=None)` | options | `dict(rows,total)` |
| `keywords` | `keywords(corpus_name=None, measure='log-likelihood', stoplist=None, ref_language=None, ignore_numbers=True, ignore_strange=True, min_chars=2, limit=None)` | options | `dict(rows,total)` |
| `kwic` | `kwic(node, corpus_name=None, pos=None, case_sensitive=False, regexp=False, horizon=10, limit=None)` | options | `dict(rows,total)` |
| `concordance` | `concordance(node, corpus_name=None, pos=None, case_sensitive=False, regexp=False, limit=None)` | options | `dict(rows,total)` |
| `collocates` | `collocates(node, corpus_name=None, pos=None, coll_pos=None, case_sensitive=False, regexp=False, left_span=5, right_span=5, lowercase=True, measure='mutual information', limit=None)` | options | `dict(rows,total)` |
| `collgraph` | `collgraph(node, corpus_name=None, pos=None, coll_pos=None, case_sensitive=False, regexp=False, left_span=5, right_span=5, measure='mutual information', plot=False)` | options | `dict(rows,total)` |
| `wtfreq` | `wtfreq(corpus_name=None, lowercase=True, limit=None)` | options | `dict(rows,total)` |
| `wfreqinfiles` | `wfreqinfiles(corpus_name=None, lowercase=True, limit=None)` | options | `dict(rows,total)` |
| `clusters` | `clusters(word, corpus_name=None, pos=None, size=3, minfreq=1, minrange=1, lowercase=True, limit=None)` | options | `dict(rows,total)` |
| `ngrams` | `ngrams(corpus_name=None, pos=None, size=3, minfreq=1, minrange=1, lowercase=True, limit=None)` | options | `dict(rows,total)` |
| `dispersion` | `dispersion(node, corpus_name=None, pos=None, case_sensitive=False, regexp=False, limit=None)` | options | `dict(rows,total,totals)` |
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
- `semantic_search(query, top_k=5, db_path=None, model_name=None) -> dict`
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

## Output Conventions

- Tabular results are returned as JSON-serializable dictionaries:
- `{ "rows": [ ... ], "total": <int> }`
- Some analyses add totals metadata:
- `{ "rows": [ ... ], "total": <int>, "totals": { ... } }`

Dataframe values are normalized to Python primitive types where possible.

## Compatibility Notes

- The action layer intentionally avoids interactive prompts.
- Destructive actions (`delete`, `cleanse`) execute immediately.
- `open(..., launch=False)` resolves and validates output paths without launching external apps by default.
- `collgraph(..., plot=False)` returns collocate data without plotting by default.
- MCP server auto-registers tools from `KitconcActions.mcp_tool_catalog()`.
