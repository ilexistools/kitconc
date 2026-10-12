# -*- coding: utf-8 -*-
"""Server-side storage of analysis results.

Every analysis returns a ``result_id`` that points to the full table. Results are kept in a small
in-memory cache and written to ``<workspace>/.kitconc_results/<id>.json`` so they survive server
restarts and can be shared between sessions and jobs. The oldest files are pruned beyond
``disk_capacity``.
"""

from __future__ import annotations

import json
import math
import os
import secrets
import tempfile
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pandas as pd

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000
DEFAULT_MEMORY_CAPACITY = 32
DEFAULT_DISK_CAPACITY = 500
RESULTS_DIRNAME = ".kitconc_results"


class ToolFailure(Exception):
    """Error reported to the client as a structured JSON payload."""

    def __init__(self, code: str, message: str, hint: str | None = None, candidates: list[Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.candidates = candidates

    def payload(self) -> dict[str, Any]:
        error: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.hint:
            error["hint"] = self.hint
        if self.candidates:
            error["candidates"] = self.candidates
        return {"error": error}


def clean(value: Any) -> Any:
    """Converts numpy/pandas scalars, NaN and paths into JSON-friendly values."""
    if hasattr(value, "item") and not isinstance(value, (list, dict, str)):
        try:
            value = value.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    return value


@dataclass
class StoredResult:
    result_id: str
    analysis: str
    corpus: str | None
    params: dict[str, Any]
    frame: pd.DataFrame
    extra: dict[str, Any] = field(default_factory=dict)
    parents: list[str] = field(default_factory=list)
    created: float = field(default_factory=time.time)

    def summary(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "analysis": self.analysis,
            "corpus": self.corpus,
            "params": self.params,
            "parents": self.parents,
            "total": len(self.frame),
            "columns": [str(c) for c in self.frame.columns],
            "created": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.created)),
        }

    def to_json(self) -> dict[str, Any]:
        return clean({
            "meta": {
                "result_id": self.result_id, "analysis": self.analysis, "corpus": self.corpus,
                "params": self.params, "extra": self.extra, "parents": self.parents, "created": self.created,
            },
            "columns": [str(c) for c in self.frame.columns],
            "rows": self.frame.astype(object).where(self.frame.notna(), None).values.tolist(),
        })

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "StoredResult":
        meta = data["meta"]
        frame = pd.DataFrame(data.get("rows", []), columns=data.get("columns", []))
        return cls(meta["result_id"], meta["analysis"], meta.get("corpus"), meta.get("params", {}), frame,
                   meta.get("extra", {}), meta.get("parents", []), meta.get("created", time.time()))


