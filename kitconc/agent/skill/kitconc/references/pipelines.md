# Pipelines

`pipeline_run {"pipeline": {...}, "params": {...}}` runs several tools in one call. Check new
pipelines with `pipeline_validate` first. Every intermediate `result_id` stays available.

## Format

```json
{
  "params": {"corpus": {"type": "string", "required": true}, "top": {"default": 50}},
  "steps": [
    {"id": "step_a", "tool": "<tool>", "args": {"corpus": "$params.corpus", "limit": 0}},
    {"id": "step_b", "tool": "<tool>", "args": {"result_id": "$step_a.result_id"}}
  ],
  "output": "step_b"
}
```

- `"$params.x"`, `"$step.result_id"`, `"$step.items.0.total"` — whole-string references keep types.
- `"${params.corpus}"` — interpolation inside longer strings and expressions.
- `"foreach": "$params.words", "as": "w"` — run a step per item (`$w`, `$index`); output has
  `items`, `result_ids`, `errors`.
- `"when": "$params.export_path"` — skip when empty/false/null.
- `"continue_on_error": true` — record the error and continue.
- Not allowed inside pipelines: composition/job tools, destructive tools, `workspace_set`.
- Limits: 60 steps, 500 `foreach` items.

## Example: two-word terms specific to corpus A, with evidence

```json
{
  "params": {"a": {"required": true}, "b": {"required": true}},
  "steps": [
    {"id": "ta", "tool": "term_candidates", "args": {"corpus": "$params.a", "min_freq": 2, "limit": 0}},
    {"id": "tb", "tool": "term_candidates", "args": {"corpus": "$params.b", "min_freq": 1, "limit": 0}},
    {"id": "only_a", "tool": "result_combine",
     "args": {"result_ids": ["$ta.result_id", "$tb.result_id"], "operation": "difference", "key": "TERM", "limit": 0}},
    {"id": "two", "tool": "result_filter",
     "args": {"result_id": "$only_a.result_id", "where": "LENGTH == 2 and RANGE >= 2", "sort_by": "FREQUENCY", "keep": 30, "limit": 0}},
    {"id": "evidence", "tool": "result_enrich",
     "args": {"result_id": "$two.result_id", "column": "TERM", "corpus": "$params.a", "add": ["example", "dispersion"]}}
  ]
}
```

## Example: keyness between two periods of one corpus

1. `subcorpus_create {"corpus": "news", "name": "news_2010s", "file_pattern": "^201"}`
2. `subcorpus_create {"corpus": "news", "name": "news_2020s", "file_pattern": "^202"}`
3. `recipe_run {"name": "compare-corpora", "params": {"corpus_a": "news_2020s", "corpus_b": "news_2010s"}}`

## Example: custom keyness table with expressions

```json
{
  "params": {"a": {"required": true}, "b": {"required": true}},
  "steps": [
    {"id": "wa", "tool": "analyze_wordlist", "args": {"corpus": "$params.a", "limit": 0}},
    {"id": "wb", "tool": "analyze_wordlist", "args": {"corpus": "$params.b", "limit": 0}},
    {"id": "j", "tool": "result_join",
     "args": {"left_id": "$wa.result_id", "right_id": "$wb.result_id", "on": "WORD", "how": "outer",
              "right_fields": ["FREQUENCY"], "suffix": "_B", "limit": 0}},
    {"id": "s", "tool": "result_derive", "args": {"result_id": "$j.result_id", "limit": 0, "columns": {
      "LL": "log_likelihood(FREQUENCY, corpus_tokens('${params.a}'), FREQUENCY_B, corpus_tokens('${params.b}'))",
      "LR": "log_ratio(FREQUENCY, corpus_tokens('${params.a}'), FREQUENCY_B, corpus_tokens('${params.b}'))"}}},
    {"id": "top", "tool": "result_filter",
     "args": {"result_id": "$s.result_id", "where": "LL >= 10.83 and LR >= 1 and not is_stopword(WORD)", "sort_by": "LL", "keep": 50}}
  ]
}
```

## Example: user-provided seed terms

```json
{"steps": [
  {"id": "seeds", "tool": "result_create",
   "args": {"columns": ["TERM"], "rows": [["machine learning"], ["data quality"], ["neural network"]]}},
  {"id": "evidence", "tool": "result_enrich",
   "args": {"result_id": "$seeds.result_id", "column": "TERM", "corpus": "tech",
            "add": ["frequency", "dispersion", "example", "definition", "collocates"]}}
]}
```

## Example: compare several words in one loop

```json
{"params": {"corpus": {"required": true}, "words": {"default": ["big", "large", "huge"]}},
 "steps": [
  {"id": "coll", "tool": "analyze_collocates", "foreach": "$params.words", "as": "w",
   "args": {"corpus": "$params.corpus", "node": "$w", "measure": "log-dice", "min_freq": 2, "stoplist": "default", "limit": 0},
   "continue_on_error": true},
  {"id": "stacked", "tool": "result_combine",
   "args": {"result_ids": "$coll.result_ids", "operation": "union", "key": "WORD", "source_column": "NODE",
            "label_from_param": "node", "deduplicate": false, "limit": 0}},
  {"id": "by_word", "tool": "result_aggregate",
   "args": {"result_id": "$stacked.result_id", "group_by": ["WORD"],
            "aggregations": {"NODES": "list(NODE)", "N_NODES": "nunique(NODE)"}, "sort_by": "N_NODES"}}
]}
```
