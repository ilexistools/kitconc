# Terminology workflows

## Quick path

1. `corpus_qa` — make sure the corpus is clean (duplicates and binary files distort counts).
2. `corpus_tagset` — check that nouns, adjectives and prepositions are mapped correctly; fix with
   `tag_map` if needed (e.g. `{"NE": "PROPN"}`).
3. `recipe_run("glossary-candidates", {"corpus": ..., "export_path": "glossary.xlsx"})`, or
   `glossary-contrastive` with a general reference corpus for domain-specific terms.
4. Review the list with the user; draft entries from EXAMPLE, DEFINITION and TOP_COLLOCATES.

## Building blocks

| Need | Tool / expression |
|---|---|
| Candidates by POS pattern (any tagset) | `term_candidates(mode="pos", patterns=[...])` |
| Candidates without tags | `term_candidates(mode="stopwords", max_length=3)` |
| Termhood | `result_derive(columns={"CVALUE": "c_value(TERM, FREQUENCY)"})` |
| Domain specificity | candidates of the reference corpus + `result_join` + `log_likelihood` / `log_ratio` |
| Remove generic words | `result_filter(where="TERM not in [...]")` or a `result_create` stoplist + `result_combine(operation="difference")` |
| Seed terms from the user | `result_create(columns=["TERM"], rows=[[...]])` then `result_enrich` |
| Variants | `result_filter(where="contains(TERM, 'data')")`, `analyze_clusters` |
| Definitions | `context_mine(term)` (heuristic patterns, or your own regexes with `{term}`) |
| Usage evidence | `result_enrich(add=["example", "dispersion", "collocates", "definition"])` |
| Bilingual / comparable corpora | run the recipe on each corpus and align terms manually or by `result_join` on a translation table created with `result_create` |
| Large corpora | `job_start(recipe="glossary-candidates", params=...)` |

## Pattern syntax

Space-separated elements, one per token; `|` separates alternatives:

- Category: `NOUN`, `PROPN`, `ADJ`, `VERB`, `ADV`, `ADP`, `DET`, `PRON`, `NUM`, `CONJ`, `PART`
- Raw tag of the corpus: `tag:NN*` (glob)
- Literal word: `word:of`
- Any non-punctuation token: `*`

Default pattern sets:

- head-final (English and similar): `NOUN`, `ADJ NOUN`, `NOUN NOUN`, `ADJ NOUN NOUN`,
  `NOUN NOUN NOUN`, `ADJ ADJ NOUN`, `NOUN ADP NOUN`
- head-initial (Portuguese, Spanish, French, Italian...): `NOUN`, `NOUN ADJ`, `NOUN ADP NOUN`,
  `NOUN ADJ ADJ`, `ADJ NOUN`, `NOUN ADP NOUN ADJ`, `NOUN ADJ ADP NOUN`

Matches never cross sentence boundaries; tokens with digits or without letters are excluded unless
given as `word:`; by default candidates starting or ending with a stopword are dropped
(`stopword_edges`).
