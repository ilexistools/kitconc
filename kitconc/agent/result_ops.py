# -*- coding: utf-8 -*-
"""Result algebra: tools that transform stored results into new stored results.

Every operation reads one or more ``result_id`` values, never modifies them, and stores its output
as a new result (with ``parents`` pointing back), so any chain of operations stays reproducible.
"""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

import pandas as pd
from pydantic import Field

from kitconc.agent import progress
from kitconc.agent.expressions import ExpressionError, evaluate_column, evaluate_mask
from kitconc.agent.results import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, ToolFailure

ResultIdArg = Annotated[str, Field(description="Id returned by an analysis or result tool.")]
LimitArg = Annotated[int, Field(ge=0, le=MAX_PAGE_SIZE, description="Rows to return in this page (the full result "
                                                                   "is stored).")]
FormatArg = Annotated[Literal["table", "records"], Field(
    description="'table' = compact {columns, rows: [[...]]}; 'records' = list of objects.")]

_AGG_RE = re.compile(r"^\s*(count|sum|mean|median|min|max|nunique|first|last|list)\s*\(\s*([^)]*?)\s*\)\s*$", re.I)

ENRICHMENTS = ("frequency", "dispersion", "example", "definition", "collocates")


def _expr_error(exc: ExpressionError, frame: pd.DataFrame) -> ToolFailure:
    return ToolFailure("INVALID_EXPRESSION", str(exc), hint="See guide_read('expressions').",
                       candidates=[str(c) for c in frame.columns])


