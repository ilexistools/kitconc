---
name: kitconc-recipe-author
description: Help users design, validate, run, and save reusable Kitconc analysis recipes. Use when a user asks to create, customize, refine, or troubleshoot a Kitconc recipe or multi-step corpus workflow, especially when they want to reuse or share it.
---

# Kitconc recipe author

Turn a user's analysis goal into a small, understandable, reusable Kitconc recipe. A recipe is a
JSON pipeline. Use the Kitconc MCP tools when available; otherwise use `kitconc-tool` with the same
arguments. If neither is available, explain how to connect Kitconc or install its CLI before
claiming that a recipe was validated or saved.

## Workflow

1. **Understand the goal.** Identify the corpus or corpora, the question, desired output, filters,
   measures, and whether the workflow should be saved. Ask only for information needed to make the
   workflow meaningful. Do not invent corpus ids, tool names, fields, or parameters.
2. **Check available evidence and tools.** Use `workspace_info` to discover corpus ids and
   `recipe_list` to find an existing recipe that can be reused. Read a relevant guide with
   `guide_read` (`recipes`, `pipelines`, `expressions`, or `measures`) when needed. Use
   `recipe_show` to inspect a candidate recipe. If the user refers to a specific corpus, confirm it
   exists before building around it.
3. **Design the smallest useful workflow.** Prefer a built-in recipe as a starting point. Otherwise
   compose supported tools into ordered `steps`; declare meaningful `params`; give each step a
   stable `id`; connect outputs with references such as `$params.corpus` and
   `$terms.result_id`; set `output` to the useful final step; and write an `interpretation` that
   describes how to read the result without overstating it. Avoid unnecessary steps and huge inline
   tables. For list-like inputs, preserve their list type in parameter references.
4. **Explain the proposal.** Show the recipe name, the question it answers, required inputs, and
   the main analysis choices. Clearly label choices that remain assumptions. The user can review
   this before persistence when the request is only to draft or explore.
5. **Validate.** Call `pipeline_validate` with the proposed recipe/pipeline and representative
   parameter values where available. Resolve validation errors by checking the current tool
   schemas and guides; do not guess. Validation checks structure and references, not whether the
   corpus supports a scientifically sound interpretation.
6. **Run when useful.** If the user requested a working recipe and the corpus is available, run it
   with `pipeline_run` (or `recipe_run` after saving). For a long-running workflow, use `job_start`
   if MCP is available. Inspect the step statuses and a manageable sample of the output; adjust
   parameters or steps when results expose a problem. Distinguish a successful run from a
   scientifically reviewed result.
7. **Save when requested.** Use `recipe_save` with the complete recipe object. Choose a unique,
   lowercase name using letters, digits, hyphens, or underscores. If that user recipe already
   exists, explain that `overwrite: true` is needed and use it only when the user asked to replace
   it. Avoid names matching built-in recipes because user recipes with those names override them.
   Report the saved path returned by the tool. If the user only asked for a draft, provide the JSON
   without saving.
8. **Summarize plainly.** Report what the recipe does, its inputs, validation/run status, and whether
   it was saved. Include limitations and any assumptions that affect interpretation.

## Recipe structure

Use the schema and tool list exposed by Kitconc rather than relying on memory. A typical recipe has
`name`, `title`, `description`, `tags`, `params`, `steps`, `output`, and `interpretation`. The
`steps` array uses the same format as `pipeline_run`; `recipe_save` validates before writing it to
`<workspace>/recipes/<name>.json`.

For CLI use, call the same operations with `kitconc-tool`; each tool takes its arguments as a JSON
object, and complex requests can be provided through stdin with `-`. Use `kitconc-tool --list` to
confirm available operations. For detailed syntax and a complete example, consult the Kitconc
`recipes` and `pipelines` guides.