class ResultStore:
    """Bounded memory cache backed by JSON files in the workspace."""

    def __init__(self, root: Callable[[], Path] | Path | None = None,
                 memory_capacity: int = DEFAULT_MEMORY_CAPACITY, disk_capacity: int = DEFAULT_DISK_CAPACITY):
        self._root = root
        self.memory_capacity = max(1, memory_capacity)
        self.disk_capacity = max(0, disk_capacity)
        self._items: OrderedDict[str, StoredResult] = OrderedDict()
        self._lock = threading.RLock()

    # -- storage location ----------------------------------------------------

    def root(self) -> Path | None:
        if self._root is None or self.disk_capacity == 0:
            return None
        path = Path(self._root() if callable(self._root) else self._root) / RESULTS_DIRNAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _path(self, result_id: str) -> Path | None:
        root = self.root()
        if root is None or not result_id.replace("-", "").isalnum():
            return None
        return root / f"{result_id}.json"

    # -- API -------------------------------------------------------------------

    def add(self, analysis: str, corpus: str | None, params: dict[str, Any], rows: list[dict] | pd.DataFrame,
            extra: dict[str, Any] | None = None, parents: list[str] | None = None) -> StoredResult:
        frame = rows.reset_index(drop=True) if isinstance(rows, pd.DataFrame) else pd.DataFrame.from_records(rows)
        clean_params = clean({k: v for k, v in (params or {}).items() if v is not None})
        item = StoredResult(f"r-{secrets.token_hex(4)}", analysis, corpus, clean_params, frame, extra or {},
                            parents or [])
        with self._lock:
            self._items[item.result_id] = item
            while len(self._items) > self.memory_capacity:
                self._items.popitem(last=False)
        self._write(item)
        return item

    def get(self, result_id: str) -> StoredResult:
        with self._lock:
            item = self._items.get(result_id)
            if item is not None:
                self._items.move_to_end(result_id)
                return item
        path = self._path(str(result_id))
        if path is not None and path.is_file():
            item = StoredResult.from_json(json.loads(path.read_text(encoding="utf-8")))
            with self._lock:
                self._items[result_id] = item
                while len(self._items) > self.memory_capacity:
                    self._items.popitem(last=False)
            return item
        raise ToolFailure(
            "RESULT_NOT_FOUND",
            f"Result not found: {result_id}",
            hint="Results are pruned when the store is full or the workspace changes; rerun the analysis.",
            candidates=[r["result_id"] for r in self.list(limit=10)],
        )

    def delete(self, result_id: str) -> bool:
        with self._lock:
            removed = self._items.pop(result_id, None) is not None
        path = self._path(result_id)
        if path is not None and path.is_file():
            path.unlink()
            removed = True
        return removed

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        summaries: dict[str, dict[str, Any]] = {}
        root = self.root()
        if root is not None:
            files = sorted(root.glob("r-*.json"), key=lambda p: p.stat().st_mtime_ns, reverse=True)[:limit]
            for path in files:
                try:
                    meta = json.loads(path.read_text(encoding="utf-8"))
                    item = StoredResult.from_json(meta)
                    summaries[item.result_id] = item.summary()
                except (OSError, ValueError, KeyError):
                    continue
        with self._lock:
            for item in self._items.values():
                summaries.setdefault(item.result_id, item.summary())
        ordered = sorted(summaries.values(), key=lambda s: s["created"], reverse=True)
        return ordered[:limit]

    # -- persistence -----------------------------------------------------------

    def _write(self, item: StoredResult) -> None:
        path = self._path(item.result_id)
        if path is None:
            return
        fd, tmp = tempfile.mkstemp(prefix=".tmp-", suffix=".json", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(item.to_json(), fh, ensure_ascii=False, default=str)
            os.replace(tmp, path)
        except Exception:
            Path(tmp).unlink(missing_ok=True)
            raise
        self._prune(path.parent)

    def _prune(self, root: Path) -> None:
        files = sorted(root.glob("r-*.json"), key=lambda p: p.stat().st_mtime_ns)
        for path in files[: max(0, len(files) - self.disk_capacity)]:
            try:
                path.unlink()
            except OSError:
                pass


def page(item: StoredResult, offset: int = 0, limit: int = DEFAULT_PAGE_SIZE, fmt: str = "table",
         fields: list[str] | None = None, sort_by: str | None = None, descending: bool = True) -> dict[str, Any]:
    """Returns one page of a stored result in the compact client format."""
    frame = item.frame
    if sort_by:
        if sort_by not in frame.columns:
            raise ToolFailure("INVALID_ARGUMENT", f"Unknown sort column: {sort_by}",
                              candidates=[str(c) for c in frame.columns])
        frame = frame.sort_values(sort_by, ascending=not descending, kind="mergesort")
    if fields:
        missing = [f for f in fields if f not in frame.columns]
        if missing:
            raise ToolFailure("INVALID_ARGUMENT", f"Unknown columns: {', '.join(missing)}",
                              candidates=[str(c) for c in frame.columns])
        frame = frame[fields]
    total = len(frame)
    offset = max(0, offset)
    limit = max(0, min(limit, MAX_PAGE_SIZE))
    window = frame.iloc[offset:offset + limit]
    end = offset + len(window)
    payload: dict[str, Any] = {
        "result_id": item.result_id,
        "analysis": item.analysis,
        "corpus": item.corpus,
        "total": total,
        "offset": offset,
        "returned": len(window),
        "next_offset": end if end < total else None,
        "columns": [str(c) for c in window.columns],
    }
    if fmt == "records":
        payload["rows"] = window.to_dict(orient="records")
    else:
        payload["rows"] = window.values.tolist()
    if item.extra:
        payload.update(item.extra)
    return clean(payload)
