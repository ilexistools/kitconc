# Expressions

`result_filter(where=...)` and `result_derive(columns={...})` accept a small, safe expression
language with Python syntax. It is evaluated over whole columns at once; there is no `eval`, no
attribute access, no imports and only the functions listed below.

## Syntax

- **Columns** are identifiers: `FREQUENCY`, `WORD`, `TERM`. Columns whose names are not identifiers
  (`N-GRAM`, `%`, `LOG-RATIO`) are read with `col('N-GRAM')`. Rename them with
  `result_filter(rename=...)` if you use them often.
- **Literals**: numbers, `'strings'`, `True`/`False`/`None`, lists `['a', 'b']`.
- **Arithmetic**: `+ - * / // % **` (`+` concatenates when one side is a string).
- **Comparison**: `== != < <= > >=`, chained (`2 <= LENGTH <= 3`), `in` / `not in` with a list.
- **Logic**: `and`, `or`, `not` (element-wise).
- **Conditional**: `if_(condition, a, b)`.

## Examples

```text
FREQUENCY >= 3 and RANGE >= 2
WORD not in ['said', 'says'] and not is_stopword(WORD)
LENGTH > 1 and not has_stopword_edge(TERM)
matches(TERM, '^(data|information) ')
per_million(FREQUENCY, corpus_tokens('JobAds'))
log_ratio(FREQUENCY, corpus_tokens('A'), FREQUENCY_R, corpus_tokens('B'))
round(RANGE * 100 / corpus_texts('JobAds'), 1)
c_value(TERM, FREQUENCY)
if_(LOG_RATIO > 0, 'A', 'B')
```

Inside pipelines, `${params.x}` interpolates parameter values into the expression text, e.g.
`"FREQUENCY >= ${params.min_freq}"` or `"corpus_tokens('${params.corpus}')"`.

## Notes

- `is_stopword` and `has_stopword_edge` default to the stoplist of the result's corpus language.
- `corpus_tokens` accepts a corpus name or a column of corpus names (after a labeled
  `result_combine`), so `per_million(FREQUENCY, corpus_tokens(CORPUS))` works on stacked tables.
- After a left/outer `result_join`, missing right-side numbers are 0 by default (`fill_zero`);
  use `coalesce(x, default)` for other columns.
- `sum`, `mean`, `median`, `count`, `rank`, `zscore` operate over the whole column.
