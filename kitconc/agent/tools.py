# -*- coding: utf-8 -*-
"""Curated MCP tool surface for Kitconc.

Wraps :class:`KitconcActions` with agent-oriented tools organized in layers:

- primitives: workspace, corpus and analysis tools (``workspace_*``, ``corpus_*``, ``analyze_*``,
  ``term_candidates``, ``context_mine``, ``text_stats``...);
- result algebra: ``result_*`` tools that page, filter, derive, join, combine, aggregate, enrich and
  export stored results (:mod:`kitconc.agent.result_ops`);
- composition: ``pipeline_run`` and ``recipe_*`` (:mod:`kitconc.agent.pipeline`,
  :mod:`kitconc.agent.recipes`);
- long-running work: ``job_*`` (:mod:`kitconc.agent.jobs`).

Every tool has described parameters, MCP annotations, explicit corpus selection and structured
errors. Handlers run in worker threads and forward progress notifications to the client.
"""

from __future__ import annotations

import inspect
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Callable, Literal

import anyio
import pandas as pd
from pydantic import Field

from kitconc.agent import progress
from kitconc.agent.actions import (
    ActionLayerError,
    KitconcActions,
    NotFoundError,
    StateError,
    ValidationError,
    _normalize_path,
)
from kitconc.agent.corpus_tools import CorpusToolsMixin
from kitconc.agent.expressions import FUNCTION_DOCS, ExpressionError
from kitconc.agent.jobs import JobManager, JobsMixin
from kitconc.agent.pipeline import PipelineMixin
from kitconc.agent.recipes import RecipesMixin
from kitconc.agent.result_ops import ResultOpsMixin
from kitconc.agent.results import (
    DEFAULT_DISK_CAPACITY,
    DEFAULT_MEMORY_CAPACITY,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    ResultStore,
    ToolFailure,
    clean,
    page,
)
from mcp.server.fastmcp import Context
from mcp.types import CallToolResult, TextContent, ToolAnnotations

DEFAULT_RESULT_CAPACITY = DEFAULT_MEMORY_CAPACITY
GUIDES_DIR = Path(__file__).resolve().parent / "guides"

SERVER_INSTRUCTIONS = """\
Kitconc is a corpus linguistics toolkit (wordlists, keywords, KWIC/concordances, collocates,
clusters, n-grams, dispersion, terminology, semantic search) over corpora stored in a workspace.

Mental model: workspace -> corpora -> analyses -> results -> result operations -> pipelines/recipes.
1. Call `workspace_info` first (corpus ids, sizes, reference languages). Every corpus-scoped tool
   takes an explicit `corpus`; there is no hidden "current corpus".
2. Analyses store the full table on the server and return a `result_id`, `columns`, `total` and one
   page of rows (default 50, compact {"columns", "rows": [[...]]}). Results persist on disk.
3. Build answers by composing results instead of asking for big pages:
   result_filter / result_derive (expressions: per_million, log_likelihood, log_ratio, c_value...) /
   result_join / result_combine / result_aggregate / result_enrich (examples, definitions,
   dispersion, collocates per row) / result_page / result_export.
4. For multi-step studies, `pipeline_run` wires tools together ($step.result_id, $params.x,
   foreach). `recipe_list` shows ready-made pipelines (corpus profile, word profile, corpus
   comparison, synonyms, keywords, glossary candidates, lexical bundles, collocation entries,
   corpus QA); adapt them freely (recipe_show -> edit -> pipeline_run / recipe_save).
5. Work that may take minutes (large corpora, enriching hundreds of rows, corpus_create, semantic
   indexing) should go through `job_start`; poll `job_status`.
6. POS tagsets vary by corpus (built-in Brown/Mac-Morpho taggers, spaCy Universal POS, pre-tagged
   texts). `corpus_tagset` shows raw tags and their coarse categories; raw tags go into `pos`
   arguments, categories (NOUN, ADJ, ADP...) into term_candidates patterns.
7. Errors are JSON {"error": {"code", "message", "hint", "candidates"}}; read them before retrying.
8. Guides: `guide_read` (overview, expressions, pipelines, recipes, measures, terminology) — also
   exposed as kitconc://guide/<name> resources.
Report results in the user's language; cite the measures and thresholds used.
"""


# ---------------------------------------------------------------------------
# Shared parameter types
# ---------------------------------------------------------------------------

CorpusArg = Annotated[str, Field(description="Corpus id, as listed by `workspace_info` / `corpus_list`.")]
LimitArg = Annotated[int, Field(ge=0, le=MAX_PAGE_SIZE,
                                description="Rows to return in this page (the full result is stored).")]
FormatArg = Annotated[Literal["table", "records"], Field(
    description="'table' = compact {columns, rows: [[...]]} (fewer tokens); 'records' = list of objects.")]
PosArg = Annotated[str | list[str] | None, Field(
    description="Restrict the node to raw POS tag(s) of this corpus (see corpus_tagset), e.g. 'NN' or "
                "['NN', 'NNS'] (Brown/Penn), 'NOUN' (spaCy), 'N' (Portuguese tagger).")]
WordListArg = Annotated[list[str] | str | None, Field(
    description="List of words, a path to a one-word-per-line file, or 'default' for the bundled list.")]
NodeArg = Annotated[str, Field(description="Search term. Plain word, wildcard pattern (with wildcards=true) "
                                           "or regular expression (with regexp=true).")]
CaseArg = Annotated[bool, Field(description="Match case exactly.")]
RegexpArg = Annotated[bool, Field(description="Treat the search term as a regular expression.")]
WildcardsArg = Annotated[bool, Field(description="Enable wildcards: teach*, *ing, a|b, [a,b].")]
LowercaseArg = Annotated[bool, Field(description="Fold words to lowercase before counting.")]
MinFreqArg = Annotated[int, Field(ge=1, description="Minimum frequency.")]
MinRangeArg = Annotated[int, Field(ge=1, description="Minimum number of texts the item must occur in.")]

