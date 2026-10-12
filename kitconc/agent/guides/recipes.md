# Recipes

Recipes are named pipelines with documentation and interpretation notes. They are starting points,
not fixed reports: show one, change what the question needs, run the variant or save it.

| Tool | Purpose |
|---|---|
| `recipe_list(tag?)` | Names, descriptions, tags and parameters |
| `recipe_show(name)` | Full JSON (params, steps, output, interpretation) |
| `recipe_run(name, params)` | Run it; the response includes `interpretation` |
| `recipe_save(recipe, overwrite?)` | Save to `<workspace>/recipes/<name>.json` (overrides a built-in with the same name) |
| `job_start(recipe=name, params=...)` | Run it in the background |

## Built-in recipes

| Name | Question it answers | Main params |
|---|---|---|
| `corpus-qa` | Is the corpus clean (binary files, duplicates, encoding, outliers)? | `corpus` |
| `corpus-profile` | What is this corpus like? | `corpus`, `top` |
| `word-profile` | How is this word used? | `corpus`, `node` |
| `synonym-comparison` | How do these near-synonyms differ? | `corpus`, `words` |
| `collocation-entry` | Collocation-dictionary entry grouped by part of speech | `corpus`, `node` |
| `keyword-report` | What is the corpus about / what is typical of it? | `corpus`, `ref_corpus?` |
| `compare-corpora` | What distinguishes A from B? | `corpus_a`, `corpus_b` |
| `word-frequency-comparison` | How frequent are these words across corpora? | `corpora`, `words` |
| `lexical-bundles` | Which recurrent sequences and frames characterize the corpus? | `corpus`, `size` |
| `glossary-candidates` | Which terms belong in a glossary? | `corpus`, `export_path?` |
| `glossary-contrastive` | Which terms are specific to this domain vs a reference? | `corpus`, `ref_corpus` |

## Writing a recipe

```json
{
  "name": "verb-patterns",
  "title": "Verb + noun patterns",
  "description": "Most frequent VERB DET? NOUN combinations with examples.",
  "tags": ["phraseology"],
  "params": {"corpus": {"type": "string", "required": true}},
  "steps": [
    {"id": "pairs", "tool": "term_candidates",
     "args": {"corpus": "$params.corpus", "patterns": ["VERB NOUN", "VERB DET NOUN"],
              "stopword_edges": false, "min_freq": 3, "limit": 0}},
    {"id": "evidence", "tool": "result_enrich",
     "args": {"result_id": "$pairs.result_id", "column": "TERM", "corpus": "$params.corpus",
              "add": ["example"], "max_rows": 30}}
  ],
  "output": "evidence",
  "interpretation": "Group the pairs by verb and describe typical objects."
}
```

Names use lowercase letters, digits, `-` and `_`. `recipe_save` validates the pipeline before saving.

## Creating a recipe with an assistant

The `kitconc-recipe-author` Agent Skill guides recipe creation in Claude and Codex. Describe the
outcome you want in ordinary language; the assistant can check available corpora and existing
recipes, draft the pipeline, validate it, optionally run it, and save it in the active workspace.
The skill is installed alongside the general Kitconc skill by `kitconc-skill install`.

Example requests:

- “Create a reusable recipe that finds adjective–noun terms occurring at least three times and
  adds example contexts.”
- “Adapt `glossary-candidates` to compare terms with corpus `general-en`, validate the result, and
  save it as `legal-glossary-contrast`.”
- “Draft a recipe to compare `period-a` and `period-b` using normalized frequencies and log ratio;
  show me the steps before saving.”

The assistant should confirm corpus ids and available tools, explain the parameters and analysis
choices, and call `pipeline_validate` before execution or persistence. Validation checks pipeline
structure and references; it does not establish that an interpretation is statistically or
linguistically sound. `recipe_save` writes the JSON recipe to `<workspace>/recipes/`. Ask for a
draft if you want the JSON without saving it.