class ResultOpsMixin:
    """Mixed into KitconcTools; relies on ``self.results``, ``self._save`` and ``self._corpus_stat``."""

    def result_create(
        self,
        columns: Annotated[list[str], Field(min_length=1, description="Column names.")],
        rows: Annotated[list[list[Any]], Field(description="Rows, each a list aligned with columns.")],
        name: Annotated[str, Field(description="Label stored as the result's analysis name.")] = "user_table",
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Store a small table you provide (seed terms, a custom stoplist, words to compare) so it can be
        joined, combined or enriched like any analysis result."""
        if any(len(row) != len(columns) for row in rows):
            raise ToolFailure("INVALID_ARGUMENT", "Every row must have one value per column.")
        frame = pd.DataFrame(rows, columns=columns)
        return self._save(name, None, {"rows": len(rows)}, frame, limit, format)

    def result_filter(
        self,
        result_id: ResultIdArg,
        where: Annotated[str | None, Field(description="Boolean expression, e.g. \"FREQUENCY >= 3 and not "
                                                       "is_stopword(WORD, 'english')\". See guide 'expressions'.")]
        = None,
        sort_by: Annotated[str | None, Field(description="Column to sort by.")] = None,
        descending: Annotated[bool, Field(description="Sort direction.")] = True,
        keep: Annotated[int | None, Field(ge=1, description="Keep only the first N rows after sorting.")] = None,
        fields: Annotated[list[str] | None, Field(description="Columns to keep, in this order.")] = None,
        rename: Annotated[dict[str, str] | None, Field(description="Rename columns, e.g. {'N-GRAM': 'TERM'}.")]
        = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Filter, sort, trim, select and rename columns of a stored result, producing a new result."""
        item = self.results.get(result_id)
        frame = item.frame
        if where:
            try:
                frame = frame[evaluate_mask(where, frame, self._corpus_stat, self._language_of(item))]
            except ExpressionError as exc:
                raise _expr_error(exc, frame) from exc
        if sort_by:
            if sort_by not in frame.columns:
                raise ToolFailure("INVALID_ARGUMENT", f"Unknown sort column: {sort_by}",
                                  candidates=[str(c) for c in frame.columns])
            frame = frame.sort_values(sort_by, ascending=not descending, kind="mergesort")
        if keep:
            frame = frame.head(keep)
        if fields:
            missing = [f for f in fields if f not in frame.columns]
            if missing:
                raise ToolFailure("INVALID_ARGUMENT", f"Unknown columns: {', '.join(missing)}",
                                  candidates=[str(c) for c in frame.columns])
            frame = frame[fields]
        if rename:
            frame = frame.rename(columns=rename)
        params = {"where": where, "sort_by": sort_by, "descending": descending if sort_by else None, "keep": keep,
                  "fields": fields, "rename": rename}
        return self._save("filter", item.corpus, params, frame, limit, format, parents=[item.result_id])

    def result_derive(
        self,
        result_id: ResultIdArg,
        columns: Annotated[dict[str, str], Field(min_length=1, description="New or replaced columns as "
                                                                           "{name: expression}, evaluated in order "
                                                                           "(later ones may use earlier ones).")],
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Add computed columns: normalized frequencies, keyness/effect sizes between joined columns, C-value,
        ranks, string features. Example: {"PM": "per_million(FREQUENCY, corpus_tokens('JobAds'))"}."""
        item = self.results.get(result_id)
        frame = item.frame.copy()
        for name, expression in columns.items():
            try:
                values = evaluate_column(expression, frame, self._corpus_stat, self._language_of(item))
                frame[name] = values.to_numpy()
            except ExpressionError as exc:
                raise _expr_error(exc, frame) from exc
        return self._save("derive", item.corpus, {"columns": columns}, frame, limit, format,
                          parents=[item.result_id])

    def result_join(
        self,
        left_id: Annotated[str, Field(description="Left result id (all its rows are kept with how='left').")],
        right_id: Annotated[str, Field(description="Right result id.")],
        on: Annotated[str | None, Field(description="Key column present in both results.")] = None,
        left_on: Annotated[str | None, Field(description="Key column in the left result.")] = None,
        right_on: Annotated[str | None, Field(description="Key column in the right result.")] = None,
        how: Annotated[Literal["left", "inner", "outer"], Field(description="Join type.")] = "left",
        right_fields: Annotated[list[str] | None, Field(description="Right columns to bring (default: all).")]
        = None,
        suffix: Annotated[str, Field(description="Suffix for right columns whose names clash with left ones.")]
        = "_R",
        ignore_case: Annotated[bool, Field(description="Compare keys case-insensitively.")] = True,
        fill_zero: Annotated[bool, Field(description="Fill missing numeric values from the right side with 0 "
                                                     "(useful for frequencies).")] = True,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Join two results by a key column, e.g. a wordlist of corpus A with a wordlist of corpus B, or
        term candidates with keywords. Clashing right columns get `suffix` (FREQUENCY -> FREQUENCY_R)."""
        left, right = self.results.get(left_id), self.results.get(right_id)
        lkey, rkey = left_on or on, right_on or on
        if not lkey or not rkey:
            raise ToolFailure("INVALID_ARGUMENT", "Give `on`, or both `left_on` and `right_on`.")
        for key, item in ((lkey, left), (rkey, right)):
            if key not in item.frame.columns:
                raise ToolFailure("INVALID_ARGUMENT", f"Column '{key}' not in result {item.result_id}.",
                                  candidates=[str(c) for c in item.frame.columns])
        rframe = right.frame
        if right_fields:
            missing = [f for f in right_fields if f not in rframe.columns]
            if missing:
                raise ToolFailure("INVALID_ARGUMENT", f"Unknown right columns: {', '.join(missing)}",
                                  candidates=[str(c) for c in rframe.columns])
            rframe = rframe[[rkey] + [f for f in right_fields if f != rkey]]
        lframe = left.frame.copy()
        rframe = rframe.copy()
        lframe["__key"] = lframe[lkey].astype(str).str.strip()
        rframe["__key"] = rframe[rkey].astype(str).str.strip()
        if ignore_case:
            lframe["__key"] = lframe["__key"].str.lower()
            rframe["__key"] = rframe["__key"].str.lower()
        rframe = rframe.drop_duplicates("__key")
        rframe = rframe.rename(columns={rkey: "__rkey"})
        rename = {c: f"{c}{suffix}" for c in rframe.columns if c in lframe.columns and c != "__key"}
        rframe = rframe.rename(columns=rename)
        right_numeric = [c for c in rframe.columns if c != "__key" and pd.api.types.is_numeric_dtype(rframe[c])]
        merged = lframe.merge(rframe, on="__key", how=how)
        if how == "outer":
            merged[lkey] = merged[lkey].fillna(merged["__rkey"])
        if rkey == lkey:
            merged = merged.drop(columns=["__rkey"])
        else:
            merged = merged.rename(columns={"__rkey": rkey if rkey not in merged.columns else f"{rkey}{suffix}"})
        if fill_zero:
            for c in right_numeric:
                merged[c] = merged[c].fillna(0)
            if how == "outer":
                for c in left.frame.columns:
                    if c in merged.columns and pd.api.types.is_numeric_dtype(left.frame[c]):
                        merged[c] = merged[c].fillna(0)
        merged = merged.drop(columns=["__key"])
        params = {"on": on, "left_on": left_on, "right_on": right_on, "how": how, "suffix": suffix,
                  "ignore_case": ignore_case}
        corpus = left.corpus if left.corpus == right.corpus else f"{left.corpus}+{right.corpus}"
        return self._save("join", corpus, params, merged, limit, format, parents=[left.result_id, right.result_id])

    def result_combine(
        self,
        result_ids: Annotated[list[str], Field(min_length=2, description="Results to combine; the first one is "
                                                                         "the base for intersect/difference.")],
        operation: Annotated[Literal["union", "intersect", "difference"], Field(
            description="union = all rows (deduplicated by key); intersect = rows of the first whose key is in "
                        "all others; difference = rows of the first whose key is in none of the others.")],
        key: Annotated[str, Field(description="Key column present in every result (e.g. WORD, TERM).")],
        ignore_case: Annotated[bool, Field(description="Compare keys case-insensitively.")] = True,
        source_column: Annotated[str | None, Field(description="For union: add a column identifying each row's "
                                                               "source (its label, or its result_id).")] = None,
        labels: Annotated[list[str] | None, Field(description="For union with source_column: one label per "
                                                              "result, e.g. the corpus names or node words.")]
        = None,
        label_from_param: Annotated[str | None, Field(description="For union with source_column: take each "
                                                                  "label from a parameter stored with the result, "
                                                                  "e.g. 'node' for collocates/KWIC results.")]
        = None,
        deduplicate: Annotated[bool, Field(description="For union: keep only the first row per key. Set false "
                                                       "to stack all rows (long format).")] = True,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Set operations between results by a key column, e.g. terms found in corpus A but not in B, or
        the union of candidates from several patterns. A labeled union without deduplication stacks
        results (e.g. collocates of several words) for result_aggregate."""
        if labels is not None and len(labels) != len(result_ids):
            raise ToolFailure("INVALID_ARGUMENT", "`labels` must have one entry per result id.")
        items = [self.results.get(r) for r in result_ids]
        for item in items:
            if key not in item.frame.columns:
                raise ToolFailure("INVALID_ARGUMENT", f"Column '{key}' not in result {item.result_id}.",
                                  candidates=[str(c) for c in item.frame.columns])

        def keys(frame):
            values = frame[key].astype(str).str.strip()
            return values.str.lower() if ignore_case else values

        if operation == "union":
            frames = []
            for i, item in enumerate(items):
                frame = item.frame.copy()
                if source_column:
                    if labels:
                        label = labels[i]
                    elif label_from_param:
                        label = item.params.get(label_from_param, item.result_id)
                    else:
                        label = item.result_id
                    frame[source_column] = label
                frames.append(frame)
            combined = pd.concat(frames, ignore_index=True, sort=False)
            if deduplicate:
                combined = combined[~keys(combined).duplicated()]
        else:
            base = items[0].frame
            others = [set(keys(item.frame)) for item in items[1:]]
            base_keys = keys(base)
            if operation == "intersect":
                mask = base_keys.map(lambda k: all(k in other for other in others))
            else:
                mask = base_keys.map(lambda k: not any(k in other for other in others))
            combined = base[mask.astype(bool)]
        corpora = {item.corpus for item in items}
        corpus = items[0].corpus if len(corpora) == 1 else "+".join(str(c) for c in corpora)
        return self._save(operation, corpus, {"key": key, "ignore_case": ignore_case}, combined, limit, format,
                          parents=[item.result_id for item in items])

    def result_aggregate(
        self,
        result_id: ResultIdArg,
        group_by: Annotated[list[str], Field(min_length=1, description="Columns to group by.")],
        aggregations: Annotated[dict[str, str], Field(
            min_length=1, description="{new_column: 'func(COLUMN)'} with func in count, sum, mean, median, min, "
                                      "max, nunique, first, last, list (first 10 distinct values in row order, "
                                      "joined by '; '). count() takes no column. Sort with result_filter first "
                                      "to control first/last/list.")],
        sort_by: Annotated[str | None, Field(description="Column to sort the groups by (descending).")] = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Group rows and aggregate, e.g. total frequency per FILENAME, per PATTERN or per head word."""
        item = self.results.get(result_id)
        frame = item.frame
        missing = [c for c in group_by if c not in frame.columns]
        if missing:
            raise ToolFailure("INVALID_ARGUMENT", f"Unknown group_by columns: {', '.join(missing)}",
                              candidates=[str(c) for c in frame.columns])
        grouped = frame.groupby(group_by, dropna=False, sort=False)
        out = grouped.size().rename("__size").to_frame()
        for name, spec in aggregations.items():
            match = _AGG_RE.match(spec or "")
            if not match:
                raise ToolFailure("INVALID_ARGUMENT", f"Bad aggregation '{spec}' for '{name}'.",
                                  hint="Use e.g. 'sum(FREQUENCY)', 'count()', 'list(FILENAME)'.")
            func, column = match.group(1).lower(), match.group(2)
            if func == "count":
                out[name] = out["__size"]
                continue
            if column not in frame.columns:
                raise ToolFailure("INVALID_ARGUMENT", f"Unknown column '{column}' in '{spec}'.",
                                  candidates=[str(c) for c in frame.columns])
            series = grouped[column]
            if func == "list":
                out[name] = series.agg(lambda s: "; ".join(pd.unique(pd.Series(s).astype(str))[:10]))
            elif func in ("sum", "mean", "median", "min", "max") and not pd.api.types.is_numeric_dtype(frame[column]):
                out[name] = pd.to_numeric(frame[column], errors="coerce").groupby(
                    [frame[c] for c in group_by], dropna=False, sort=False).agg(func)
            else:
                out[name] = series.agg(func)
        out = out.drop(columns=["__size"]).reset_index()
        if sort_by:
            if sort_by not in out.columns:
                raise ToolFailure("INVALID_ARGUMENT", f"Unknown sort column: {sort_by}",
                                  candidates=[str(c) for c in out.columns])
            out = out.sort_values(sort_by, ascending=False, kind="mergesort")
        return self._save("aggregate", item.corpus, {"group_by": group_by, "aggregations": aggregations}, out,
                          limit, format, parents=[item.result_id])

    def result_enrich(
        self,
        result_id: ResultIdArg,
        column: Annotated[str, Field(description="Column holding the word or term to look up (e.g. WORD, TERM).")],
        corpus: Annotated[str, Field(description="Corpus to look the terms up in.")],
        add: Annotated[list[Literal["frequency", "dispersion", "example", "definition", "collocates"]], Field(
            min_length=1,
            description="frequency: HITS; dispersion: RANGE, DP, JUILLAND_D; example: EXAMPLE, EXAMPLE_FILE "
                        "(a readable sentence); definition: DEFINITION, DEFINITION_FILE (definitional context, "
                        "if any); collocates: TOP_COLLOCATES (by log-dice, stopwords removed).")],
        max_rows: Annotated[int, Field(ge=1, le=2000, description="Enrich only the first N rows (each row runs "
                                                                  "searches; use job_start for large N).")] = 50,
        collocates_top: Annotated[int, Field(ge=1, le=20, description="Collocates per row.")] = 5,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Add per-row corpus evidence to a result: frequency, dispersion, an example sentence, a definitional
        context and top collocates of each word/term. Rows beyond max_rows are dropped."""
        item = self.results.get(result_id)
        corpus = self._require_corpus(corpus)
        if column not in item.frame.columns:
            raise ToolFailure("INVALID_ARGUMENT", f"Unknown column '{column}'.",
                              candidates=[str(c) for c in item.frame.columns])
        frame = item.frame.head(max_rows).copy()
        language = self.actions.get_corpus_info(corpus).get("language", "")
        new: dict[str, list[Any]] = {}
        terms = frame[column].astype(str).tolist()
        for i, term in enumerate(terms):
            progress.report(i, len(terms), f"enriching '{term}'")
            evidence = self._term_evidence(corpus, term, add, language, collocates_top)
            for name, value in evidence.items():
                new.setdefault(name, [None] * len(terms))[i] = value
        progress.report(len(terms), len(terms), "done")
        for name, values in new.items():
            frame[name] = values
        params = {"column": column, "corpus": corpus, "add": add, "max_rows": max_rows}
        return self._save("enrich", item.corpus, params, frame, limit, format, parents=[item.result_id])

    # -- helpers ---------------------------------------------------------------

    def _language_of(self, item) -> str:
        """Language of the result's corpus (first one for combined results), for stopword functions."""
        name = str(item.corpus or "").split("+")[0]
        if name and self.actions.corpus_exists(name):
            language = self.actions.get_corpus_info(name).get("language") or "english"
            return "english" if language == "no-tagging" else language
        return "english"

    def _term_evidence(self, corpus: str, term: str, add: list[str], language: str, top: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        term = term.strip()
        if not term:
            return out
        if "frequency" in add or "example" in add or "definition" in add:
            conc = self.actions.concordance(term, corpus_name=corpus)["rows"]
            if "frequency" in add:
                out["HITS"] = len(conc)
            if "example" in add:
                best = _best_example(conc)
                out["EXAMPLE"] = best.get("CONCORDANCE") if best else None
                out["EXAMPLE_FILE"] = best.get("FILENAME") if best else None
            if "definition" in add:
                hit = next(iter(self._definition_hits(term, conc, language, None)), None)
                out["DEFINITION"] = hit["SENTENCE"] if hit else None
                out["DEFINITION_FILE"] = hit["FILENAME"] if hit else None
        if "dispersion" in add:
            stats = self.actions.dispersion(term, corpus_name=corpus).get("stats") or {}
            out["RANGE"] = stats.get("range")
            out["DP"] = stats.get("dp")
            out["JUILLAND_D"] = stats.get("juilland-d")
        if "collocates" in add:
            try:
                rows = self.actions.collocates(term, corpus_name=corpus, measure="log-dice", min_freq=2,
                                               stoplist="default")["rows"]
            except Exception:  # noqa: BLE001 - collocates may fail for rare multi-word terms
                rows = []
            words = [str(r.get("WORD")) for r in rows[:top] if r.get("WORD")]
            out["TOP_COLLOCATES"] = ", ".join(words) if words else None
        return out


def _best_example(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Prefers sentences of 8-40 words that end like a sentence; falls back to the first hit."""
    if not rows:
        return None

    def score(row):
        text = str(row.get("CONCORDANCE", ""))
        n = len(text.split())
        good_length = 8 <= n <= 40
        ends = text.rstrip().endswith((".", "!", "?"))
        return (good_length, ends, -abs(n - 20))

    return max(rows, key=score)
