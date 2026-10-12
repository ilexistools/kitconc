# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br
"""Association, keyness, effect-size and dispersion statistics.

Notation follows Evert (2004): a 2x2 contingency table with observed
frequencies O11, O12, O21, O22, row totals R1, R2, column totals C1, C2,
grand total N and expected frequencies E_ij = R_i * C_j / N.

For keywords, row 1 is the target corpus and row 2 the reference corpus;
column 1 is the word. For collocates, row 1 is the node and column 1 the
collocate.
"""
import math
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# Critical values of chi-square / log-likelihood with 1 degree of freedom
P_VALUES: Dict[str, float] = {
    'p<0.05': 3.84,
    'p<0.01': 6.63,
    'p<0.001': 10.83,
    'p<0.0001': 15.13,
}

KEYNESS_MEASURES = ('log-likelihood', 'log-likelihood-2', 'chi-square', 'chi-square-yates')
EFFECT_MEASURES = ('log-ratio', 'dice', 'log-dice', 'mi', 'mi2', 'mi3', 'ms', 'mu',
                   'rrf', 'drf', 'z-score', 't-score', '%diff', 'odds-ratio')
COLLOCATE_MEASURES = ('t-score', 'mutual information', 'mi', 'mi2', 'mi3', 'log-likelihood',
                      'log-likelihood-2', 'chi-square', 'dice', 'log-dice', 'log-ratio',
                      'z-score', 'ms', 'mu')
DISPERSION_MEASURES = ('juilland-d', 'dp', 'dp-norm', 'range', 'sd', 'cv')


def p_value_threshold(p_value) -> float:
    """Returns the critical value (1 d.f.) for a p-value label or number.

    Accepts labels such as 'p<0.05' or numbers (0.05, 0.01, 0.001, 0.0001).
    Bonferroni correction can be applied by passing the corrected p-value.
    """
    if p_value is None:
        return 0.0
    if isinstance(p_value, str):
        key = p_value.replace(' ', '').lower()
        if key in P_VALUES:
            return P_VALUES[key]
        p_value = float(key.replace('p<', ''))
    p = float(p_value)
    if not 0 < p < 1:
        raise ValueError(f'Invalid p-value: {p_value}')
    return _chi2_isf_1df(p)


def _chi2_isf_1df(p: float) -> float:
    """Inverse survival function of chi-square with 1 d.f. (bisection on erfc)."""
    lo, hi = 0.0, 200.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if math.erfc(math.sqrt(mid / 2)) > p:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 4)


def bonferroni(p_value: float, comparisons: int) -> float:
    """Returns a Bonferroni-corrected p-value."""
    return float(p_value) / max(int(comparisons), 1)


def contingency(o11: float, r1: float, c1: float, n: float) -> Tuple[float, float, float, float, float, float, float, float]:
    """Builds the observed and expected frequencies of a 2x2 table."""
    o12 = r1 - o11
    o21 = c1 - o11
    o22 = n - r1 - c1 + o11
    r2 = n - r1
    c2 = n - c1
    e11 = r1 * c1 / n if n else 0.0
    e12 = r1 * c2 / n if n else 0.0
    e21 = r2 * c1 / n if n else 0.0
    e22 = r2 * c2 / n if n else 0.0
    return (o11, o12, o21, o22, e11, e12, e21, e22)


def _xlogx(o: float, e: float) -> float:
    if o <= 0 or e <= 0:
        return 0.0
    return o * math.log(o / e)


def _keyness_table(freq_tar: float, freq_ref: float, tokens_tar: float, tokens_ref: float):
    """Table where R1=target size, R2=reference size, C1=word frequency in both."""
    n = tokens_tar + tokens_ref
    c1 = freq_tar + freq_ref
    return contingency(freq_tar, tokens_tar, c1, n)


def _sign(freq_tar: float, freq_ref: float, tokens_tar: float, tokens_ref: float) -> int:
    """+1 when the word is relatively more frequent in the target corpus."""
    nt = freq_tar / tokens_tar if tokens_tar else 0.0
    nr = freq_ref / tokens_ref if tokens_ref else 0.0
    return -1 if nt < nr else 1


