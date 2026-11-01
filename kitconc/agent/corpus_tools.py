# -*- coding: utf-8 -*-
"""Corpus-level tools that work directly on the indexed corpus data.

These complement the classic analyses with building blocks for terminology, quality control and
corpus design: tagset inspection, tagset-agnostic term candidates, context mining, per-text
statistics, corpus QA and subcorpora.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal

import numpy as np
import pandas as pd
from pydantic import Field

from kitconc import kit_util
from kitconc.agent import progress
from kitconc.agent.results import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, ToolFailure
from kitconc.agent.tagsets import (
    CATEGORIES,
    CATEGORY_DESCRIPTIONS,
    TERM_PATTERNS,
    build_mapping,
    default_pattern_set,
    parse_pattern,
)

CorpusArg = Annotated[str, Field(description="Corpus id, as listed by `workspace_info` / `corpus_list`.")]
LimitArg = Annotated[int, Field(ge=0, le=MAX_PAGE_SIZE, description="Rows to return in this page (the full result "
                                                                   "is stored).")]
FormatArg = Annotated[Literal["table", "records"], Field(
    description="'table' = compact {columns, rows: [[...]]}; 'records' = list of objects.")]
TagMapArg = Annotated[dict[str, str] | None, Field(
    description="Override the inferred category of raw tags, e.g. {'NE': 'PROPN', 'ADJ*': 'ADJ'} (globs allowed). "
                "Inspect tags with corpus_tagset first.")]

_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)
_MOJIBAKE_RE = re.compile("�|Ã[\u0080-¿]|â€")

DEFINITION_PATTERNS = {
    "english": [
        r"{term}\s+(is|are|was|were)\s+(a|an|the|any|one)\b",
        r"{term}\s+(refers? to|means|denotes|consists? of|is defined as|stands for)\b",
        r"\b(called|known as|termed|defined as|referred to as)\s+(a\s+|an\s+|the\s+)?{term}",
        r"{term}\s*,?\s*(i\s*\.\s*e\s*\.|that is|namely)",
        r"{term}\s*\(",
    ],
    "portuguese": [
        r"{term}\s+(é|são|era|eram)\s+(um|uma|o|a|os|as|uns|umas)\b",
        r"{term}\s+(significa|refere-se a|se refere a|consiste em|corresponde a|define-se como)\b",
        r"\b(chamad[oa]s?|conhecid[oa]s? como|denominad[oa]s?|definid[oa]s? como)\s+(de\s+)?{term}",
        r"{term}\s*,?\s*(ou seja|isto é|isto e)",
        r"{term}\s*\(",
    ],
}


@dataclass
class CorpusData:
    name: str
    path: Path
    language: str
    words: dict[int, str]
    tags: dict[int, str]
    files: list[tuple[str, Path]]

    def arrays(self):
        for filename, path in self.files:
            yield filename, np.load(path)


_cache: dict[tuple[str, str], tuple[float, CorpusData]] = {}
_cache_lock = threading.Lock()


def load_corpus_data(workspace: str, corpus: str, language: str) -> CorpusData:
    path = Path(workspace) / corpus
    idx = path / "data" / "idx"
    words_file = idx / "words.pickle"
    if not words_file.is_file():
        raise ToolFailure("NOT_FOUND", f"Corpus '{corpus}' has no index data.",
                          hint="Recreate the corpus with corpus_create.")
    mtime = words_file.stat().st_mtime
    key = (str(Path(workspace).resolve()), corpus)
    with _cache_lock:
        cached = _cache.get(key)
        if cached and cached[0] == mtime:
            return cached[1]
    words = kit_util.load(str(words_file), base_dir=str(path))
    tags_file = idx / "tags.pickle"
    tags = kit_util.load(str(tags_file), base_dir=str(path)) if tags_file.is_file() else {}
    npy_dir = path / "data" / "npy"
    files = sorted(((p.name[:-4], p) for p in npy_dir.glob("*.npy")), key=lambda x: x[0]) if npy_dir.is_dir() else []
    data = CorpusData(corpus, path, language, dict(words), dict(tags), files)
    with _cache_lock:
        _cache[key] = (mtime, data)
    return data


def _lookup(mapping: dict[int, Any], default: Any, size: int | None = None, dtype=object) -> np.ndarray:
    size = (max(mapping) + 1) if size is None and mapping else (size or 1)
    table = np.full(size, default, dtype=dtype)
    for key, value in mapping.items():
        if 0 <= int(key) < size:
            table[int(key)] = value
    return table


class CorpusToolsMixin:
    """Mixed into KitconcTools; relies on ``self.actions``, ``self._require_corpus`` and ``self._save``."""

    def _corpus_data(self, corpus: str) -> CorpusData:
        corpus = self._require_corpus(corpus)
        language = self.actions.get_corpus_info(corpus).get("language", "")
        return load_corpus_data(self.actions.workspace(), corpus, language)

    # -- tagset ------------------------------------------------------------------

    def corpus_tagset(
        self,
        corpus: CorpusArg,
        tag_map: TagMapArg = None,
        limit: LimitArg = 200,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Show the POS tags of a corpus with frequency, example words and the inferred coarse category
        (NOUN, ADJ, ADP...). Use it before term_candidates or POS-filtered searches; raw tags are what the
        `pos` arguments of analyze_* tools expect."""
        data = self._corpus_data(corpus)
        tag_counts: Counter = Counter()
        pair_counts: Counter = Counter()
        for i, (_, arr) in enumerate(data.arrays()):
            progress.report(i, len(data.files), "counting tags")
            pairs, counts = np.unique(arr[:, [1, 0]], axis=0, return_counts=True)
            for (tag_id, word_id), count in zip(pairs.tolist(), counts.tolist()):
                tag_counts[tag_id] += count
                pair_counts[(tag_id, word_id)] += count
        examples: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for (tag_id, word_id), count in pair_counts.items():
            examples[tag_id].append((count, word_id))
        raw = {tag_id: data.tags.get(tag_id, str(tag_id)) for tag_id in tag_counts}
        try:
            mapping = build_mapping(raw.values(), tag_map)
        except ValueError as exc:
            raise ToolFailure("INVALID_ARGUMENT", str(exc)) from exc
        rows = []
        for tag_id, count in tag_counts.most_common():
            top = sorted(examples[tag_id], reverse=True)[:5]
            rows.append({"TAG": raw[tag_id], "CATEGORY": mapping.category(raw[tag_id]), "FREQUENCY": count,
                         "EXAMPLES": ", ".join(data.words.get(w, "") for _, w in top)})
        frame = pd.DataFrame(rows, columns=["TAG", "CATEGORY", "FREQUENCY", "EXAMPLES"])
        extra = {"tagset_family": mapping.family,
                 "categories": {c: CATEGORY_DESCRIPTIONS[c] for c in CATEGORIES}}
        return self._save("tagset", data.name, {"tag_map": tag_map}, frame, limit, format, extra=extra)

    # -- terms -------------------------------------------------------------------

    def term_candidates(
        self,
        corpus: CorpusArg,
        mode: Annotated[Literal["auto", "pos", "stopwords"], Field(
            description="pos = token patterns over POS categories; stopwords = n-grams without stopwords at the "
                        "edges (works on untagged corpora); auto = pos when the corpus is tagged.")] = "auto",
        patterns: Annotated[list[str] | None, Field(
            description="Token patterns for mode=pos. Elements: a category (NOUN, PROPN, ADJ, VERB, ADV, ADP, DET, "
                        "PRON, NUM, CONJ, PART), tag:<raw tag or glob>, word:<literal word> or *; '|' for "
                        "alternatives. E.g. ['ADJ NOUN', 'NOUN word:of NOUN', 'ADJ|NOUN NOUN']. Default: a set "
                        "for the language word order.")] = None,
        pattern_set: Annotated[Literal["auto", "head-final", "head-initial"], Field(
            description="Default patterns: head-final (English: 'data analysis') or head-initial (Romance: "
                        "'análise de dados'). auto = by corpus language.")] = "auto",
        max_length: Annotated[int, Field(ge=1, le=6, description="Maximum words per candidate in stopwords mode.")]
        = 3,
        min_freq: Annotated[int, Field(ge=1, description="Minimum frequency.")] = 2,
        min_range: Annotated[int, Field(ge=1, description="Minimum number of texts.")] = 1,
        lowercase: Annotated[bool, Field(description="Merge case variants.")] = True,
        stopword_edges: Annotated[bool, Field(description="Drop candidates starting or ending with a stopword.")]
        = True,
        tag_map: TagMapArg = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Extract single- and multi-word term candidates (TERM, LENGTH, PATTERN, FREQUENCY, RANGE,
        PER_MILLION). Works with any tagset (Brown, Penn, Universal/spaCy, Mac-Morpho...) by mapping tags to
        coarse categories; falls back to stopword-bounded n-grams on untagged corpora. Combine with
        result_derive (c_value), result_join (keywords, reference corpora) and result_enrich (examples,
        definitions)."""
        data = self._corpus_data(corpus)
        stoplist = _stoplist(data.language)
        mapping = build_mapping(data.tags.values(), tag_map) if data.tags else build_mapping([])
        has_nouns = any(c in ("NOUN", "PROPN") for c in mapping.categories.values())
        if mode == "auto":
            mode = "pos" if mapping.family != "none" and has_nouns else "stopwords"
        if mode == "pos" and not has_nouns:
            raise ToolFailure("INVALID_ARGUMENT", "This corpus has no recognizable noun tags.",
                              hint="Use mode='stopwords', or pass tag_map after checking corpus_tagset.")
        size = max(data.words) + 1 if data.words else 1
        word_text = _lookup(data.words, "", size)
        lowered = np.array([str(w).lower() for w in word_text], dtype=object)
        valid = np.array([bool(_LETTER_RE.search(str(w))) and not any(ch.isdigit() for ch in str(w))
                          for w in word_text])
        is_stop = np.array([w in stoplist for w in lowered]) if stopword_edges else np.zeros(size, dtype=bool)

        if mode == "pos":
            chosen = patterns or TERM_PATTERNS[pattern_set if pattern_set != "auto"
                                               else default_pattern_set(data.language)]
            try:
                parsed = [(p, parse_pattern(p)) for p in chosen]
            except ValueError as exc:
                raise ToolFailure("INVALID_ARGUMENT", str(exc)) from exc
            tag_size = max(data.tags) + 1 if data.tags else 1
            tag_raw = _lookup(data.tags, "", tag_size)
            tag_cat = np.array([mapping.category(str(t)) for t in tag_raw], dtype=object)
            compiled = []
            for text, slots in parsed:
                slot_masks = []
                for slot in slots:
                    tag_ok = np.array([slot.matches("", str(tag_raw[i]), str(tag_cat[i])) for i in range(tag_size)])
                    word_ok = np.isin(lowered, list(slot.words)) if slot.words else np.zeros(size, dtype=bool)
                    literal = word_ok.copy()
                    slot_masks.append((tag_ok, word_ok, literal))
                compiled.append((text, slot_masks))
        else:
            compiled = [(f"{n}-gram", n) for n in range(1, max_length + 1)]

        counts: Counter = Counter()
        ranges: dict[str, set[str]] = defaultdict(set)
        pattern_of: dict[str, str] = {}
        total_tokens = 0
        for fi, (filename, arr) in enumerate(data.arrays()):
            progress.report(fi, len(data.files), f"scanning {filename}")
            w, t, s = arr[:, 0], arr[:, 1], arr[:, 2]
            total_tokens += len(w)
            seen: set[tuple[int, int]] = set()
            for text, spec in compiled:
                n = len(spec) if mode == "pos" else spec
                m = len(w) - n + 1
                if m <= 0:
                    continue
                mask = s[n - 1:] == s[:m]
                if mode == "pos":
                    for k, (tag_ok, word_ok, literal) in enumerate(spec):
                        wk, tk = w[k:k + m], t[k:k + m]
                        slot_hit = tag_ok[np.clip(tk, 0, len(tag_ok) - 1)] | word_ok[wk]
                        is_literal = literal[wk]
                        mask &= slot_hit & (valid[wk] | is_literal)
                else:
                    for k in range(n):
                        mask &= valid[w[k:k + m]]
                if stopword_edges:
                    mask &= ~is_stop[w[:m]] & ~is_stop[w[n - 1:n - 1 + m]]
                for start in np.nonzero(mask)[0].tolist():
                    if (start, n) in seen:
                        continue
                    seen.add((start, n))
                    ids = w[start:start + n]
                    term = " ".join((lowered if lowercase else word_text)[ids].tolist())
                    counts[term] += 1
                    ranges[term].add(filename)
                    pattern_of.setdefault(term, text)
        progress.report(1, 1, "ranking")
        rows = [
            {"TERM": term, "LENGTH": len(term.split()), "PATTERN": pattern_of[term], "FREQUENCY": freq,
             "RANGE": len(ranges[term]), "PER_MILLION": round(freq * 1_000_000 / max(total_tokens, 1), 2)}
            for term, freq in counts.items()
            if freq >= min_freq and len(ranges[term]) >= min_range
        ]
        frame = pd.DataFrame(rows, columns=["TERM", "LENGTH", "PATTERN", "FREQUENCY", "RANGE", "PER_MILLION"])
        frame = frame.sort_values(["FREQUENCY", "RANGE", "TERM"], ascending=[False, False, True], kind="mergesort")
        params = {"mode": mode, "patterns": [p for p, _ in compiled] if mode == "pos" else None,
                  "max_length": max_length if mode == "stopwords" else None, "min_freq": min_freq,
                  "min_range": min_range, "lowercase": lowercase, "stopword_edges": stopword_edges,
                  "tag_map": tag_map}
        extra = {"tagset_family": mapping.family, "corpus_tokens": total_tokens}
        return self._save("term_candidates", data.name, params, frame, limit, format, extra=extra)

    # -- contexts ----------------------------------------------------------------

    def context_mine(
        self,
        corpus: CorpusArg,
        term: Annotated[str, Field(min_length=1, description="Word or multi-word term to search.")],
        patterns: Annotated[list[str] | None, Field(
            description="Regular expressions applied to each sentence containing the term; '{term}' is replaced "
                        "by the term. Default: definitional patterns for the corpus language ('X is a', "
                        "'known as X', 'X refers to'...).")] = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Find knowledge-rich contexts of a term: definitions, explanations, synonyms or any regex pattern
        you supply (SENTENCE, FILENAME, PATTERN). Useful for glossary definitions and concept studies. The
        default patterns are heuristic: read the sentences before treating them as definitions."""
        corpus = self._require_corpus(corpus)
        language = self.actions.get_corpus_info(corpus).get("language", "")
        conc = self.actions.concordance(term, corpus_name=corpus)["rows"]
        try:
            hits = self._definition_hits(term, conc, language, patterns)
        except re.error as exc:
            raise ToolFailure("INVALID_ARGUMENT", f"Invalid regular expression: {exc}") from exc
        frame = pd.DataFrame(hits, columns=["SENTENCE", "FILENAME", "PATTERN"])
        extra = {"sentences_searched": len(conc)}
        return self._save("context_mine", corpus, {"term": term, "patterns": patterns}, frame, limit, format,
                          extra=extra)

    def _definition_hits(self, term: str, conc_rows: list[dict[str, Any]], language: str,
                         patterns: list[str] | None) -> list[dict[str, Any]]:
        templates = patterns or DEFINITION_PATTERNS.get((language or "").lower(), DEFINITION_PATTERNS["english"])
        term_rx = r"\s+".join(re.escape(part) for part in term.split())
        compiled = [(tpl, re.compile(tpl.replace("{term}", term_rx), re.IGNORECASE)) for tpl in templates]
        hits = []
        for row in conc_rows:
            sentence = str(row.get("CONCORDANCE", ""))
            for template, rx in compiled:
                if rx.search(sentence):
                    hits.append({"SENTENCE": sentence, "FILENAME": row.get("FILENAME"), "PATTERN": template})
                    break
        return hits

    # -- per-text statistics and QA ------------------------------------------------

    def text_stats(
        self,
        corpus: CorpusArg,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Per-text statistics: tokens, words, types, TTR (%), hapax, mean word and sentence length,
        non-word ratio and lexical density (tagged corpora). Use to find atypical texts or describe a
        corpus; filter/sort with result_filter."""
        data = self._corpus_data(corpus)
        frame = self._text_stats_frame(data).drop(columns=["_HASH", "_MOJIBAKE"], errors="ignore")
        return self._save("text_stats", data.name, {}, frame, limit, format)

    def _text_stats_frame(self, data: CorpusData) -> pd.DataFrame:
        size = max(data.words) + 1 if data.words else 1
        word_text = _lookup(data.words, "", size)
        lowered = np.array([str(w).lower() for w in word_text], dtype=object)
        has_letter = np.array([bool(_LETTER_RE.search(str(w))) for w in word_text])
        lengths = np.array([len(str(w)) for w in word_text])
        mapping = build_mapping(data.tags.values()) if data.tags else build_mapping([])
        tag_size = max(data.tags) + 1 if data.tags else 1
        content = np.array([mapping.category(str(t)) in ("NOUN", "PROPN", "ADJ", "VERB", "ADV")
                            for t in _lookup(data.tags, "", tag_size)])
        tagged = mapping.family != "none"
        rows = []
        for i, (filename, arr) in enumerate(data.arrays()):
            progress.report(i, len(data.files), f"measuring {filename}")
            w, t = arr[:, 0], arr[:, 1]
            words_mask = has_letter[w]
            word_ids = w[words_mask]
            n_words = int(words_mask.sum())
            counts = Counter(lowered[word_ids].tolist())
            sentences = len(np.unique(arr[:, 2]))
            rows.append({
                "FILENAME": filename,
                "TOKENS": int(len(w)),
                "WORDS": n_words,
                "TYPES": len(counts),
                "TTR": round(len(counts) * 100 / n_words, 2) if n_words else 0.0,
                "HAPAX": sum(1 for c in counts.values() if c == 1),
                "MEAN_WORD_LENGTH": round(float(lengths[word_ids].mean()), 2) if n_words else 0.0,
                "SENTENCES": sentences,
                "MEAN_SENTENCE_LENGTH": round(n_words / sentences, 2) if sentences else 0.0,
                "NON_WORD_RATIO": round(1 - n_words / len(w), 3) if len(w) else 1.0,
                "LEXICAL_DENSITY": (round(float(content[np.clip(t[words_mask], 0, tag_size - 1)].mean()) * 100, 2)
                                    if tagged and n_words else None),
                "_HASH": hashlib.sha1(w.tobytes()).hexdigest(),
                "_MOJIBAKE": sum(1 for wid in set(word_ids.tolist()) if _MOJIBAKE_RE.search(str(word_text[wid]))),
            })
        return pd.DataFrame(rows)

    def corpus_qa(
        self,
        corpus: CorpusArg,
        min_words: Annotated[int, Field(ge=1, description="Texts with fewer words are flagged as too short.")] = 20,
        outlier_factor: Annotated[float, Field(gt=1, description="Texts longer than this times the median are "
                                                                 "flagged.")] = 10.0,
    ) -> dict[str, Any]:
        """Quality check of a corpus: predominantly non-word content, duplicates, too short/long texts,
        garbled encoding, metadata mismatches and untagged data. The non_text check uses token content,
        not file extensions; readable TSV/CSV files may be classified as too_short. Returns issues with severity and a
        per-text statistics result (stats_result_id)."""
        data = self._corpus_data(corpus)
        info = self.actions.get_corpus_info(data.name)
        frame = self._text_stats_frame(data)
        issues: list[dict[str, Any]] = []

        def issue(severity, check, message, files=None):
            entry = {"severity": severity, "check": check, "message": message}
            if files:
                entry["files"] = files[:50]
                entry["count"] = len(files)
            issues.append(entry)

        if info.get("texts") != len(data.files):
            issue("warning", "metadata", f"info.tab lists {info.get('texts')} texts but the index has "
                                         f"{len(data.files)}.")
        if not frame.empty:
            garbage = frame[frame["NON_WORD_RATIO"] > 0.5]["FILENAME"].tolist()
            if garbage:
                issue("error", "non_text", "Texts where most tokens are not words (binary or garbled files?).",
                      garbage)
            short = frame[frame["WORDS"] < min_words]["FILENAME"].tolist()
            if short:
                issue("warning", "too_short", f"Texts with fewer than {min_words} words.", short)
            median = float(frame["TOKENS"].median())
            long = frame[frame["TOKENS"] > outlier_factor * max(median, 1)]["FILENAME"].tolist()
            if long:
                issue("warning", "too_long", f"Texts over {outlier_factor:g}x the median length ({median:g} tokens).",
                      long)
            duplicates = [group["FILENAME"].tolist() for _, group in frame.groupby("_HASH") if len(group) > 1]
            if duplicates:
                issue("warning", "duplicates", f"{len(duplicates)} groups of identical texts.",
                      [" = ".join(g) for g in duplicates])
            mojibake = frame[frame["_MOJIBAKE"] > 0]["FILENAME"].tolist()
            if mojibake:
                issue("warning", "encoding", "Words with replacement characters or mojibake (wrong encoding?).",
                      mojibake)
            if frame["LEXICAL_DENSITY"].isna().all():
                issue("info", "untagged", "The corpus has no POS tags; POS-based tools will fall back or fail.")
        source = Path(str(self._info_value(data.name, "source") or ""))
        if str(source) not in ("", ".") and source.is_dir():
            _, skipped = kit_util.list_source_files(str(source))
            binary = [s for s in skipped if s not in {".DS_Store", "desktop.ini", "Thumbs.db"}]
            if binary:
                issue("info", "source_binaries", "Binary files in the source folder were skipped on ingestion.",
                      binary)
        elif str(source) not in ("", "."):
            issue("info", "source_missing", f"Source folder not found: {source} (subcorpus_create needs it).")
        stats = self._save("text_stats", data.name, {}, frame.drop(columns=["_HASH", "_MOJIBAKE"]), 0, "table")
        severities = Counter(i["severity"] for i in issues)
        return {"corpus": data.name, "texts": len(data.files), "ok": severities.get("error", 0) == 0,
                "summary": dict(severities), "issues": issues, "stats_result_id": stats["result_id"]}

    def _info_value(self, corpus: str, key: str) -> str | None:
        info_file = Path(self.actions.workspace()) / corpus / "info.tab"
        if not info_file.is_file():
            return None
        return {k.lower(): v for k, v in kit_util.parse_info_tab(str(info_file))}.get(key.lower())

    # -- subcorpora ------------------------------------------------------------------

    def subcorpus_create(
        self,
        corpus: CorpusArg,
        name: Annotated[str, Field(pattern=r"^[A-Za-z0-9_.-]+$", description="Id of the new corpus.")],
        files: Annotated[list[str] | None, Field(description="Text file names to include (see corpus_files).")]
        = None,
        file_pattern: Annotated[str | None, Field(description="Regular expression on file names, e.g. '^2020_' "
                                                              "or 'news|blog'.")] = None,
        exclude: Annotated[bool, Field(description="Invert the selection (everything except the matches).")]
        = False,
        source_folder: Annotated[str | None, Field(description="Folder with the original texts, if it moved "
                                                               "since the corpus was created.")] = None,
    ) -> dict[str, Any]:
        """Create a new corpus from a selection of the texts of an existing one (by name list or regex), e.g.
        to compare periods, genres or authors with analyze_keywords(ref_corpus=...). Rebuilds from the
        original source files."""
        data = self._corpus_data(corpus)
        if not files and not file_pattern:
            raise ToolFailure("INVALID_ARGUMENT", "Give `files` or `file_pattern`.")
        available = [f for f, _ in data.files]
        try:
            rx = re.compile(file_pattern) if file_pattern else None
        except re.error as exc:
            raise ToolFailure("INVALID_ARGUMENT", f"Invalid file_pattern: {exc}") from exc
        wanted = set(files or [])
        selected = [f for f in available if (f in wanted) or (rx is not None and rx.search(f))]
        if exclude:
            selected = [f for f in available if f not in set(selected)]
        unknown = sorted(wanted - set(available))
        if unknown:
            raise ToolFailure("NOT_FOUND", f"Files not in corpus: {', '.join(unknown[:10])}",
                              candidates=available[:20])
        if not selected:
            raise ToolFailure("INVALID_ARGUMENT", "The selection is empty.", candidates=available[:20])
        source = Path(source_folder or self._info_value(data.name, "source") or "")
        if not source.is_dir():
            raise ToolFailure("NOT_FOUND", f"Source folder not found: {source}",
                              hint="Pass source_folder with the original texts.")
        accepted, _ = kit_util.list_source_files(str(source))
        by_corpus_name: dict[str, str] = {}
        for original in accepted:
            stem, ext = Path(original).stem, Path(original).suffix.lower()
            prepared = f"{stem}.txt" if ext in kit_util.SOURCE_CONVERTERS else original
            by_corpus_name.setdefault(prepared, original)
            by_corpus_name.setdefault(original + ".txt", original)
        missing = [f for f in selected if f not in by_corpus_name]
        if missing:
            raise ToolFailure("NOT_FOUND", f"{len(missing)} selected texts are missing from {source}.",
                              candidates=missing[:20])
        tmp = Path(tempfile.mkdtemp(prefix="kitconc-subcorpus-"))
        try:
            for i, filename in enumerate(selected):
                progress.report(i, len(selected) * 2, f"copying {filename}")
                shutil.copy2(source / by_corpus_name[filename], tmp / by_corpus_name[filename])
            progress.report(1, 2, "indexing")
            info = self.actions.create_corpus(name, data.language, str(tmp))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        info_file = Path(self.actions.workspace()) / name / "info.tab"
        pairs = [(k, str(source) if k.lower() == "source" else v) for k, v in kit_util.parse_info_tab(str(info_file))]
        pairs.append(("Parent corpus", data.name))
        kit_util.write_info_tab(str(info_file), pairs)
        return {"created": name, "parent": data.name, "texts": len(selected), "info": info}


def _stoplist(language: str) -> frozenset[str]:
    path = Path(kit_util.__file__).resolve().parent / "data" / f"stoplist_{(language or 'english').lower()}.tab"
    if not path.is_file():
        path = path.with_name("stoplist_english.tab")
    return frozenset(line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
