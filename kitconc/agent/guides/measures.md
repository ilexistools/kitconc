# Choosing measures

## Frequency

- Compare corpora with **normalized frequency** (`per_million`), never raw counts.
- **Range** (number of texts) and **dispersion** guard against items that are frequent only
  because of one or two texts. Gries' **DP** goes from 0 (perfectly even) to 1 (all in one part);
  **Juilland's D** goes the other way (1 = even). `analyze_dispersion_measures`,
  `analyze_dispersion` and `result_enrich(add=["dispersion"])` provide them.

## Keyness (corpus comparison)

| Measure | Tells you | Notes |
|---|---|---|
| Log-likelihood (G2) | How reliable the difference is | Grows with corpus size. 3.84 = p<0.05, 6.63 = p<0.01, 10.83 = p<0.001, 15.13 = p<0.0001 |
| Chi-square (± Yates) | Same idea | Less reliable for low frequencies |
| Log-ratio | How large the difference is | log2 of the ratio of relative frequencies; 1 = 2x, 2 = 4x; 0.5 smoothing for zeros |
| %DIFF | Size of the difference in % | Unstable when the reference frequency is 0 |
| TF-IDF, text-dispersion keyness | Keyness that rewards spread across texts | Text-dispersion needs a reference corpus |

Good practice: filter by significance (LL, optionally with Bonferroni correction for many tests),
rank or threshold by effect size (log-ratio), require a minimum range, and check DP.

## Association (collocation)

| Measure | Favors | Use when |
|---|---|---|
| Log-dice | Strong, typical partners; stable across corpus sizes | Default for lexicography and comparisons |
| MI (mutual information) | Rare, exclusive partners | With `min_freq` >= 3-5 to avoid noise |
| MI3 | Frequent and exclusive | Compromise between MI and frequency |
| T-score | Frequent partners (often grammatical) | Describing common usage |
| Log-likelihood | Reliable association | Medium/large corpora |
| Dice, z-score, MS, MU, log-ratio | Alternatives | See the Kitconc documentation |

## Termhood

- **C-value** (`c_value(TERM, FREQUENCY)`) rewards frequent candidates that are not just parts of
  longer candidates (e.g. *stock purchase* inside *employee stock purchase plan*).
- **Keyness against a general reference** (`glossary-contrastive`) measures domain specificity.
- Combine both and require a minimum range.

## Lexical bundles and frames

- Bundles: n-grams above a normalized threshold (often 20-40 per million) occurring in at least
  3-5 texts.
- P-frames: n-grams with an open slot; `VARIANTS`, `TTR` and `ENTROPY` show slot variability.

Always report the measure, thresholds and corpus sizes used.
