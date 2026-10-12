# -*- coding: utf-8 -*-
"""Small, safe expression language evaluated over result tables.

Expressions use Python syntax but are evaluated by walking a whitelisted AST: no attribute access,
no subscripts, no lambdas, no imports and only the functions listed in :data:`FUNCTIONS`. Column
names are plain identifiers (``FREQUENCY``); columns whose names are not identifiers are read with
``col("N-GRAM")``. Operations are vectorized over pandas Series.

Examples::

    FREQUENCY >= 3 and RANGE >= 2
    WORD not in ['the', 'of'] and not is_stopword(WORD, 'english')
    per_million(FREQUENCY, corpus_tokens('JobAds'))
    log_ratio(FREQUENCY, corpus_tokens('A'), FREQUENCY_R, corpus_tokens('B'))
    matches(TERM, '^[a-z]+ [a-z]+$')
"""

from __future__ import annotations

import ast
import math
import operator
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd


class ExpressionError(ValueError):
    """Invalid or unsupported expression."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _series(value: Any, index: pd.Index) -> pd.Series:
    if isinstance(value, pd.Series):
        return value
    return pd.Series([value] * len(index), index=index)


def _num(value: Any):
    if isinstance(value, pd.Series):
        return pd.to_numeric(value, errors="coerce")
    return value


def _str(value: Any):
    if isinstance(value, pd.Series):
        return value.astype("string")
    return None if value is None else str(value)


def _apply_str(value: Any, fn: Callable[[str], Any]):
    if isinstance(value, pd.Series):
        return value.map(lambda v: None if v is None or (isinstance(v, float) and math.isnan(v)) else fn(str(v)))
    return None if value is None else fn(str(value))


@lru_cache(maxsize=16)
def _stoplist(language: str) -> frozenset[str]:
    path = Path(__file__).resolve().parent.parent / "data" / f"stoplist_{language.lower()}.tab"
    if not path.exists():
        raise ExpressionError(f"No bundled stoplist for language '{language}'.")
    return frozenset(line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


# ---------------------------------------------------------------------------
# Statistics (vectorized)
# ---------------------------------------------------------------------------


def log_likelihood(a, n1, b, n2):
    """Log-likelihood (G2) for frequency a in a corpus of n1 tokens vs b in n2 tokens (Rayson & Garside)."""
    a, n1, b, n2 = (np.asarray(_num(x), dtype=float) for x in (a, n1, b, n2))
    e1 = n1 * (a + b) / (n1 + n2)
    e2 = n2 * (a + b) / (n1 + n2)
    with np.errstate(divide="ignore", invalid="ignore"):
        t1 = np.where(a > 0, a * np.log(a / e1), 0.0)
        t2 = np.where(b > 0, b * np.log(b / e2), 0.0)
    return 2 * (t1 + t2)


def log_ratio(a, n1, b, n2):
    """Binary log of the ratio of relative frequencies, with 0.5 smoothing (Hardie 2014)."""
    a, n1, b, n2 = (np.asarray(_num(x), dtype=float) for x in (a, n1, b, n2))
    return np.log2(((a + 0.5) / n1) / ((b + 0.5) / n2))


def percent_diff(a, n1, b, n2):
    """%DIFF of normalized frequencies (Gabrielatos & Marchi 2012); b=0 uses a tiny normalized value."""
    a, n1, b, n2 = (np.asarray(_num(x), dtype=float) for x in (a, n1, b, n2))
    na, nb = a / n1 * 1e6, b / n2 * 1e6
    nb = np.where(nb == 0, 1e-18, nb)
    return (na - nb) * 100 / nb


def c_value(terms, freqs):
    """C-value termhood (Frantzi et al. 2000), using log2(length + 1) so single words are scored too.

    Terms nested in longer candidates are penalized by the mean frequency of those candidates.
    """
    if not isinstance(terms, pd.Series):
        raise ExpressionError("c_value() needs a column of terms.")
    words = [tuple(str(t).split()) for t in terms]
    freq = np.asarray(_num(freqs), dtype=float)
    index = {w: i for i, w in enumerate(words)}
    nested: dict[int, list[float]] = {}
    for i, w in enumerate(words):
        n = len(w)
        seen = set()
        for size in range(1, n):
            for start in range(0, n - size + 1):
                sub = w[start:start + size]
                j = index.get(sub)
                if j is not None and j not in seen:
                    seen.add(j)
                    nested.setdefault(j, []).append(freq[i])
    out = np.empty(len(words))
    for i, w in enumerate(words):
        weight = math.log2(len(w) + 1)
        longer = nested.get(i)
        out[i] = weight * (freq[i] - (sum(longer) / len(longer) if longer else 0.0))
    return pd.Series(out, index=terms.index)


# ---------------------------------------------------------------------------
# Function table
# ---------------------------------------------------------------------------


def _round(x, digits=0):
    x = _num(x)
    return x.round(int(digits)) if isinstance(x, pd.Series) else round(x, int(digits))


def _elementwise(fn):
    def wrapper(*args):
        args = [_num(a) for a in args]
        series = [a for a in args if isinstance(a, pd.Series)]
        if series:
            values = [a.to_numpy(dtype=float) if isinstance(a, pd.Series) else a for a in args]
            return pd.Series(fn(*values), index=series[0].index)
        return fn(*args)
    return wrapper


def _np_unary(fn):
    def wrapper(x):
        x = _num(x)
        with np.errstate(divide="ignore", invalid="ignore"):
            if isinstance(x, pd.Series):
                return pd.Series(fn(x.to_numpy(dtype=float)), index=x.index)
            return float(fn(float(x)))
    return wrapper


def _corpus_stat_of(context: "EvalContext", name: Any, key: str):
    """Corpus size for a name, or per row when given a column of corpus names."""
    if isinstance(name, pd.Series):
        sizes = {value: context.corpus_stat(str(value), key) for value in name.dropna().unique()}
        return name.map(sizes).astype(float)
    return context.corpus_stat(str(name), key)


def _make_functions(context: "EvalContext") -> dict[str, Callable[..., Any]]:
    frame = context.frame

    def col(name):
        if name not in frame.columns:
            raise ExpressionError(f"Unknown column '{name}'. Columns: {', '.join(map(str, frame.columns))}")
        return frame[name]

    def is_stopword(x, language=None):
        words = _stoplist(str(language or context.language))
        return _apply_str(x, lambda s: s.lower() in words)

    def has_stopword_edge(x, language=None):
        words = _stoplist(str(language or context.language))

        def check(s):
            parts = s.lower().split()
            return bool(parts) and (parts[0] in words or parts[-1] in words)

        return _apply_str(x, check)

    def matches(x, pattern):
        rx = re.compile(str(pattern))
        return _apply_str(x, lambda s: bool(rx.search(s)))

    def rank(x, ascending=False):
        return _num(x).rank(ascending=bool(ascending), method="min")

    def zscore(x):
        x = _num(x)
        std = x.std(ddof=0)
        return (x - x.mean()) / std if std else x * 0.0

    def coalesce(x, default):
        return x.fillna(default) if isinstance(x, pd.Series) else (default if x is None else x)

    def is_null(x):
        return x.isna() if isinstance(x, pd.Series) else x is None

    def concat(*parts):
        result = None
        for part in parts:
            text = _str(part)
            if isinstance(text, pd.Series):
                text = text.fillna("")
            result = text if result is None else result + text
        return result

    def if_(condition, a, b):
        cond = _series(condition, frame.index).astype(bool)
        return pd.Series(np.where(cond, _series(a, frame.index), _series(b, frame.index)), index=frame.index)

    return {
        "col": col,
        # strings
        "lower": lambda x: _apply_str(x, str.lower),
        "upper": lambda x: _apply_str(x, str.upper),
        "length": lambda x: _apply_str(x, len),
        "words": lambda x: _apply_str(x, lambda s: len(s.split())),
        "first_word": lambda x: _apply_str(x, lambda s: s.split()[0] if s.split() else ""),
        "last_word": lambda x: _apply_str(x, lambda s: s.split()[-1] if s.split() else ""),
        "contains": lambda x, s: _apply_str(x, lambda v: str(s).lower() in v.lower()),
        "startswith": lambda x, s: _apply_str(x, lambda v: v.lower().startswith(str(s).lower())),
        "endswith": lambda x, s: _apply_str(x, lambda v: v.lower().endswith(str(s).lower())),
        "matches": matches,
        "replace": lambda x, a, b: _apply_str(x, lambda v: v.replace(str(a), str(b))),
        "concat": concat,
        "is_stopword": is_stopword,
        "has_stopword_edge": has_stopword_edge,
        # math
        "abs": _np_unary(np.abs),
        "log": _np_unary(np.log),
        "log2": _np_unary(np.log2),
        "log10": _np_unary(np.log10),
        "sqrt": _np_unary(np.sqrt),
        "round": _round,
        "min": _elementwise(np.minimum),
        "max": _elementwise(np.maximum),
        "clip": lambda x, lo, hi: _num(x).clip(lo, hi) if isinstance(x, pd.Series) else min(max(x, lo), hi),
        "coalesce": coalesce,
        "is_null": is_null,
        "if_": if_,
        # column statistics
        "rank": rank,
        "zscore": zscore,
        "sum": lambda x: float(_num(x).sum()),
        "mean": lambda x: float(_num(x).mean()),
        "median": lambda x: float(_num(x).median()),
        "count": lambda: len(frame),
        # corpus and linguistic statistics
        "corpus_tokens": lambda name: _corpus_stat_of(context, name, "tokens"),
        "corpus_texts": lambda name: _corpus_stat_of(context, name, "texts"),
        "per_million": lambda freq, tokens: _num(freq) * 1_000_000 / _num(tokens),
        "log_likelihood": lambda a, n1, b, n2: pd.Series(log_likelihood(a, n1, b, n2), index=frame.index),
        "log_ratio": lambda a, n1, b, n2: pd.Series(log_ratio(a, n1, b, n2), index=frame.index),
        "percent_diff": lambda a, n1, b, n2: pd.Series(percent_diff(a, n1, b, n2), index=frame.index),
        "c_value": c_value,
    }


FUNCTION_DOCS = {
    "col(name)": "Column by name, for names that are not identifiers, e.g. col('N-GRAM'), col('%').",
    "lower(x) / upper(x)": "Change case.",
    "length(x)": "Number of characters.",
    "words(x)": "Number of space-separated words (n-gram length).",
    "first_word(x) / last_word(x)": "First / last word of a multi-word string.",
    "contains(x, s) / startswith(x, s) / endswith(x, s)": "Case-insensitive substring tests.",
    "matches(x, regex)": "Regular-expression search (use (?i) for case-insensitive).",
    "replace(x, a, b)": "Replace text.",
    "concat(a, b, ...)": "Join strings.",
    "is_stopword(x, language?)": "True if x is in the bundled stoplist (default: language of the result's corpus).",
    "has_stopword_edge(x, language?)": "True if the first or last word of x is a stopword.",
    "abs, log, log2, log10, sqrt, round(x, digits)": "Math functions.",
    "min(a, b) / max(a, b)": "Element-wise minimum / maximum.",
    "clip(x, lo, hi)": "Limit values to a range.",
    "coalesce(x, default) / is_null(x)": "Handle missing values (e.g. after a left join).",
    "if_(condition, a, b)": "a where condition is true, otherwise b.",
    "rank(x, ascending=False)": "Rank of each value (1 = highest by default).",
    "zscore(x)": "Standardized value within the column.",
    "sum(x) / mean(x) / median(x) / count()": "Column-level scalars.",
    "corpus_tokens(name) / corpus_texts(name)": "Size of a corpus in the workspace.",
    "per_million(freq, tokens)": "Normalized frequency per million tokens.",
    "log_likelihood(a, n1, b, n2)": "G2 keyness of frequency a (corpus size n1) vs b (size n2).",
    "log_ratio(a, n1, b, n2)": "Effect size: log2 of the ratio of relative frequencies (0.5 smoothing).",
    "percent_diff(a, n1, b, n2)": "%DIFF effect size.",
    "c_value(terms, freqs)": "C-value termhood of multi-word candidates (nesting-aware).",
}


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_CMPOPS = {
    ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le,
    ast.Gt: operator.gt, ast.GtE: operator.ge,
}
_CONSTANT_NAMES = {"True": True, "False": False, "None": None, "true": True, "false": False, "null": None}


class EvalContext:
    def __init__(self, frame: pd.DataFrame, corpus_stat: Callable[[str, str], float] | None = None,
                 language: str = "english"):
        self.language = language or "english"
        self.frame = frame
        self._corpus_stat = corpus_stat

    def corpus_stat(self, name: str, key: str) -> float:
        if self._corpus_stat is None:
            raise ExpressionError("Corpus statistics are not available here.")
        return self._corpus_stat(name, key)


def _bool(value: Any, index: pd.Index):
    if isinstance(value, pd.Series):
        return value.fillna(False).astype(bool)
    return _series(bool(value), index)


class _Evaluator:
    def __init__(self, context: EvalContext):
        self.context = context
        self.frame = context.frame
        self.functions = _make_functions(context)

    def eval(self, node: ast.AST):
        method = getattr(self, f"_{type(node).__name__}", None)
        if method is None:
            raise ExpressionError(f"Unsupported syntax: {type(node).__name__}")
        return method(node)

    def _Expression(self, node: ast.Expression):
        return self.eval(node.body)

    def _Constant(self, node: ast.Constant):
        if not isinstance(node.value, (str, int, float, bool, type(None))):
            raise ExpressionError("Unsupported constant.")
        return node.value

    def _Name(self, node: ast.Name):
        if node.id in self.frame.columns:
            return self.frame[node.id]
        if node.id in _CONSTANT_NAMES:
            return _CONSTANT_NAMES[node.id]
        columns = ", ".join(map(str, self.frame.columns))
        raise ExpressionError(f"Unknown column '{node.id}'. Columns: {columns}. Use col('...') for other names.")

    def _List(self, node: ast.List):
        return [self.eval(e) for e in node.elts]

    _Tuple = _List

    def _UnaryOp(self, node: ast.UnaryOp):
        value = self.eval(node.operand)
        if isinstance(node.op, ast.Not):
            return ~_bool(value, self.frame.index) if isinstance(value, pd.Series) else (not value)
        if isinstance(node.op, ast.USub):
            return -_num(value)
        if isinstance(node.op, ast.UAdd):
            return _num(value)
        raise ExpressionError("Unsupported unary operator.")

    def _BinOp(self, node: ast.BinOp):
        op = _BINOPS.get(type(node.op))
        if op is None:
            raise ExpressionError("Unsupported operator.")
        left, right = self.eval(node.left), self.eval(node.right)
        if isinstance(node.op, ast.Add) and (isinstance(left, str) or isinstance(right, str)):
            return op(_str(left), _str(right))
        with np.errstate(divide="ignore", invalid="ignore"):
            return op(_num(left), _num(right))

    def _BoolOp(self, node: ast.BoolOp):
        values = [_bool(self.eval(v), self.frame.index) for v in node.values]
        result = values[0]
        for value in values[1:]:
            result = (result & value) if isinstance(node.op, ast.And) else (result | value)
        return result

    def _Compare(self, node: ast.Compare):
        result = None
        left = self.eval(node.left)
        for op_node, comparator in zip(node.ops, node.comparators):
            right = self.eval(comparator)
            if isinstance(op_node, (ast.In, ast.NotIn)):
                if not isinstance(right, list):
                    raise ExpressionError("'in' needs a list, e.g. WORD in ['a', 'b'].")
                part = _series(left, self.frame.index).isin(right)
                if isinstance(op_node, ast.NotIn):
                    part = ~part
            else:
                op = _CMPOPS.get(type(op_node))
                if op is None:
                    raise ExpressionError("Unsupported comparison.")
                l_val, r_val = left, right
                if isinstance(l_val, pd.Series) and isinstance(r_val, (int, float)) and not isinstance(r_val, bool):
                    l_val = _num(l_val)
                if isinstance(r_val, pd.Series) and isinstance(l_val, (int, float)) and not isinstance(l_val, bool):
                    r_val = _num(r_val)
                part = op(l_val, r_val)
            part = _bool(part, self.frame.index)
            result = part if result is None else (result & part)
            left = right
        return result

    def _Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ExpressionError("Only direct function calls are allowed.")
        name = node.func.id
        if name == "if":
            name = "if_"
        fn = self.functions.get(name)
        if fn is None:
            raise ExpressionError(f"Unknown function '{name}'. Available: {', '.join(sorted(self.functions))}")
        args = [self.eval(a) for a in node.args]
        kwargs = {kw.arg: self.eval(kw.value) for kw in node.keywords if kw.arg}
        try:
            return fn(*args, **kwargs)
        except ExpressionError:
            raise
        except TypeError as exc:
            raise ExpressionError(f"Bad arguments for {name}(): {exc}") from exc


def evaluate(expression: str, frame: pd.DataFrame,
             corpus_stat: Callable[[str, str], float] | None = None, language: str = "english") -> Any:
    """Evaluates an expression over a DataFrame and returns a Series or a scalar."""
    if not isinstance(expression, str) or not expression.strip():
        raise ExpressionError("Expression must be a non-empty string.")
    if len(expression) > 2000:
        raise ExpressionError("Expression is too long (max 2000 characters).")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"Syntax error in expression: {exc.msg}") from exc
    return _Evaluator(EvalContext(frame, corpus_stat, language)).eval(tree)


def evaluate_mask(expression: str, frame: pd.DataFrame,
                  corpus_stat: Callable[[str, str], float] | None = None, language: str = "english") -> pd.Series:
    """Evaluates a boolean filter expression; scalars are broadcast."""
    value = evaluate(expression, frame, corpus_stat, language)
    return _bool(value, frame.index)


def evaluate_column(expression: str, frame: pd.DataFrame,
                    corpus_stat: Callable[[str, str], float] | None = None, language: str = "english") -> pd.Series:
    value = evaluate(expression, frame, corpus_stat, language)
    if isinstance(value, np.ndarray):
        value = pd.Series(value, index=frame.index)
    return _series(value, frame.index)
