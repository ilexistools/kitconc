# Expressions

Used by `result_filter` (`where`) and `result_derive` (`columns`). Python syntax, evaluated safely
over whole columns (no attribute access, imports or comprehensions).

## Syntax

- Columns: `FREQUENCY`, `WORD`, `TERM`. Non-identifier names: `col('N-GRAM')`, `col('%')`,
  `col('LOG-RATIO')` (or rename them with `result_filter(rename=...)`).
- Literals: numbers, `'text'`, `True`/`False`/`None`, lists `['a', 'b']`.
- Operators: `+ - * / // % **`, `== != < <= > >=` (chainable), `in` / `not in` (lists),
  `and` / `or` / `not`.
- In pipelines, `${params.x}` is interpolated into the expression text before evaluation.

## Functions

| Function | Meaning |
|---|---|
| `col(name)` | Column by name |
| `lower(x)`, `upper(x)` | Change case |
| `length(x)` | Characters |
| `words(x)` | Number of words (n-gram length) |
| `first_word(x)`, `last_word(x)` | First / last word |
| `contains(x, s)`, `startswith(x, s)`, `endswith(x, s)` | Case-insensitive substring tests |
| `matches(x, regex)` | Regex search (`(?i)` for case-insensitive) |
| `replace(x, a, b)`, `concat(a, b, ...)` | Text manipulation |
| `is_stopword(x, language?)` | In the bundled stoplist (default: the corpus language) |
| `has_stopword_edge(x, language?)` | First or last word is a stopword |
| `abs`, `log`, `log2`, `log10`, `sqrt`, `round(x, digits)` | Math |
| `min(a, b)`, `max(a, b)`, `clip(x, lo, hi)` | Element-wise bounds |
| `coalesce(x, default)`, `is_null(x)` | Missing values (e.g. after joins) |
| `if_(condition, a, b)` | Conditional value |
| `rank(x, ascending=False)`, `zscore(x)` | Column-relative values |
| `sum(x)`, `mean(x)`, `median(x)`, `count()` | Column scalars |
| `corpus_tokens(name)`, `corpus_texts(name)` | Corpus size; accepts a column of corpus names |
| `per_million(freq, tokens)` | Normalized frequency |
| `log_likelihood(a, n1, b, n2)` | G2 keyness (3.84 p<.05, 6.63 p<.01, 10.83 p<.001) |
| `log_ratio(a, n1, b, n2)` | Effect size, log2 of relative-frequency ratio (0.5 smoothing) |
| `percent_diff(a, n1, b, n2)` | %DIFF effect size |
| `c_value(terms, freqs)` | C-value termhood (nesting-aware; single words included) |

## Examples

```text
FREQUENCY >= 3 and RANGE >= 2 and not is_stopword(WORD)
LENGTH > 1 and not has_stopword_edge(TERM)
matches(TERM, '^(data|information) ')
per_million(FREQUENCY, corpus_tokens('ads'))
round(RANGE * 100 / corpus_texts('ads'), 1)
if_(LR > 0, 'A', 'B')
```
