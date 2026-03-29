# -*- coding: utf-8 -*-
"""Typed schemas for agent action inputs and outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class SchemaBase:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorkspaceRequest(SchemaBase):
    path: str | None = None


@dataclass
class WorkspaceResult(SchemaBase):
    workspace: str
    corpus_in_use: str | None


@dataclass
class CorpusInfo(SchemaBase):
    id: str
    name: str
    language: str
    encoding: str
    texts: int
    tokens: int
    types: int
    ttr: float


@dataclass
class CreateCorpusRequest(SchemaBase):
    name: str
    source: str
    language: str
    tagged: bool = False
    verbose: bool = False


@dataclass
class KeywordsRequest(SchemaBase):
    corpus_name: str | None = None
    measure: str = "log-likelihood"
    stoplist: list[str] | None = None
    ref_language: str | None = None
    ignore_numbers: bool = True
    ignore_strange: bool = True
    min_chars: int = 2
    limit: int | None = None


@dataclass
class KwicRequest(SchemaBase):
    node: str = ""
    corpus_name: str | None = None
    pos: str | list[str] | None = None
    case_sensitive: bool = False
    regexp: bool = False
    horizon: int = 10
    limit: int | None = None


@dataclass
class TabularResult(SchemaBase):
    rows: list[dict[str, Any]]
    total: int
    totals: dict[str, Any] | None = None


@dataclass
class CollgraphRequest(SchemaBase):
    node: str
    corpus_name: str | None = None
    pos: str | list[str] | None = None
    coll_pos: str | list[str] | None = None
    case_sensitive: bool = False
    regexp: bool = False
    left_span: int = 5
    right_span: int = 5
    measure: str = "mutual information"
    plot: bool = False


@dataclass
class DispersionRequest(SchemaBase):
    node: str
    corpus_name: str | None = None
    pos: str | list[str] | None = None
    case_sensitive: bool = False
    regexp: bool = False
    limit: int | None = None


@dataclass
class KeywordsDispersionRequest(SchemaBase):
    corpus_name: str | None = None
    lowercase: bool = True
    limit: int = 25
    keywords_measure: str = "log-likelihood"


@dataclass
class Text2Utf8Request(SchemaBase):
    source: str
    target: str
    source_encoding: str = "mbcs"
    verbose: bool = False


@dataclass
class Text2Utf8Result(SchemaBase):
    source: str
    target: str
    files: list[str]
    total: int


@dataclass
class ExportCorpusRequest(SchemaBase):
    dest_path: str
    corpus_name: str | None = None


@dataclass
class ImportCorpusRequest(SchemaBase):
    filename: str


@dataclass
class TrainModelRequest(SchemaBase):
    source: str
    language: str
    reflist: str | None = None
    stoplist: str | None = None
    verbose: bool = False


@dataclass
class TrainModelResult(SchemaBase):
    source: str
    language: str
    reflist: str | None
    stoplist: str | None


@dataclass
class SemanticSearchRequest(SchemaBase):
    query: str
    top_k: int = 5
    db_path: str | None = None
    model_name: str | None = None


@dataclass
class SemanticSearchResult(SchemaBase):
    db_path: str
    rows: list[dict[str, Any]]
    total: int