def keyness(freq_tar: float, freq_ref: float, tokens_tar: float, tokens_ref: float,
            measure: str = 'log-likelihood', signed: bool = True) -> float:
    """Keyness (significance) of a word in a target corpus against a reference corpus.

    measure: 'log-likelihood' (4-term), 'log-likelihood-2' (2-term, Rayson & Garside),
             'chi-square' or 'chi-square-yates'.
    The value is negative for negative keywords when ``signed`` is True.
    """
    if tokens_tar <= 0 or tokens_ref <= 0:
        return 0.0
    o11, o12, o21, o22, e11, e12, e21, e22 = _keyness_table(freq_tar, freq_ref, tokens_tar, tokens_ref)
    # in this table O11=target freq, O21=reference freq
    if measure == 'log-likelihood':
        v = 2 * (_xlogx(o11, e11) + _xlogx(o12, e12) + _xlogx(o21, e21) + _xlogx(o22, e22))
    elif measure == 'log-likelihood-2':
        v = 2 * (_xlogx(o11, e11) + _xlogx(o21, e21))
    elif measure in ('chi-square', 'chi-square-yates'):
        yates = 0.5 if measure == 'chi-square-yates' else 0.0
        v = 0.0
        for o, e in ((o11, e11), (o12, e12), (o21, e21), (o22, e22)):
            if e > 0:
                d = max(abs(o - e) - yates, 0.0)
                v += d * d / e
    else:
        raise ValueError(f'Unknown keyness measure: {measure}. Use one of {KEYNESS_MEASURES}')
    v = max(v, 0.0)
    if signed:
        v *= _sign(freq_tar, freq_ref, tokens_tar, tokens_ref)
    return v


def effect_size(freq_tar: float, freq_ref: float, tokens_tar: float, tokens_ref: float,
                measure: str = 'log-ratio') -> float:
    """Effect size of a keyword comparison (target vs. reference).

    Zero reference frequencies are replaced by 0.5 for ratio-based measures,
    following Hardie's Log Ratio.
    """
    if tokens_tar <= 0 or tokens_ref <= 0:
        return 0.0
    rel_t = freq_tar / tokens_tar
    rel_r = (freq_ref if freq_ref > 0 else 0.5) / tokens_ref
    rel_t_safe = (freq_tar if freq_tar > 0 else 0.5) / tokens_tar
    if measure == 'log-ratio':
        return math.log2(rel_t_safe / rel_r)
    if measure == 'rrf':
        return rel_t_safe / rel_r
    if measure == 'drf':
        return freq_tar / tokens_tar - freq_ref / tokens_ref
    if measure == '%diff':
        base = freq_ref / tokens_ref
        if base == 0:
            base = 0.5 / tokens_ref
        return (rel_t - base) * 100 / base
    if measure == 'odds-ratio':
        a = freq_tar if freq_tar > 0 else 0.5
        b = freq_ref if freq_ref > 0 else 0.5
        c = max(tokens_tar - freq_tar, 0.5)
        d = max(tokens_ref - freq_ref, 0.5)
        return (a * d) / (b * c)
    # measures computed from the contingency table (target row = R1)
    return association(freq_tar, tokens_tar, freq_tar + freq_ref, tokens_tar + tokens_ref, measure)


