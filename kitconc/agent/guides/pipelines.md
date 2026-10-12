# Pipelines

A pipeline runs several tools in one call and wires outputs into inputs. Run it with
`pipeline_run(pipeline, params)`, check it with `pipeline_validate`, run it in the background with
`job_start(pipeline=..., params=...)`, or save it as a recipe with `recipe_save`.

## Format

```json
{
  "params": {
    "corpus": {"type": "string", "required": true, "description": "Corpus id"},
    "top":    {"type": "integer", "default": 50}
  },
  "steps": [
    {"id": "terms",  "tool": "term_candidates",
     "args": {"corpus": "$params.corpus", "min_freq": 3, "limit": 0}},
    {"id": "scored", "tool": "result_derive",
     "args": {"result_id": "$terms.result_id", "columns": {"CVALUE": "c_value(TERM, FREQUENCY)"}, "limit": 0}},
    {"id": "top",    "tool": "result_filter",
     "args": {"result_id": "$scored.result_id", "sort_by": "CVALUE", "keep": "$params.top"}}
  ],
  "output": "top"
}
```

| Field | Meaning |
|---|---|
| `params` | Declared parameters: `required`, `default`, `type`, `description`. Undeclared params passed at run time are also available. |
| `steps[].id` | Identifier used in references (default `step1`, `step2`...). Not `params`, `item` or `index`. |
| `steps[].tool` | Any tool except composition/job tools, destructive tools and `workspace_set`. |
| `steps[].args` | Tool arguments; may contain references. |
| `steps[].foreach` | A list (or reference to one): the step runs once per item. |
| `steps[].as` | Name of the loop variable (default `item`); `$index` is the position. |
| `steps[].when` | Skip the step when the value is empty, false, 0 or null (e.g. `"$params.export_path"`). |
| `steps[].continue_on_error` | Record the error and continue; the step output is null. |
| `output` | Step whose payload is returned in full (default: last step). |

## References

- `"$params.top"` — a whole-string reference keeps the value's type (number, list, object).
- `"$terms.result_id"`, `"$qa.issues.0.files"` — walk keys and list indexes of earlier outputs.
- `"exports/${params.corpus}.xlsx"`, `"FREQUENCY >= ${params.min_freq}"` — interpolation into text.
- In `foreach` steps: `"$item"` (or the `as` name) and `"$index"`.
- A `foreach` step's output is `{"items": [...], "result_ids": [...], "errors": [...]}` — pass
  `"$step.result_ids"` to `result_combine`.

## Result of a run

```json
{"steps": [{"id": "terms", "tool": "term_candidates", "status": "ok", "seconds": 0.2,
            "result_id": "r-1a2b3c4d", "total": 1955, "columns": ["TERM", "..."]}, ...],
 "output_step": "top", "output": {...full payload of the output step...},
 "result_ids": {"terms": "r-1a2b3c4d", "scored": "...", "top": "..."}}
```

Every intermediate result stays available for `result_page`, further operations or export.

## Tips

- Use `limit: 0` on intermediate steps to keep the run compact.
- Validate first (`pipeline_validate`) when writing a new pipeline.
- Start from a recipe: `recipe_show(name)` returns its JSON — edit steps and run the variant.
- Limits: 60 steps per pipeline, 500 items per `foreach`.
