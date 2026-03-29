# -*- coding: utf-8 -*-
"""Internal action layer designed for agent/tool orchestration."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import inspect
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any

from kitconc import kit_util, version
from kitconc.agent.schemas import (
    CollgraphRequest,
    CorpusInfo,
    CreateCorpusRequest,
    DispersionRequest,
    ExportCorpusRequest,
    ImportCorpusRequest,
    KeywordsRequest,
    KeywordsDispersionRequest,
    KwicRequest,
    TabularResult,
    Text2Utf8Request,
    Text2Utf8Result,
    TrainModelRequest,
    TrainModelResult,
    SemanticSearchRequest,
    SemanticSearchResult,
    WorkspaceRequest,
    WorkspaceResult,
)
from kitconc.core import Examples
from kitconc.export_corpus import export as export_zip
from kitconc.kit_corpus import Corpora, Corpus
from kitconc.kit_models import Models
from kitconc.kit_plots import CollGraph
from kitconc.kit_cmd import Kit
from kitconc.py_keywords import available_ref_languages

_CORPUS_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class ActionLayerError(Exception):
    """Base error for action layer failures."""


class ValidationError(ActionLayerError):
    """Input validation error."""


class NotFoundError(ActionLayerError):
    """Resource was not found."""


class StateError(ActionLayerError):
    """Action requires a state that is not currently set."""


def _normalize_workspace(path: str) -> str:
    workspace = Path(path).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    return str(workspace)


def _normalize_path(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def _read_info_tab(info_file: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not info_file.exists():
        return data
    with info_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = line.strip()
            if not row or "\t" not in row:
                continue
            key, value = row.split("\t", 1)
            data[key.replace(":", "").strip().lower()] = value.strip()
    return data


def _df_to_records(df, limit: int | None = None) -> list[dict[str, Any]]:
    if limit is not None and limit >= 0:
        df = df.head(limit)
    records = df.to_dict(orient="records")
    normalized: list[dict[str, Any]] = []
    for row in records:
        clean: dict[str, Any] = {}
        for key, value in row.items():
            if hasattr(value, "item"):
                clean[key] = value.item()
            else:
                clean[key] = value
        normalized.append(clean)
    return normalized


def _to_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class KitconcActions:
    """Thin wrapper exposing stable agent-friendly actions."""

    def __init__(self, workspace: str):
        self._workspace = _normalize_workspace(workspace)
        self.corpus_in_use: str | None = None

    @classmethod
    def from_workspace_file(cls, filename: str = "kitconc.tmp") -> "KitconcActions":
        path = Path(filename)
        if not path.exists():
            raise NotFoundError(f"Workspace file not found: {path}")
        workspace = path.read_text(encoding="utf-8").strip()
        if not workspace:
            raise ValidationError("Workspace file is empty.")
        return cls(workspace)

    def save_workspace_file(self, filename: str = "kitconc.tmp") -> str:
        Path(filename).write_text(self._workspace, encoding="utf-8")
        return self._workspace

    def set_workspace(self, workspace: str) -> str:
        self._workspace = _normalize_workspace(workspace)
        self.corpus_in_use = None
        return self._workspace

    def workspace(self, path: str | WorkspaceRequest | None = None) -> str:
        """Equivalent to CLI `workspace`: get/set current workspace."""
        if isinstance(path, WorkspaceRequest):
            path = path.path
        if path is None or path.strip() == "":
            return self._workspace
        return self.set_workspace(path)

    def workspace_typed(self, request: WorkspaceRequest) -> WorkspaceResult:
        self.workspace(request)
        state = self.workspace_status()
        return WorkspaceResult(
            workspace=state["workspace"],
            corpus_in_use=state["corpus_in_use"],
        )

    def workspace_status(self) -> dict[str, Any]:
        return {
            "workspace": self._workspace,
            "corpus_in_use": self.corpus_in_use,
        }

    def list_commands(self) -> list[str]:
        names: list[str] = []
        for item in sorted([f for f in dir(Kit) if callable(getattr(Kit, f))]):
            if item.startswith("do_"):
                names.append(item.replace("do_", ""))
        return names

    def tool_catalog(self) -> list[dict[str, Any]]:
        """Build a catalog of callable action-tools for orchestration layers."""
        ignore = {"tool_catalog", "mcp_tool_catalog"}
        catalog: list[dict[str, Any]] = []
        for name, fn in sorted(inspect.getmembers(self, predicate=callable), key=lambda x: x[0]):
            if name.startswith("_") or name in ignore:
                continue
            if name in {"exit", "quit", "clear", "cls", "clear_screen"}:
                # Keep terminal control/termination methods outside of tool surface.
                continue
            sig = inspect.signature(fn)
            params: list[dict[str, Any]] = []
            for param in sig.parameters.values():
                if param.name == "self":
                    continue
                annotation = "Any" if param.annotation is inspect._empty else str(param.annotation)
                default = None if param.default is inspect._empty else param.default
                required = param.default is inspect._empty
                params.append(
                    {
                        "name": param.name,
                        "annotation": annotation,
                        "required": required,
                        "default": default,
                    }
                )
            return_annotation = "Any" if sig.return_annotation is inspect._empty else str(sig.return_annotation)
            catalog.append(
                {
                    "name": name,
                    "params": params,
                    "returns": return_annotation,
                    "doc": (fn.__doc__ or "").strip(),
                }
            )
        return catalog

    def mcp_tool_catalog(self) -> list[dict[str, Any]]:
        """Return MCP-style tool descriptors derived from action signatures."""
        tools: list[dict[str, Any]] = []
        for item in self.tool_catalog():
            properties: dict[str, Any] = {}
            required: list[str] = []
            for p in item["params"]:
                properties[p["name"]] = {
                    "type": "string",
                    "description": p["annotation"],
                }
                if p["default"] is not None:
                    properties[p["name"]]["default"] = p["default"]
                if p["required"]:
                    required.append(p["name"])
            tools.append(
                {
                    "name": item["name"],
                    "description": item["doc"] or f"Execute action `{item['name']}`.",
                    "inputSchema": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                }
            )
        return tools

    def command_help(self, command: str | None = None) -> str:
        if command is None or command.strip() == "":
            cmds = self.list_commands()
            lines = [
                "Documented commands (type help <topic>):",
                "========================================",
            ]
            lines.extend([f"{i + 1}) {name}" for i, name in enumerate(cmds)])
            return "\n".join(lines)
        parser = Kit().get_parser(command.strip())
        if parser is None:
            raise NotFoundError(f"Unknown command: {command}")
        return parser.format_help()

    def help(self, command: str | None = None) -> str:
        return self.command_help(command)

    def app_version(self) -> str:
        return version.__version__

    def version(self) -> str:
        return self.app_version()

    def clear_screen(self) -> None:
        subprocess.run("cls" if os.name == "nt" else "clear", shell=True, check=False)

    def clear(self) -> None:
        self.clear_screen()

    def cls(self) -> None:
        self.clear_screen()

    # ------------------------------------------------------------
    # Workspace and corpus selection (ls/home/use/workspace/delete)
    # ------------------------------------------------------------

    def list_corpora(self) -> list[dict[str, Any]]:
        base = Path(self._workspace)
        items: list[dict[str, Any]] = []
        for child in sorted(base.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            info = _read_info_tab(child / "info.tab")
            if not info:
                continue
            items.append(
                {
                    "id": child.name,
                    "name": info.get("corpus name", child.name),
                    "language": info.get("language", ""),
                    "encoding": info.get("encoding", ""),
                    "texts": _to_int(info.get("textfiles", "0")),
                    "tokens": _to_int(info.get("tokens", "0")),
                    "types": _to_int(info.get("types", "0")),
                    "ttr": _to_float(info.get("type/token", "0")),
                }
            )
        return items

    def ls(self, corpus_name: str | None = None) -> dict[str, Any]:
        """Equivalent to CLI `ls`: corpora at root or files in selected corpus output."""
        target = corpus_name if corpus_name is not None else self.corpus_in_use
        if target is None:
            corpora = self.list_corpora()
            return {"mode": "corpora", "rows": corpora, "total": len(corpora)}
        files = self.list_output_files(target)
        return {"mode": "output_files", "corpus": target, "rows": files, "total": len(files)}

    def home(self) -> None:
        self.corpus_in_use = None

    def use(self, corpus_name: str) -> dict[str, Any]:
        if not self.corpus_exists(corpus_name):
            raise NotFoundError(f"Corpus not found: {corpus_name}")
        self.corpus_in_use = corpus_name
        return self.get_corpus_info(corpus_name)

    def corpus_exists(self, corpus_name: str) -> bool:
        return (Path(self._workspace) / corpus_name / "info.tab").exists()

    def get_corpus_info(self, corpus_name: str) -> dict[str, Any]:
        info_file = Path(self._workspace) / corpus_name / "info.tab"
        if not info_file.exists():
            raise NotFoundError(f"Corpus not found: {corpus_name}")
        data = _read_info_tab(info_file)
        return {
            "id": corpus_name,
            "name": data.get("corpus name", corpus_name),
            "language": data.get("language", ""),
            "encoding": data.get("encoding", ""),
            "texts": _to_int(data.get("textfiles", "0")),
            "tokens": _to_int(data.get("tokens", "0")),
            "types": _to_int(data.get("types", "0")),
            "ttr": _to_float(data.get("type/token", "0")),
        }

    def create_corpus(
        self,
        corpus_name: str,
        language: str,
        source_folder: str,
        tagged: bool = False,
        verbose: bool = False,
    ) -> dict[str, Any]:
        corpus_name = corpus_name.strip()
        language = language.strip().lower()
        source = _normalize_path(source_folder)

        if not corpus_name:
            raise ValidationError("Corpus name is required.")
        if _CORPUS_NAME_RE.fullmatch(corpus_name) is None:
            raise ValidationError("Invalid corpus name.")
        if not language:
            raise ValidationError("Language is required.")
        if not Path(source).exists() or not Path(source).is_dir():
            raise ValidationError(f"Source folder does not exist: {source}")
        if self.corpus_exists(corpus_name):
            raise ValidationError(f"Corpus already exists: {corpus_name}")

        corpus = Corpus(self._workspace, corpus_name, language)
        corpus.add_texts(source, tagged=tagged, verbose=verbose)
        return self.get_corpus_info(corpus_name)

    def create(
        self,
        name: str | CreateCorpusRequest,
        source: str | None = None,
        language: str | None = None,
        tagged: bool = False,
        verbose: bool = False,
    ) -> dict[str, Any]:
        if isinstance(name, CreateCorpusRequest):
            req = name
            return self.create_corpus(
                req.name,
                req.language,
                req.source,
                tagged=req.tagged,
                verbose=req.verbose,
            )
        if source is None or language is None:
            raise ValidationError("`source` and `language` are required.")
        return self.create_corpus(name, language, source, tagged=tagged, verbose=verbose)

    def create_typed(self, request: CreateCorpusRequest) -> CorpusInfo:
        created = self.create(request)
        return CorpusInfo(**created)

    def delete(self, corpus_name: str) -> None:
        self.delete_corpus(corpus_name)

    def delete_corpus(self, corpus_name: str) -> None:
        if not self.corpus_exists(corpus_name):
            raise NotFoundError(f"Corpus not found: {corpus_name}")
        shutil.rmtree(Path(self._workspace) / corpus_name)
        if self.corpus_in_use == corpus_name:
            self.corpus_in_use = None

    # ----------------------
    # Output folder actions
    # ----------------------

    def list_output_files(self, corpus_name: str | None = None) -> list[str]:
        selected = self._resolve_corpus_name(corpus_name)
        output_path = Path(self._workspace) / selected / "output"
        if not output_path.exists():
            return []
        return sorted([p.name for p in output_path.iterdir() if p.is_file()])

    def cleanse(self, corpus_name: str | None = None) -> list[str]:
        """Equivalent to CLI `cleanse`: delete all output files."""
        selected = self._resolve_corpus_name(corpus_name)
        output_path = Path(self._workspace) / selected / "output"
        if not output_path.exists():
            return []
        removed: list[str] = []
        for file in output_path.iterdir():
            if file.is_file():
                file.unlink()
                removed.append(file.name)
        return removed

    def open(self, filename: str, corpus_name: str | None = None, launch: bool = False) -> str:
        """Equivalent to CLI `open`: resolve output filename and optionally open with OS app."""
        selected = self._resolve_corpus_name(corpus_name)
        name = filename if filename.endswith(".xlsx") else f"{filename}.xlsx"
        path = Path(self._workspace) / selected / "output" / name
        if not path.exists():
            raise NotFoundError(f"Output file not found: {path}")
        if launch:
            self._launch_file(path)
        return str(path)

    # -----------------
    # Analysis actions
    # -----------------

    def list_ref_languages(self) -> list[str]:
        return available_ref_languages()

    def wordlist(
        self,
        corpus_name: str | None = None,
        lowercase: bool = True,
        limit: int | None = None,
    ) -> dict[str, Any]:
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        result = corpus.wordlist(lowercase=lowercase, verbose=False)
        records = _df_to_records(result.df, limit)
        return {"rows": records, "total": len(result.df)}

    def keywords(
        self,
        corpus_name: str | KeywordsRequest | None = None,
        measure: str = "log-likelihood",
        stoplist: list[str] | None = None,
        ref_language: str | None = None,
        ignore_numbers: bool = True,
        ignore_strange: bool = True,
        min_chars: int = 2,
        limit: int | None = None,
    ) -> dict[str, Any]:
        if isinstance(corpus_name, KeywordsRequest):
            req = corpus_name
            return self.keywords(
                corpus_name=req.corpus_name,
                measure=req.measure,
                stoplist=req.stoplist,
                ref_language=req.ref_language,
                ignore_numbers=req.ignore_numbers,
                ignore_strange=req.ignore_strange,
                min_chars=req.min_chars,
                limit=req.limit,
            )
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        result = corpus.keywords(
            measure=measure,
            stoplist=stoplist or [],
            ref_language=ref_language,
            ignore_numbers=ignore_numbers,
            ignore_strange=ignore_strange,
            min_chars=min_chars,
            verbose=False,
        )
        records = _df_to_records(result.df, limit)
        return {"rows": records, "total": len(result.df)}

    def keywords_typed(self, request: KeywordsRequest) -> TabularResult:
        data = self.keywords(request)
        return TabularResult(rows=data["rows"], total=data["total"])

    def kwic(
        self,
        node: str | KwicRequest,
        corpus_name: str | None = None,
        pos: str | list[str] | None = None,
        case_sensitive: bool = False,
        regexp: bool = False,
        horizon: int = 10,
        limit: int | None = None,
    ) -> dict[str, Any]:
        if isinstance(node, KwicRequest):
            req = node
            return self.kwic(
                node=req.node,
                corpus_name=req.corpus_name,
                pos=req.pos,
                case_sensitive=req.case_sensitive,
                regexp=req.regexp,
                horizon=req.horizon,
                limit=req.limit,
            )
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        result = corpus.kwic(
            node=node,
            pos=pos,
            case_sensitive=case_sensitive,
            regexp=regexp,
            horizon=horizon,
            limit=limit,
            verbose=False,
        )
        records = _df_to_records(result.df, limit=None)
        return {"rows": records, "total": len(result.df)}

    def kwic_typed(self, request: KwicRequest) -> TabularResult:
        data = self.kwic(request)
        return TabularResult(rows=data["rows"], total=data["total"])

    def concordance(
        self,
        node: str,
        corpus_name: str | None = None,
        pos: str | list[str] | None = None,
        case_sensitive: bool = False,
        regexp: bool = False,
        limit: int | None = None,
    ) -> dict[str, Any]:
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        result = corpus.concordance(
            node=node,
            pos=pos,
            case_sensitive=case_sensitive,
            regexp=regexp,
            limit=limit,
            verbose=False,
        )
        records = _df_to_records(result.df, limit=None)
        return {"rows": records, "total": len(result.df)}

    def collocates(
        self,
        node: str,
        corpus_name: str | None = None,
        pos: str | list[str] | None = None,
        coll_pos: str | list[str] | None = None,
        case_sensitive: bool = False,
        regexp: bool = False,
        left_span: int = 5,
        right_span: int = 5,
        lowercase: bool = True,
        measure: str = "mutual information",
        limit: int | None = None,
    ) -> dict[str, Any]:
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        result = corpus.collocates(
            node=node,
            pos=pos,
            coll_pos=coll_pos,
            case_sensitive=case_sensitive,
            regexp=regexp,
            left_span=left_span,
            right_span=right_span,
            lowercase=lowercase,
            measure=measure,
            limit=limit,
            verbose=False,
        )
        records = _df_to_records(result.df, limit=None)
        return {"rows": records, "total": len(result.df)}

    def collgraph(
        self,
        node: str | CollgraphRequest,
        corpus_name: str | None = None,
        pos: str | list[str] | None = None,
        coll_pos: str | list[str] | None = None,
        case_sensitive: bool = False,
        regexp: bool = False,
        left_span: int = 5,
        right_span: int = 5,
        measure: str = "mutual information",
        plot: bool = False,
    ) -> dict[str, Any]:
        if isinstance(node, CollgraphRequest):
            req = node
            return self.collgraph(
                node=req.node,
                corpus_name=req.corpus_name,
                pos=req.pos,
                coll_pos=req.coll_pos,
                case_sensitive=req.case_sensitive,
                regexp=req.regexp,
                left_span=req.left_span,
                right_span=req.right_span,
                measure=req.measure,
                plot=req.plot,
            )
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        coll = corpus.collocates(
            node=node,
            pos=pos,
            coll_pos=coll_pos,
            case_sensitive=case_sensitive,
            regexp=regexp,
            left_span=left_span,
            right_span=right_span,
            measure=measure,
            verbose=False,
        )
        if plot:
            graph = CollGraph(node=node)
            graph.plot_graphcoll(coll)
        records = _df_to_records(coll.df, limit=None)
        return {"rows": records, "total": len(coll.df)}

    def collgraph_typed(self, request: CollgraphRequest) -> TabularResult:
        data = self.collgraph(request)
        return TabularResult(rows=data["rows"], total=data["total"])

    def wtfreq(
        self,
        corpus_name: str | None = None,
        lowercase: bool = True,
        limit: int | None = None,
    ) -> dict[str, Any]:
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        result = corpus.wtfreq(lowercase=lowercase, verbose=False)
        records = _df_to_records(result.df, limit)
        return {"rows": records, "total": len(result.df)}

    def wfreqinfiles(
        self,
        corpus_name: str | None = None,
        lowercase: bool = True,
        limit: int | None = None,
    ) -> dict[str, Any]:
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        result = corpus.wfreqinfiles(lowercase=lowercase, verbose=False)
        records = _df_to_records(result.df, limit)
        return {"rows": records, "total": len(result.df)}

    def clusters(
        self,
        word: str,
        corpus_name: str | None = None,
        pos: str | list[str] | None = None,
        size: int = 3,
        minfreq: int = 1,
        minrange: int = 1,
        lowercase: bool = True,
        limit: int | None = None,
    ) -> dict[str, Any]:
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        result = corpus.clusters(
            word,
            pos=pos,
            size=size,
            minfreq=minfreq,
            minrange=minrange,
            lowercase=lowercase,
            verbose=False,
        )
        records = _df_to_records(result.df, limit)
        return {"rows": records, "total": len(result.df)}

    def ngrams(
        self,
        corpus_name: str | None = None,
        pos: str | list[str] | None = None,
        size: int = 3,
        minfreq: int = 1,
        minrange: int = 1,
        lowercase: bool = True,
        limit: int | None = None,
    ) -> dict[str, Any]:
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        result = corpus.ngrams(
            pos=pos,
            size=size,
            minfreq=minfreq,
            minrange=minrange,
            lowercase=lowercase,
            verbose=False,
        )
        records = _df_to_records(result.df, limit)
        return {"rows": records, "total": len(result.df)}

    def dispersion(
        self,
        node: str | DispersionRequest,
        corpus_name: str | None = None,
        pos: str | list[str] | None = None,
        case_sensitive: bool = False,
        regexp: bool = False,
        limit: int | None = None,
    ) -> dict[str, Any]:
        if isinstance(node, DispersionRequest):
            req = node
            return self.dispersion(
                node=req.node,
                corpus_name=req.corpus_name,
                pos=req.pos,
                case_sensitive=req.case_sensitive,
                regexp=req.regexp,
                limit=req.limit,
            )
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        result = corpus.dispersion(
            node=node,
            pos=pos,
            case_sensitive=case_sensitive,
            regexp=regexp,
            limit=limit,
            verbose=False,
        )
        records = _df_to_records(result.df, limit=None)
        return {
            "rows": records,
            "total": len(result.df),
            "totals": {
                "s1": result.total_s1,
                "s2": result.total_s2,
                "s3": result.total_s3,
                "s4": result.total_s4,
                "s5": result.total_s5,
            },
        }

    def dispersion_typed(self, request: DispersionRequest) -> TabularResult:
        data = self.dispersion(request)
        return TabularResult(rows=data["rows"], total=data["total"], totals=data.get("totals"))

    def keywords_dispersion(
        self,
        corpus_name: str | KeywordsDispersionRequest | None = None,
        lowercase: bool = True,
        limit: int = 25,
        keywords_measure: str = "log-likelihood",
    ) -> dict[str, Any]:
        if isinstance(corpus_name, KeywordsDispersionRequest):
            req = corpus_name
            return self.keywords_dispersion(
                corpus_name=req.corpus_name,
                lowercase=req.lowercase,
                limit=req.limit,
                keywords_measure=req.keywords_measure,
            )
        selected = self._resolve_corpus_name(corpus_name)
        corpus = self._open_corpus(selected)
        keywords = corpus.keywords(measure=keywords_measure, verbose=False)
        result = corpus.keywords_dispersion(
            keywords,
            lowercase=lowercase,
            limit=limit,
            verbose=False,
        )
        records = _df_to_records(result.df, limit=None)
        return {
            "rows": records,
            "total": len(result.df),
            "totals": {
                "s1": result.total_s1,
                "s2": result.total_s2,
                "s3": result.total_s3,
                "s4": result.total_s4,
                "s5": result.total_s5,
            },
        }

    def keywords_dispersion_typed(self, request: KeywordsDispersionRequest) -> TabularResult:
        data = self.keywords_dispersion(request)
        return TabularResult(rows=data["rows"], total=data["total"], totals=data.get("totals"))

    # --------------------------
    # Utility / data operations
    # --------------------------

    def text2utf8(
        self,
        source: str | Text2Utf8Request,
        target: str | None = None,
        source_encoding: str = "mbcs",
        verbose: bool = False,
    ) -> dict[str, Any]:
        if isinstance(source, Text2Utf8Request):
            req = source
            return self.text2utf8(
                source=req.source,
                target=req.target,
                source_encoding=req.source_encoding,
                verbose=req.verbose,
            )
        if target is None:
            raise ValidationError("`target` is required.")
        src = Path(_normalize_path(source))
        dst = Path(_normalize_path(target))
        if not src.exists() or not src.is_dir():
            raise ValidationError("Source path is not a valid folder.")
        dst.mkdir(parents=True, exist_ok=True)
        kit_util.files2utf8(str(src), str(dst), source_encoding, verbose)
        converted = sorted([p.name for p in dst.iterdir() if p.is_file()])
        return {"source": str(src), "target": str(dst), "files": converted, "total": len(converted)}

    def text2utf8_typed(self, request: Text2Utf8Request) -> Text2Utf8Result:
        data = self.text2utf8(request)
        return Text2Utf8Result(**data)

    def examples(self, dest_path: str | None = None) -> str:
        ex = Examples()
        if dest_path is None:
            ex.download()
            return str(Path.cwd())
        target = _normalize_path(dest_path)
        ex.download(dest_path=target)
        return target

    def semantic_search(
        self,
        query: str | SemanticSearchRequest,
        top_k: int | str = 5,
        db_path: str | None = None,
        model_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Semantic search over a sqlite-vec index.

        Notes
        -----
        - Expects an existing index file.
        - Default DB path: <workspace>/semantic_index.sqlite3
        """
        if isinstance(query, SemanticSearchRequest):
            req = query
            return self.semantic_search(
                query=req.query,
                top_k=req.top_k,
                db_path=req.db_path,
                model_name=req.model_name,
            )
        if not isinstance(query, str) or not query.strip():
            raise ValidationError("`query` must be a non-empty string.")
        try:
            k = int(top_k)
        except (TypeError, ValueError):
            raise ValidationError("`top_k` must be an integer.") from None
        if k < 1:
            raise ValidationError("`top_k` must be >= 1.")

        index_path = (
            _normalize_path(db_path)
            if db_path is not None
            else str(Path(self._workspace) / "semantic_index.sqlite3")
        )
        if not Path(index_path).exists():
            raise NotFoundError(f"Semantic index not found: {index_path}")

        try:
            from embeddings.sqlite_vec_search import SQLiteVecSearch
        except Exception as exc:
            raise ActionLayerError(
                "Embeddings runtime unavailable. Ensure dependencies are installed."
            ) from exc

        kwargs: dict[str, Any] = {}
        if model_name is not None and model_name.strip() != "":
            kwargs["model_name"] = model_name.strip()

        with SQLiteVecSearch(index_path, **kwargs) as index:
            rows = index.search(query.strip(), top_k=k)
        return {"db_path": index_path, "rows": rows, "total": len(rows)}

    def semantic_search_typed(self, request: SemanticSearchRequest) -> SemanticSearchResult:
        data = self.semantic_search(request)
        return SemanticSearchResult(**data)

    def export_corpus(self, dest_path: str | ExportCorpusRequest, corpus_name: str | None = None) -> str:
        if isinstance(dest_path, ExportCorpusRequest):
            req = dest_path
            return self.export_corpus(dest_path=req.dest_path, corpus_name=req.corpus_name)
        selected = self._resolve_corpus_name(corpus_name)
        dst = _normalize_path(dest_path)
        Path(dst).mkdir(parents=True, exist_ok=True)
        export_zip(self._workspace, selected, dst)
        return str(Path(dst) / f"{selected}.zip")

    def import_corpus(self, filename: str | ImportCorpusRequest) -> str:
        if isinstance(filename, ImportCorpusRequest):
            return self.import_corpus(filename.filename)
        filepath = _normalize_path(filename)
        if not Path(filepath).exists() or not Path(filepath).is_file():
            raise ValidationError(f"Invalid corpus file path: {filepath}")
        manager = Corpora(self._workspace)
        manager.import_corpus(filepath)
        return filepath

    def train_model(
        self,
        source: str | TrainModelRequest,
        language: str | None = None,
        reflist: str | None = None,
        stoplist: str | None = None,
        verbose: bool = False,
    ) -> dict[str, Any]:
        if isinstance(source, TrainModelRequest):
            req = source
            return self.train_model(
                source=req.source,
                language=req.language,
                reflist=req.reflist,
                stoplist=req.stoplist,
                verbose=req.verbose,
            )
        if language is None:
            raise ValidationError("`language` is required.")
        source_path = _normalize_path(source)
        if not Path(source_path).exists():
            raise ValidationError(f"Source path does not exist: {source_path}")
        reflist_path = _normalize_path(reflist) if reflist is not None else None
        stoplist_path = _normalize_path(stoplist) if stoplist is not None else None
        model = Models()
        model.nltk_create_model(
            source_path,
            language,
            reflist=reflist_path,
            stoplist=stoplist_path,
            verbose=verbose,
        )
        return {
            "source": source_path,
            "language": language,
            "reflist": reflist_path,
            "stoplist": stoplist_path,
        }

    def train_model_typed(self, request: TrainModelRequest) -> TrainModelResult:
        data = self.train_model(request)
        return TrainModelResult(**data)

    # -----------------
    # Command aliases
    # -----------------

    def quit(self) -> None:
        raise SystemExit

    def exit(self) -> None:
        raise SystemExit

    # -----------------
    # Internal helpers
    # -----------------

    def _resolve_corpus_name(self, corpus_name: str | None) -> str:
        if corpus_name is not None and corpus_name.strip() != "":
            selected = corpus_name.strip()
        elif self.corpus_in_use is not None:
            selected = self.corpus_in_use
        else:
            raise StateError("No corpus selected. Use `use(...)` or provide corpus_name.")
        if not self.corpus_exists(selected):
            raise NotFoundError(f"Corpus not found: {selected}")
        return selected

    def _open_corpus(self, corpus_name: str) -> Corpus:
        if not self.corpus_exists(corpus_name):
            raise NotFoundError(f"Corpus not found: {corpus_name}")
        return Corpus(self._workspace, corpus_name)

    def _launch_file(self, path: Path) -> None:
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
            return
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, str(path)])