def association(o11: float, r1: float, c1: float, n: float, measure: str = 't-score') -> float:
    """Association between a node (row) and a collocate (column).

    o11: co-occurrence frequency; r1: node frequency; c1: collocate frequency;
    n: corpus size in tokens.
    """
    if n <= 0 or o11 <= 0:
        return 0.0
    o11, o12, o21, o22, e11, e12, e21, e22 = contingency(o11, r1, c1, n)
    if measure in ('mi', 'mutual information'):
        return math.log2(o11 / e11) if e11 > 0 else 0.0
    if measure == 'mi2':
        return math.log2(o11 ** 2 / e11) if e11 > 0 else 0.0
    if measure == 'mi3':
        return math.log2(o11 ** 3 / e11) if e11 > 0 else 0.0
    if measure == 'mu':
        return o11 / e11 if e11 > 0 else 0.0
    if measure == 't-score':
        return (o11 - e11) / math.sqrt(o11)
    if measure == 'z-score':
        return (o11 - e11) / math.sqrt(e11) if e11 > 0 else 0.0
    if measure == 'dice':
        return 2 * o11 / (r1 + c1) if (r1 + c1) > 0 else 0.0
    if measure == 'log-dice':
        return 14 + math.log2(2 * o11 / (r1 + c1)) if (r1 + c1) > 0 else 0.0
    if measure == 'ms':
        return min(o11 / r1 if r1 else 0.0, o11 / c1 if c1 else 0.0)
    if measure == 'log-ratio':
        r2 = n - r1
        o21_safe = o21 if o21 > 0 else 0.5
        return math.log2((o11 / r1) / (o21_safe / r2)) if r1 > 0 and r2 > 0 else 0.0
    if measure in ('log-likelihood', 'log-likelihood-2'):
        if measure == 'log-likelihood':
            v = 2 * (_xlogx(o11, e11) + _xlogx(o12, e12) + _xlogx(o21, e21) + _xlogx(o22, e22))
        else:
            v = 2 * (_xlogx(o11, e11) + _xlogx(o21, e21))
        return v if o11 >= e11 else -v
    if measure == 'chi-square':
        v = 0.0
        for o, e in ((o11, e11), (o12, e12), (o21, e21), (o22, e22)):
            if e > 0:
                v += (o - e) ** 2 / e
        return v if o11 >= e11 else -v
    raise ValueError(f'Unknown association measure: {measure}. Use one of {COLLOCATE_MEASURES}')


# ---------------------------------------------------------------------------
# Dispersion
# ---------------------------------------------------------------------------

def dispersion(freqs: Sequence[float], sizes: Optional[Sequence[float]] = None) -> Dict[str, float]:
    """Dispersion statistics of an item over corpus parts (usually text files).

    freqs: frequency of the item in each part (include parts with 0 hits).
    sizes: size of each part in tokens; when omitted, parts are considered equal.

    Returns a dict with:
      range      number of parts where the item occurs
      sd         standard deviation of the frequencies
      cv         coefficient of variation (sd / mean)
      juilland-d Juilland's D = 1 - cv / sqrt(n - 1) (on relative frequencies
                 when part sizes differ)
      dp         Gries' Deviation of Proportions (0 = even, ~1 = uneven)
      dp-norm    DP normalised by its maximum (Lijffijt & Gries 2012)
    """
    freqs = [float(f) for f in freqs]
    n = len(freqs)
    result = {'range': float(sum(1 for f in freqs if f > 0)), 'sd': 0.0, 'cv': 0.0,
              'juilland-d': 0.0, 'dp': 0.0, 'dp-norm': 0.0}
    total = sum(freqs)
    if n == 0 or total == 0:
        return result
    if sizes is None:
        sizes = [1.0] * n
    sizes = [float(s) for s in sizes]
    corpus_size = sum(sizes)
    # standard deviation and coefficient of variation of raw frequencies
    mean = total / n
    sd = math.sqrt(sum((f - mean) ** 2 for f in freqs) / n)
    result['sd'] = sd
    result['cv'] = sd / mean if mean else 0.0
    # Juilland's D on relative frequencies (equal to raw frequencies for equal parts)
    if n > 1:
        rel = [f / s if s > 0 else 0.0 for f, s in zip(freqs, sizes)]
        rmean = sum(rel) / n
        rsd = math.sqrt(sum((r - rmean) ** 2 for r in rel) / n)
        cv = rsd / rmean if rmean else 0.0
        result['juilland-d'] = max(0.0, 1 - cv / math.sqrt(n - 1))
    else:
        result['juilland-d'] = 1.0
    # Gries' DP
    expected = [s / corpus_size for s in sizes] if corpus_size else [1.0 / n] * n
    observed = [f / total for f in freqs]
    dp = sum(abs(o - e) for o, e in zip(observed, expected)) / 2
    result['dp'] = dp
    min_s = min(expected)
    result['dp-norm'] = dp / (1 - min_s) if min_s < 1 else 0.0
    return result
