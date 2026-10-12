# -*- coding: utf-8 -*-
"""Progress reporting and cooperative cancellation for long-running tools.

Tools call :func:`report` at natural checkpoints (pipeline steps, enriched rows, files). The active
sink is thread-local: the MCP wrapper installs one that forwards progress notifications to the
client, and the job manager installs one that updates the job record and raises
:class:`Cancelled` when the job was cancelled. :func:`scope` maps a child's progress into a slice
of the parent's range, so nested work (a pipeline step that enriches rows) reports one smooth
overall percentage.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Callable, Iterator

Sink = Callable[[float, str], None]
_local = threading.local()


class Cancelled(Exception):
    """Raised inside a job when cancellation was requested."""


def _stack() -> list[tuple[float, float, str]]:
    if not hasattr(_local, "stack"):
        _local.stack = []
    return _local.stack


@contextmanager
def install(sink: Sink | None, cancel_event: threading.Event | None = None) -> Iterator[None]:
    """Installs a progress sink (fraction 0..1, message) for the current thread."""
    previous = (getattr(_local, "sink", None), getattr(_local, "cancel", None), list(_stack()))
    _local.sink, _local.cancel, _local.stack = sink, cancel_event, []
    try:
        yield
    finally:
        _local.sink, _local.cancel, _local.stack = previous


def check_cancelled() -> None:
    event = getattr(_local, "cancel", None)
    if event is not None and event.is_set():
        raise Cancelled("Cancelled by request.")


def report(done: float, total: float | None = None, message: str = "") -> None:
    """Reports progress of the innermost scope; also a cancellation checkpoint."""
    check_cancelled()
    sink = getattr(_local, "sink", None)
    if sink is None:
        return
    fraction = 0.0 if not total else max(0.0, min(1.0, done / total))
    labels = []
    for start, end, label in reversed(_stack()):
        fraction = start + (end - start) * fraction
        if label:
            labels.append(label)
    text = " / ".join(list(reversed(labels)) + ([message] if message else []))
    sink(fraction, text)


@contextmanager
def scope(index: int, count: int, label: str = "") -> Iterator[None]:
    """Maps progress reported inside the block to slice ``index`` of ``count`` of the parent."""
    stack = _stack()
    start, end = (index / count, (index + 1) / count) if count else (0.0, 1.0)
    stack.append((start, end, label))
    try:
        report(0, 1)
        yield
    finally:
        stack.pop()