CollocateMeasure = Literal["t-score", "mutual information", "mi", "mi2", "mi3", "log-likelihood",
                           "log-likelihood-2", "chi-square", "dice", "log-dice", "log-ratio", "z-score",
                           "ms", "mu"]
KeynessMeasure = Literal["log-likelihood", "log-likelihood-2", "chi-square", "chi-square-yates", "tf-idf",
                         "text-dispersion"]
EffectMeasure = Literal["log-ratio", "dice", "log-dice", "mi", "mi2", "mi3", "ms", "mu", "rrf", "drf",
                        "z-score", "t-score", "%diff", "odds-ratio"]

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
WRITES = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False,
                              openWorldHint=False)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


class KitconcTools(ResultOpsMixin, CorpusToolsMixin, PipelineMixin, RecipesMixin, JobsMixin):
    """Agent-oriented tool functions. Each public tool returns a JSON-serializable payload."""

    def __init__(self, actions: KitconcActions, result_capacity: int = DEFAULT_RESULT_CAPACITY,
                 disk_capacity: int = DEFAULT_DISK_CAPACITY, job_workers: int = 2):
        self.actions = actions
        self.results = ResultStore(lambda: Path(self.actions.workspace()), result_capacity, disk_capacity)
        self.jobs = JobManager(lambda: Path(self.actions.workspace()), job_workers)

    # -- helpers -----------------------------------------------------------

    def _corpus_ids(self) -> list[str]:
        return [c["id"] for c in self.actions.list_corpora()]

    def _require_corpus(self, corpus: str) -> str:
        corpus = (corpus or "").strip()
        if not corpus or not self.actions.corpus_exists(corpus):
            raise ToolFailure(
                "CORPUS_NOT_FOUND",
                f"Corpus not found: {corpus or '(empty)'}",
                hint="Use one of the candidate corpus ids, or create one with corpus_create.",
                candidates=self._corpus_ids(),
            )
        return corpus

    def _corpus_stat(self, corpus: str, key: str) -> float:
        info = self.actions.get_corpus_info(self._require_corpus(corpus))
        if key == "tokens" and not info.get("tokens"):
            self.actions.wordlist(corpus_name=corpus, limit=0)  # computes and records corpus size
            info = self.actions.get_corpus_info(corpus)
        return float(info.get(key) or 0)

    def _save(self, analysis: str, corpus: str | None, params: dict[str, Any], frame: pd.DataFrame | list,
              limit: int, fmt: str, extra: dict[str, Any] | None = None,
              parents: list[str] | None = None) -> dict[str, Any]:
        item = self.results.add(analysis, corpus, params, frame, extra, parents)
        return page(item, 0, limit, fmt)

    def _store(self, analysis: str, corpus: str | None, params: dict[str, Any], data: dict[str, Any],
               limit: int, fmt: str, extra_keys: tuple[str, ...] = ()) -> dict[str, Any]:
        extra = {k: data[k] for k in extra_keys if k in data}
        frame = pd.DataFrame.from_records(data.get("rows", []), columns=data.get("columns") or None)
        return self._save(analysis, corpus, params, frame, limit, fmt, extra=extra)

    def _failure(self, exc: Exception) -> ToolFailure:
        return _map_exception(exc, self)

    # -- workspace & corpora ------------------------------------------------

    def workspace_info(self) -> dict[str, Any]:
        """Start here. Returns the workspace path, Kitconc version, the corpora available (id, language,
        texts, tokens, types, ttr = type/token ratio as a percentage) and the bundled reference languages
        usable by analyze_keywords."""
        return {
            "workspace": self.actions.workspace(),
            "version": self.actions.app_version(),
            "corpora": self.actions.list_corpora(),
            "ref_languages": self.actions.list_ref_languages(),
        }

    def workspace_set(
        self,
        path: Annotated[str, Field(description="Absolute path of the workspace folder (created if missing).")],
    ) -> dict[str, Any]:
        """Switch the workspace folder that holds the corpora. Affects every later call on this server."""
        workspace = self.actions.workspace(path)
        return {"workspace": workspace, "corpora": self.actions.list_corpora()}

    def corpus_list(self) -> dict[str, Any]:
        """List corpora in the workspace with size statistics."""
        corpora = self.actions.list_corpora()
        return {"corpora": corpora, "total": len(corpora)}

    def corpus_info(self, corpus: CorpusArg) -> dict[str, Any]:
        """Metadata and size statistics of one corpus (language, texts, tokens, types, ttr = type/token
        ratio as a percentage), plus whether a semantic index exists."""
        corpus = self._require_corpus(corpus)
        info = self.actions.get_corpus_info(corpus)
        try:
            info["semantic_index"] = self.actions.semantic_index_status(corpus_name=corpus)
        except ActionLayerError:
            info["semantic_index"] = None
        return info

    def corpus_files(
        self,
        corpus: CorpusArg,
        offset: Annotated[int, Field(ge=0, description="First file to return.")] = 0,
        limit: Annotated[int, Field(ge=1, le=5000, description="Maximum number of file names.")] = 200,
    ) -> dict[str, Any]:
        """List the text file names of a corpus (use them with corpus_read_file)."""
        corpus = self._require_corpus(corpus)
        npy_dir = Path(self.actions.workspace()) / corpus / "data" / "npy"
        names = sorted(p.stem for p in npy_dir.glob("*.npy")) if npy_dir.is_dir() else []
        window = names[offset:offset + limit]
        end = offset + len(window)
        return {"corpus": corpus, "total": len(names), "offset": offset, "files": window,
                "next_offset": end if end < len(names) else None}

    def corpus_read_file(
        self,
        corpus: CorpusArg,
        filename: Annotated[str, Field(description="Text file name, as listed by corpus_files or the FILENAME "
                                                   "column of other results.")],
        node: Annotated[str | None, Field(description="Optional search term whose hits are marked [[like this]].")]
        = None,
        case_sensitive: CaseArg = False,
        regexp: RegexpArg = False,
        wildcards: WildcardsArg = False,
        start_line: Annotated[int, Field(ge=0, description="First sentence/line to return.")] = 0,
        max_lines: Annotated[int, Field(ge=1, le=5000, description="Maximum sentences/lines to return.")] = 200,
    ) -> dict[str, Any]:
        """Read one corpus text (one sentence per line), optionally marking the hits of a search term.
        Long texts are paginated by line."""
        corpus = self._require_corpus(corpus)
        view = self.actions.fileview(filename, corpus_name=corpus, node=node, case_sensitive=case_sensitive,
                                     regexp=regexp, wildcards=wildcards)
        lines = (view.get("text") or "").splitlines()
        window = lines[start_line:start_line + max_lines]
        end = start_line + len(window)
        return {
            "corpus": corpus,
            "filename": view.get("filename"),
            "tokens": view.get("tokens"),
            "types": view.get("types"),
            "hits": view.get("hits"),
            "total_lines": len(lines),
            "start_line": start_line,
            "next_line": end if end < len(lines) else None,
            "text": "\n".join(window),
        }

    def corpus_create(
        self,
        name: Annotated[str, Field(pattern=r"^[A-Za-z0-9_.-]+$",
                                   description="New corpus id (letters, digits, _ . -).")],
        source_folder: Annotated[str, Field(description="Folder with the source texts (.txt; PDFs are converted).")],
        language: Annotated[str, Field(description="Corpus language, e.g. 'english' or 'portuguese'.")],
        tagged: Annotated[bool, Field(description="Source texts are already POS-tagged (word_TAG).")] = False,
    ) -> dict[str, Any]:
        """Create (tokenize, tag and index) a new corpus from a folder of texts. May take minutes for large
        folders."""
        return self.actions.create_corpus(name, language, source_folder, tagged=tagged)

    def corpus_delete(
        self,
        corpus: CorpusArg,
        confirm: Annotated[bool, Field(description="Must be true. Confirm with the user before deleting.")] = False,
    ) -> dict[str, Any]:
        """Permanently delete a corpus and all its data from the workspace. Irreversible."""
        corpus = self._require_corpus(corpus)
        if not confirm:
            raise ToolFailure("CONFIRMATION_REQUIRED", f"Deleting corpus '{corpus}' is irreversible.",
                              hint="Ask the user, then call again with confirm=true.")
        self.actions.delete_corpus(corpus)
        return {"deleted": corpus}

    def corpus_import(
        self,
        zip_path: Annotated[str, Field(description="Path to a corpus .zip created by corpus_export.")],
    ) -> dict[str, Any]:
        """Import a corpus archive (.zip) into the workspace."""
        self.actions.import_corpus(zip_path)
        return {"imported": zip_path, "corpora": self.actions.list_corpora()}

    def corpus_export(
        self,
        corpus: CorpusArg,
        dest_folder: Annotated[str, Field(description="Folder where <corpus>.zip will be written.")],
    ) -> dict[str, Any]:
        """Export a corpus as a .zip archive that can be shared and re-imported with corpus_import."""
        corpus = self._require_corpus(corpus)
        return {"zip_path": self.actions.export_corpus(dest_folder, corpus_name=corpus)}

    # -- analyses -----------------------------------------------------------

    def analyze_wordlist(
        self,
        corpus: CorpusArg,
        search: Annotated[str | None, Field(description="Filter words: wildcard (teach*, *ing) or regex "
                                                        "(with regexp=true).")] = None,
        regexp: RegexpArg = False,
        lowercase: LowercaseArg = True,
        min_freq: MinFreqArg = 1,
        min_range: MinRangeArg = 1,
        stoplist: WordListArg = None,
        allowlist: WordListArg = None,
        dispersion: Annotated[bool, Field(description="Add RANGE, JUILLAND_D and DP columns.")] = False,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Word frequency list of a corpus, ordered by frequency. Use for an overview of the vocabulary or
        the frequency of specific words (via `search`)."""
        corpus = self._require_corpus(corpus)
        params = dict(search=search, regexp=regexp, lowercase=lowercase, min_freq=min_freq,
                      min_range=min_range, stoplist=stoplist, allowlist=allowlist, dispersion=dispersion)
        data = self.actions.wordlist(corpus_name=corpus, **params)
        return self._store("wordlist", corpus, params, data, limit, format)

    def analyze_keywords(
        self,
        corpus: CorpusArg,
        ref_corpus: Annotated[str | None, Field(description="Another corpus id to compare against. If omitted, "
                                                            "the bundled reference list of ref_language is used.")]
        = None,
        ref_language: Annotated[str | None, Field(description="Bundled reference list (see workspace_info."
                                                              "ref_languages). Defaults to the corpus language.")]
        = None,
        measure: Annotated[KeynessMeasure, Field(description="Keyness statistic. 'text-dispersion' needs "
                                                             "ref_corpus.")] = "log-likelihood",
        effect: Annotated[list[EffectMeasure] | None, Field(description="Effect-size columns to add, e.g. "
                                                                        "['log-ratio'].")] = None,
        polarity: Annotated[Literal["all", "positive", "negative"], Field(
            description="'positive' = overused in corpus, 'negative' = underused.")] = "all",
        p_value: Annotated[str | float | None, Field(description="Significance cut-off, e.g. 'p<0.05' or 0.01.")]
        = None,
        bonferroni: Annotated[bool, Field(description="Apply Bonferroni correction to p_value.")] = False,
        sort_by: Annotated[Literal["keyness", "effect"], Field(description="Sort by keyness or by the first "
                                                                           "effect measure.")] = "keyness",
        min_freq: MinFreqArg = 1,
        min_range: MinRangeArg = 1,
        min_chars: Annotated[int, Field(ge=1, description="Ignore words shorter than this.")] = 2,
        ignore_numbers: Annotated[bool, Field(description="Skip numeric tokens.")] = True,
        stoplist: Annotated[list[str] | None, Field(description="Words to exclude.")] = None,
        allowlist: WordListArg = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Keywords: words unusually frequent (or infrequent) in a corpus compared with a reference corpus or
        the bundled reference list. Use for aboutness, style and corpus comparison."""
        corpus = self._require_corpus(corpus)
        if ref_corpus is not None:
            ref_corpus = self._require_corpus(ref_corpus)
        params = dict(ref_corpus=ref_corpus, ref_language=ref_language, measure=measure, effect=effect,
                      polarity=polarity, p_value=p_value, bonferroni=bonferroni, sort_by=sort_by,
                      min_freq=min_freq, min_range=min_range, min_chars=min_chars,
                      ignore_numbers=ignore_numbers, stoplist=stoplist, allowlist=allowlist)
        data = self.actions.keywords(corpus_name=corpus, **params)
        return self._store("keywords", corpus, params, data, limit, format)

    def analyze_kwic(
        self,
        corpus: CorpusArg,
        node: NodeArg,
        pos: PosArg = None,
        case_sensitive: CaseArg = False,
        regexp: RegexpArg = False,
        wildcards: WildcardsArg = False,
        horizon: Annotated[int, Field(ge=1, le=50, description="Tokens shown on each side of the node.")] = 10,
        context: Annotated[list[str] | str | None, Field(description="Only lines with these word(s) near the "
                                                                     "node.")] = None,
        context_left: Annotated[int, Field(ge=0, description="Context window to the left.")] = 5,
        context_right: Annotated[int, Field(ge=0, description="Context window to the right.")] = 5,
        context_mode: Annotated[Literal["or", "and"], Field(description="Any or all context words.")] = "or",
        context_exclude: Annotated[bool, Field(description="Exclude (instead of require) context words.")]
        = False,
        sample: Annotated[int | None, Field(ge=1, description="Random sample of N lines (good for reading).")]
        = None,
        seed: Annotated[int | None, Field(description="Random seed for reproducible samples.")] = None,
        kpf: Annotated[list[str] | None, Field(description="Add KWIC pattern frequency for up to 3 positions, "
                                                           "e.g. ['R1', 'R2'] or ['L1'].")] = None,
        max_hits: Annotated[int | None, Field(ge=1, description="Stop after this many hits (for very frequent "
                                                                "nodes).")] = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Key Word In Context lines: each occurrence of a node with its left/right context and file. Use to
        read how a word is actually used; prefer `sample` for frequent words."""
        corpus = self._require_corpus(corpus)
        params = dict(node=node, pos=pos, case_sensitive=case_sensitive, regexp=regexp, wildcards=wildcards,
                      horizon=horizon, context=context, context_left=context_left, context_right=context_right,
                      context_mode=context_mode, context_exclude=context_exclude, sample=sample, seed=seed,
                      kpf=kpf)
        data = self.actions.kwic(corpus_name=corpus, limit=max_hits, **params)
        return self._store("kwic", corpus, {**params, "max_hits": max_hits}, data, limit, format)

    def analyze_concordance(
        self,
        corpus: CorpusArg,
        node: NodeArg,
        pos: PosArg = None,
        case_sensitive: CaseArg = False,
        regexp: RegexpArg = False,
        wildcards: WildcardsArg = False,
        sample: Annotated[int | None, Field(ge=1, description="Random sample of N lines.")] = None,
        seed: Annotated[int | None, Field(description="Random seed for reproducible samples.")] = None,
        max_hits: Annotated[int | None, Field(ge=1, description="Stop after this many hits.")] = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Sentence-level concordance: full sentences containing the node. Use when whole-sentence context
        matters more than aligned KWIC columns."""
        corpus = self._require_corpus(corpus)
        params = dict(node=node, pos=pos, case_sensitive=case_sensitive, regexp=regexp, wildcards=wildcards,
                      sample=sample, seed=seed)
        data = self.actions.concordance(corpus_name=corpus, limit=max_hits, **params)
        return self._store("concordance", corpus, {**params, "max_hits": max_hits}, data, limit, format)

    def analyze_collocates(
        self,
        corpus: CorpusArg,
        node: NodeArg,
        measure: Annotated[CollocateMeasure, Field(description="Association measure used for ranking.")]
        = "mutual information",
        extra_measures: Annotated[list[CollocateMeasure] | None, Field(description="Additional measure "
                                                                                   "columns.")] = None,
        left_span: Annotated[int, Field(ge=0, le=20, description="Window size to the left of the node.")] = 5,
        right_span: Annotated[int, Field(ge=0, le=20, description="Window size to the right of the node.")] = 5,
        min_freq: Annotated[int, Field(ge=1, description="Minimum co-occurrence frequency. Raise to 3-5 to "
                                                         "avoid rare-word noise with MI.")] = 1,
        pos: PosArg = None,
        coll_pos: Annotated[str | list[str] | None, Field(description="Restrict collocates to POS tag(s).")]
        = None,
        case_sensitive: CaseArg = False,
        regexp: RegexpArg = False,
        wildcards: WildcardsArg = False,
        lowercase: LowercaseArg = True,
        stoplist: WordListArg = None,
        allowlist: WordListArg = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Collocates: words that co-occur with the node within a window, ranked by an association measure.
        Use for meaning, phraseology and semantic prosody."""
        corpus = self._require_corpus(corpus)
        params = dict(node=node, measure=measure, extra_measures=extra_measures, left_span=left_span,
                      right_span=right_span, min_freq=min_freq, pos=pos, coll_pos=coll_pos,
                      case_sensitive=case_sensitive, regexp=regexp, wildcards=wildcards, lowercase=lowercase,
                      stoplist=stoplist, allowlist=allowlist)
        data = self.actions.collocates(corpus_name=corpus, **params)
        return self._store("collocates", corpus, params, data, limit, format)

    def analyze_clusters(
        self,
        corpus: CorpusArg,
        word: NodeArg,
        size: Annotated[int, Field(ge=2, le=10, description="Cluster length in tokens.")] = 3,
        position: Annotated[Literal["both", "left", "right"], Field(
            description="'left' = word starts the cluster, 'right' = word ends it, 'both' = anywhere.")] = "both",
        min_freq: MinFreqArg = 1,
        min_range: MinRangeArg = 1,
        pos: PosArg = None,
        case_sensitive: CaseArg = False,
        regexp: RegexpArg = False,
        wildcards: WildcardsArg = False,
        lowercase: LowercaseArg = True,
        stoplist: WordListArg = None,
        allowlist: WordListArg = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Clusters (lexical bundles) containing a given word, ranked by frequency."""
        corpus = self._require_corpus(corpus)
        params = dict(size=size, position=position, minfreq=min_freq, minrange=min_range, pos=pos,
                      case_sensitive=case_sensitive, regexp=regexp, wildcards=wildcards, lowercase=lowercase,
                      stoplist=stoplist, allowlist=allowlist)
        data = self.actions.clusters(word, corpus_name=corpus, **params)
        return self._store("clusters", corpus, {"word": word, **params}, data, limit, format)

    def analyze_ngrams(
        self,
        corpus: CorpusArg,
        size: Annotated[int, Field(ge=1, le=10, description="N-gram length in tokens.")] = 3,
        search: Annotated[str | None, Field(description="Only n-grams matching this pattern.")] = None,
        regexp: RegexpArg = False,
        min_freq: MinFreqArg = 1,
        min_range: MinRangeArg = 1,
        pos: Annotated[str | list[str] | None, Field(description="POS pattern filter (tagged corpora).")] = None,
        lowercase: LowercaseArg = True,
        stoplist: WordListArg = None,
        allowlist: WordListArg = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """All n-grams of a given size in the corpus, ranked by frequency. Use for recurrent phraseology
        not tied to a specific word (for word-specific bundles use analyze_clusters)."""
        corpus = self._require_corpus(corpus)
        params = dict(size=size, search=search, regexp=regexp, minfreq=min_freq, minrange=min_range, pos=pos,
                      lowercase=lowercase, stoplist=stoplist, allowlist=allowlist)
        data = self.actions.ngrams(corpus_name=corpus, **params)
        return self._store("ngrams", corpus, params, data, limit, format)

    def analyze_pframes(
        self,
        corpus: CorpusArg,
        size: Annotated[int, Field(ge=2, le=8, description="Frame length in tokens.")] = 4,
        slots: Annotated[int | list[int], Field(description="Number of open slots, or 1-based slot positions.")]
        = 1,
        min_freq: Annotated[int, Field(ge=1, description="Minimum frame frequency.")] = 2,
        min_range: MinRangeArg = 1,
        min_variants: Annotated[int, Field(ge=1, description="Minimum distinct slot fillers.")] = 2,
        pos: Annotated[str | None, Field(description="POS filter (tagged corpora).")] = None,
        lowercase: LowercaseArg = True,
        stoplist: WordListArg = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Phrase frames (p-frames): n-grams with open slots such as 'the * of the', with variant counts,
        TTR, entropy and top fillers."""
        corpus = self._require_corpus(corpus)
        params = dict(size=size, slots=slots, minfreq=min_freq, minrange=min_range, min_variants=min_variants,
                      pos=pos, lowercase=lowercase, stoplist=stoplist)
        data = self.actions.pframes(corpus_name=corpus, limit=None, **params)
        return self._store("pframes", corpus, params, data, limit, format)

    def analyze_lemmas(
        self,
        corpus: CorpusArg,
        lemma_file: Annotated[str | None, Field(description="Custom lemma list; defaults to the bundled list "
                                                            "for the corpus language.")] = None,
        lemma_format: Annotated[Literal["auto", "form-lemma", "headword-forms"], Field(
            description="Format of lemma_file.")] = "auto",
        min_freq: MinFreqArg = 1,
        min_range: MinRangeArg = 1,
        stoplist: WordListArg = None,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Frequency list of lemmas (headwords) with their word forms."""
        corpus = self._require_corpus(corpus)
        params = dict(lemma_file=lemma_file, lemma_format=lemma_format, min_freq=min_freq,
                      min_range=min_range, stoplist=stoplist)
        data = self.actions.lemmalist(corpus_name=corpus, limit=None, **params)
        return self._store("lemmas", corpus, params, data, limit, format)

    def analyze_dispersion(
        self,
        corpus: CorpusArg,
        node: NodeArg,
        pos: PosArg = None,
        case_sensitive: CaseArg = False,
        regexp: RegexpArg = False,
        wildcards: WildcardsArg = False,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """How a search term is spread across files (hits per file in 5 sections) plus corpus-level `stats`
        (range, Juilland's D, Gries' DP). Use to tell evenly used words from bursty ones."""
        corpus = self._require_corpus(corpus)
        params = dict(node=node, pos=pos, case_sensitive=case_sensitive, regexp=regexp, wildcards=wildcards)
        data = self.actions.dispersion(corpus_name=corpus, **params)
        return self._store("dispersion", corpus, params, data, limit, format, ("stats", "totals"))

    def analyze_dispersion_measures(
        self,
        corpus: CorpusArg,
        words: Annotated[list[str] | None, Field(description="Words to measure; all words if omitted.")] = None,
        min_freq: MinFreqArg = 1,
        lowercase: LowercaseArg = True,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Dispersion statistics per word (range, SD, CV, Juilland's D, Gries' DP) over the corpus files."""
        corpus = self._require_corpus(corpus)
        params = dict(words=words, min_freq=min_freq, lowercase=lowercase)
        data = self.actions.dispersion_measures(corpus_name=corpus, **params)
        return self._store("dispersion_measures", corpus, params, data, limit, format)

    def analyze_keywords_dispersion(
        self,
        corpus: CorpusArg,
        top_keywords: Annotated[int, Field(ge=1, le=500, description="Number of top keywords to plot across "
                                                                     "the corpus sections.")] = 25,
        keywords_measure: Annotated[KeynessMeasure, Field(description="Keyness statistic.")] = "log-likelihood",
        lowercase: LowercaseArg = True,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Distribution of the top keywords across 5 sections of the corpus."""
        corpus = self._require_corpus(corpus)
        params = dict(limit=top_keywords, keywords_measure=keywords_measure, lowercase=lowercase)
        data = self.actions.keywords_dispersion(corpus_name=corpus, **params)
        return self._store("keywords_dispersion", corpus, params, data, limit, format, ("totals",))

    def analyze_word_tag_freq(
        self,
        corpus: CorpusArg,
        lowercase: LowercaseArg = True,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Frequency of each word + POS tag pair."""
        corpus = self._require_corpus(corpus)
        data = self.actions.wtfreq(corpus_name=corpus, lowercase=lowercase)
        return self._store("word_tag_freq", corpus, {"lowercase": lowercase}, data, limit, format)

    def analyze_word_freq_by_file(
        self,
        corpus: CorpusArg,
        lowercase: LowercaseArg = True,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Frequency of each word in each text file."""
        corpus = self._require_corpus(corpus)
        data = self.actions.wfreqinfiles(corpus_name=corpus, lowercase=lowercase)
        return self._store("word_freq_by_file", corpus, {"lowercase": lowercase}, data, limit, format)

    def plot_wordcloud(
        self,
        corpus: CorpusArg,
        output_path: Annotated[str, Field(description="Destination .png file.")],
        source: Annotated[Literal["wordlist", "keywords"], Field(description="Words to draw.")] = "wordlist",
        max_words: Annotated[int, Field(ge=1, le=2000)] = 150,
        width: Annotated[int, Field(ge=100, le=8000)] = 1200,
        height: Annotated[int, Field(ge=100, le=8000)] = 800,
        colormap: Annotated[str, Field(description="Matplotlib colormap name.")] = "viridis",
    ) -> dict[str, Any]:
        """Save a word cloud PNG of the corpus wordlist or positive keywords."""
        corpus = self._require_corpus(corpus)
        return self.actions.wordcloud(output_path, corpus_name=corpus, source=source, max_words=max_words,
                                      width=width, height=height, colormap=colormap)

    # -- semantic -----------------------------------------------------------

    def semantic_index_status(self, corpus: CorpusArg) -> dict[str, Any]:
        """Whether a semantic (embedding) index exists for a corpus and how many chunks it holds."""
        corpus = self._require_corpus(corpus)
        return self.actions.semantic_index_status(corpus_name=corpus)

    def semantic_index_build(
        self,
        corpus: CorpusArg,
        source_folder: Annotated[str | None, Field(description="Folder with TXT/MD/RST/PDF sources; defaults "
                                                               "to the corpus source folder.")] = None,
        chunk_size: Annotated[int, Field(ge=50, le=5000, description="Characters per chunk.")] = 500,
        chunk_overlap: Annotated[int, Field(ge=0, le=1000, description="Overlap between chunks.")] = 50,
        rebuild: Annotated[bool, Field(description="Replace an existing index.")] = False,
    ) -> dict[str, Any]:
        """Build the semantic index of a corpus (needs the optional embeddings extra). Slow on large
        corpora."""
        corpus = self._require_corpus(corpus)
        return self.actions.index_corpus(corpus, source_folder=source_folder, chunk_size=chunk_size,
                                         chunk_overlap=chunk_overlap, rebuild=rebuild)

    def semantic_search(
        self,
        corpus: CorpusArg,
        query: Annotated[str, Field(min_length=1, description="Natural-language query.")],
        top_k: Annotated[int, Field(ge=1, le=200, description="Number of passages to retrieve.")] = 10,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        format: FormatArg = "records",
    ) -> dict[str, Any]:
        """Find passages semantically similar to a query (meaning, not exact words). Follow up with
        analyze_kwic to verify exact wording. Requires semantic_index_build first."""
        corpus = self._require_corpus(corpus)
        data = self.actions.semantic_search(query, top_k=top_k, corpus_name=corpus)
        return self._store("semantic_search", corpus, {"query": query, "top_k": top_k}, data, limit, format)

    # -- results ------------------------------------------------------------

    def result_list(
        self,
        limit: Annotated[int, Field(ge=1, le=500, description="Maximum number of results to list.")] = 50,
    ) -> dict[str, Any]:
        """List stored results (most recent first) with analysis, params, parents, columns and totals."""
        items = self.results.list(limit)
        return {"results": items, "total": len(items)}

    def result_page(
        self,
        result_id: Annotated[str, Field(description="Id returned by an analysis tool.")],
        offset: Annotated[int, Field(ge=0, description="First row to return.")] = 0,
        limit: LimitArg = DEFAULT_PAGE_SIZE,
        fields: Annotated[list[str] | None, Field(description="Subset of columns to return.")] = None,
        sort_by: Annotated[str | None, Field(description="Column to sort by before paging.")] = None,
        descending: Annotated[bool, Field(description="Sort direction for sort_by.")] = True,
        format: FormatArg = "table",
    ) -> dict[str, Any]:
        """Read another page of a stored result, optionally re-sorted or restricted to some columns. Does not
        recompute the analysis."""
        item = self.results.get(result_id)
        return page(item, offset, limit, format, fields=fields, sort_by=sort_by, descending=descending)

    def result_export(
        self,
        result_id: Annotated[str, Field(description="Id returned by an analysis tool.")],
        output_path: Annotated[str, Field(description="Destination file ending in .xlsx, .tsv or .tab.")],
        sheet_name: Annotated[str, Field(min_length=1, max_length=31, description="Worksheet name (.xlsx).")]
        = "Results",
    ) -> dict[str, Any]:
        """Save every row of a stored result to a spreadsheet or tab-separated file."""
        item = self.results.get(result_id)
        records = clean(item.frame.to_dict(orient="records"))
        return self.actions.export_analysis_result({"rows": records, "total": len(records)},
                                                   _normalize_path(output_path), sheet_name=sheet_name)

    def result_delete(
        self,
        result_id: Annotated[str, Field(description="Result to delete from the store.")],
    ) -> dict[str, Any]:
        """Delete a stored result (memory and disk). Results derived from it are kept."""
        return {"deleted": result_id, "existed": self.results.delete(result_id)}

    # -- guides ---------------------------------------------------------------

    def guide_read(
        self,
        topic: Annotated[str | None, Field(description="Guide name; omit to list the guides.")] = None,
    ) -> dict[str, Any]:
        """Read the built-in documentation: overview, expressions (functions for result_filter/derive),
        pipelines (JSON format), recipes, measures (which statistic to use) and terminology (glossary
        workflows). Same content as the kitconc://guide/<name> resources."""
        guides = list_guides()
        if topic is None:
            return {"guides": guides}
        path = GUIDES_DIR / f"{topic}.md"
        if topic not in {g["name"] for g in guides} or not path.is_file():
            raise ToolFailure("NOT_FOUND", f"Guide not found: {topic}", candidates=[g["name"] for g in guides])
        text = path.read_text(encoding="utf-8")
        if topic == "expressions":
            text += "\n\n## Function reference (generated)\n\n" + "\n".join(
                f"- `{sig}`: {doc}" for sig, doc in FUNCTION_DOCS.items())
        return {"topic": topic, "text": text}


def list_guides() -> list[dict[str, str]]:
    guides = []
    for path in sorted(GUIDES_DIR.glob("*.md")):
        first = next((line.lstrip("# ").strip() for line in path.read_text(encoding="utf-8").splitlines()
                      if line.strip()), path.stem)
        guides.append({"name": path.stem, "title": first})
    return guides


@dataclass(frozen=True)
class ToolSpec:
    name: str
    annotations: ToolAnnotations
    title: str
    group: str


_SPEC_ROWS: tuple[tuple[str, ToolAnnotations, str, str], ...] = (
    ("workspace_info", READ_ONLY, "Workspace overview", "workspace"),
    ("workspace_set", WRITES, "Switch workspace", "workspace"),
    ("guide_read", READ_ONLY, "Read a guide", "workspace"),
    ("corpus_list", READ_ONLY, "List corpora", "corpus"),
    ("corpus_info", READ_ONLY, "Corpus info", "corpus"),
    ("corpus_files", READ_ONLY, "List corpus files", "corpus"),
    ("corpus_read_file", READ_ONLY, "Read corpus file", "corpus"),
    ("corpus_tagset", READ_ONLY, "Corpus POS tagset", "corpus"),
    ("corpus_qa", READ_ONLY, "Corpus quality check", "corpus"),
    ("corpus_create", WRITES, "Create corpus", "corpus"),
    ("subcorpus_create", WRITES, "Create subcorpus", "corpus"),
    ("corpus_delete", DESTRUCTIVE, "Delete corpus", "corpus"),
    ("corpus_import", WRITES, "Import corpus", "corpus"),
    ("corpus_export", WRITES, "Export corpus", "corpus"),
    ("analyze_wordlist", READ_ONLY, "Wordlist", "analysis"),
    ("analyze_keywords", READ_ONLY, "Keywords", "analysis"),
    ("analyze_kwic", READ_ONLY, "KWIC concordance", "analysis"),
    ("analyze_concordance", READ_ONLY, "Sentence concordance", "analysis"),
    ("analyze_collocates", READ_ONLY, "Collocates", "analysis"),
    ("analyze_clusters", READ_ONLY, "Clusters", "analysis"),
    ("analyze_ngrams", READ_ONLY, "N-grams", "analysis"),
    ("analyze_pframes", READ_ONLY, "Phrase frames", "analysis"),
    ("analyze_lemmas", READ_ONLY, "Lemma list", "analysis"),
    ("analyze_dispersion", READ_ONLY, "Dispersion of a term", "analysis"),
    ("analyze_dispersion_measures", READ_ONLY, "Dispersion measures", "analysis"),
    ("analyze_keywords_dispersion", READ_ONLY, "Keywords dispersion", "analysis"),
    ("analyze_word_tag_freq", READ_ONLY, "Word/tag frequency", "analysis"),
    ("analyze_word_freq_by_file", READ_ONLY, "Word frequency by file", "analysis"),
    ("term_candidates", READ_ONLY, "Term candidates", "analysis"),
    ("context_mine", READ_ONLY, "Knowledge-rich contexts", "analysis"),
    ("text_stats", READ_ONLY, "Per-text statistics", "analysis"),
    ("plot_wordcloud", WRITES, "Word cloud", "analysis"),
    ("semantic_index_status", READ_ONLY, "Semantic index status", "semantic"),
    ("semantic_index_build", WRITES, "Build semantic index", "semantic"),
    ("semantic_search", READ_ONLY, "Semantic search", "semantic"),
    ("result_list", READ_ONLY, "List results", "results"),
    ("result_page", READ_ONLY, "Result page", "results"),
    ("result_create", READ_ONLY, "Create result from rows", "results"),
    ("result_filter", READ_ONLY, "Filter result", "results"),
    ("result_derive", READ_ONLY, "Add computed columns", "results"),
    ("result_join", READ_ONLY, "Join results", "results"),
    ("result_combine", READ_ONLY, "Combine results", "results"),
    ("result_aggregate", READ_ONLY, "Aggregate result", "results"),
    ("result_enrich", READ_ONLY, "Enrich result with corpus evidence", "results"),
    ("result_export", WRITES, "Export result", "results"),
    ("result_delete", DESTRUCTIVE, "Delete result", "results"),
    ("pipeline_validate", READ_ONLY, "Validate pipeline", "composition"),
    ("pipeline_run", WRITES, "Run pipeline", "composition"),
    ("recipe_list", READ_ONLY, "List recipes", "composition"),
    ("recipe_show", READ_ONLY, "Show recipe", "composition"),
    ("recipe_run", WRITES, "Run recipe", "composition"),
    ("recipe_save", WRITES, "Save recipe", "composition"),
    ("job_start", WRITES, "Start background job", "jobs"),
    ("job_status", READ_ONLY, "Job status", "jobs"),
    ("job_cancel", WRITES, "Cancel job", "jobs"),
)
TOOL_SPECS: tuple[ToolSpec, ...] = tuple(ToolSpec(*row) for row in _SPEC_ROWS)

# Tools that pipelines, recipes and jobs may call (no recursion into composition/job control, no
# destructive operations, no workspace switching).
PIPELINE_TOOLS: tuple[str, ...] = tuple(
    spec.name for spec in TOOL_SPECS
    if spec.group not in ("composition", "jobs") and not spec.annotations.destructiveHint
    and spec.name != "workspace_set"
)


def _map_exception(exc: Exception, tools: KitconcTools) -> ToolFailure:
    if isinstance(exc, ToolFailure):
        return exc
    message = str(exc) or exc.__class__.__name__
    if isinstance(exc, ExpressionError):
        return ToolFailure("INVALID_EXPRESSION", message, hint="See guide_read('expressions').")
    if isinstance(exc, NotFoundError):
        if message.startswith("Corpus not found"):
            return ToolFailure("CORPUS_NOT_FOUND", message, candidates=tools._corpus_ids())
        return ToolFailure("NOT_FOUND", message)
    if isinstance(exc, ValidationError):
        return ToolFailure("INVALID_ARGUMENT", message)
    if isinstance(exc, StateError):
        return ToolFailure("STATE_ERROR", message)
    if isinstance(exc, (ValueError, KeyError, TypeError)):
        return ToolFailure("INVALID_ARGUMENT", message,
                           hint="Check the parameter values against the tool schema.")
    if isinstance(exc, (FileNotFoundError, NotADirectoryError)):
        return ToolFailure("NOT_FOUND", message)
    if isinstance(exc, ImportError):
        return ToolFailure("DEPENDENCY_MISSING", message, hint="Install optional extras: uv sync --extra full")
    if isinstance(exc, progress.Cancelled):
        return ToolFailure("CANCELLED", message)
    return ToolFailure("ANALYSIS_FAILED", message)


def _text(payload: Any) -> str:
    return json.dumps(clean(payload), ensure_ascii=False, separators=(",", ":"), default=str)


def _ok(payload: Any) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=_text(payload))])


def _err(failure: ToolFailure) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=_text(failure.payload()))], isError=True)


def _wrap(tools: KitconcTools, name: str) -> Callable[..., Any]:
    """Builds an async MCP handler that runs the tool in a worker thread and forwards progress."""
    method = getattr(tools, name)
    signature = inspect.signature(method, eval_str=True)

    async def handler(ctx: Context, **kwargs: Any) -> CallToolResult:
        last = [0.0]

        def sink(fraction: float, message: str) -> None:
            now = time.monotonic()
            if now - last[0] < 0.25 and fraction < 1.0:
                return
            last[0] = now
            try:
                anyio.from_thread.run(ctx.report_progress, fraction * 100, 100.0, message or None)
            except Exception:  # noqa: BLE001 - progress is best effort
                pass

        def run() -> CallToolResult:
            try:
                with progress.install(sink):
                    return _ok(method(**kwargs))
            except SystemExit:
                raise
            except Exception as exc:  # noqa: BLE001 - every failure becomes a structured tool error
                return _err(_map_exception(exc, tools))

        return await anyio.to_thread.run_sync(run)

    params = [inspect.Parameter("ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Context)]
    params += list(signature.parameters.values())
    handler.__name__ = name
    handler.__doc__ = inspect.getdoc(method)
    handler.__signature__ = signature.replace(parameters=params, return_annotation=CallToolResult)
    handler.__annotations__ = {"ctx": Context, "return": CallToolResult}
    return handler


def register_tools(server, tools: KitconcTools, read_only: bool = False) -> list[str]:
    """Register the curated tools on a FastMCP server. Returns the registered tool names."""
    registered: list[str] = []
    for spec in TOOL_SPECS:
        if read_only and not spec.annotations.readOnlyHint:
            continue
        handler = _wrap(tools, spec.name)
        server.tool(name=spec.name, title=spec.title, description=handler.__doc__,
                    annotations=spec.annotations)(handler)
        registered.append(spec.name)
    return registered
