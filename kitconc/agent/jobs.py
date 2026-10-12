# -*- coding: utf-8 -*-
"""Background jobs for long-running work.

``job_start`` runs a tool, a pipeline or a recipe in a worker thread and returns immediately with a
``job_id``. Job records (status, progress, timings, output) are written to
``<workspace>/.kitconc_jobs/<job_id>.json``, so their status and output survive a server restart;
jobs that were running when the server stopped are reported as ``interrupted``. Cancellation is
cooperative: the job stops at the next progress checkpoint (between files, rows or steps).
"""

from __future__ import annotations

import json
import os
import secrets
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated, Any, Callable

from pydantic import Field

from kitconc.agent import progress
from kitconc.agent.pipeline import ParamsArg
from kitconc.agent.results import ToolFailure, clean

JOBS_DIRNAME = ".kitconc_jobs"
FINAL = {"succeeded", "failed", "cancelled", "interrupted"}


class JobManager:
    def __init__(self, root: Callable[[], Path], max_workers: int = 2):
        self._root = root
        self._executor = ThreadPoolExecutor(max_workers=max(1, max_workers), thread_name_prefix="kitconc-job")
        self._jobs: dict[str, dict[str, Any]] = {}
        self._events: dict[str, threading.Event] = {}
        self._lock = threading.RLock()

    def _dir(self) -> Path:
        path = Path(self._root()) / JOBS_DIRNAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _save(self, job: dict[str, Any]) -> None:
        path = self._dir() / f"{job['job_id']}.json"
        fd, tmp = tempfile.mkstemp(prefix=".tmp-", suffix=".json", dir=path.parent)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(clean(job), fh, ensure_ascii=False, default=str)
        os.replace(tmp, path)

    def start(self, kind: str, target: str, spec: dict[str, Any], run: Callable[[], Any]) -> dict[str, Any]:
        job_id = f"j-{secrets.token_hex(4)}"
        job = {"job_id": job_id, "kind": kind, "target": target, "spec": spec, "status": "queued",
               "progress": {"fraction": 0.0, "message": ""}, "created": time.time(), "started": None,
               "finished": None, "output": None, "error": None}
        event = threading.Event()
        with self._lock:
            self._jobs[job_id] = job
            self._events[job_id] = event
        self._save(job)
        self._executor.submit(self._execute, job_id, run, event)
        return self.status(job_id)

    def _execute(self, job_id: str, run: Callable[[], Any], event: threading.Event) -> None:
        job = self._jobs[job_id]
        last_write = [0.0]

        def sink(fraction: float, message: str) -> None:
            with self._lock:
                job["progress"] = {"fraction": round(fraction, 4), "message": message}
            now = time.time()
            if now - last_write[0] > 1.0:
                last_write[0] = now
                self._save(job)

        with self._lock:
            if event.is_set():
                job["status"] = "cancelled"
                job["finished"] = time.time()
                self._save(job)
                return
            job["status"] = "running"
            job["started"] = time.time()
        self._save(job)
        try:
            with progress.install(sink, event):
                output = run()
            with self._lock:
                job["status"] = "succeeded"
                job["output"] = output
                job["progress"] = {"fraction": 1.0, "message": "done"}
        except progress.Cancelled:
            with self._lock:
                job["status"] = "cancelled"
        except Exception as exc:  # noqa: BLE001 - recorded on the job
            failure = exc if isinstance(exc, ToolFailure) else ToolFailure("JOB_FAILED", str(exc) or type(exc).__name__)
            with self._lock:
                job["status"] = "failed"
                job["error"] = failure.payload()["error"]
        finally:
            with self._lock:
                job["finished"] = time.time()
            self._save(job)

    def _load(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            if job_id in self._jobs:
                return self._jobs[job_id]
        path = self._dir() / f"{job_id}.json"
        if not job_id.replace("-", "").isalnum() or not path.is_file():
            raise ToolFailure("JOB_NOT_FOUND", f"Job not found: {job_id}",
                              candidates=[j["job_id"] for j in self.list()[:10]])
        job = json.loads(path.read_text(encoding="utf-8"))
        if job.get("status") not in FINAL:
            job["status"] = "interrupted"
        return job

    def status(self, job_id: str, include_output: bool = False) -> dict[str, Any]:
        job = self._load(job_id)
        with self._lock:
            view = {k: v for k, v in job.items() if k not in ("output", "spec")}
            if job.get("started"):
                view["elapsed_seconds"] = round((job.get("finished") or time.time()) - job["started"], 1)
            output = job.get("output")
            if isinstance(output, dict):
                view["result_ids"] = output.get("result_ids") or (
                    {"output": output["result_id"]} if "result_id" in output else None)
            if include_output:
                view["output"] = output
        for key in ("created", "started", "finished"):
            if view.get(key):
                view[key] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(view[key]))
        return clean(view)

    def list(self) -> list[dict[str, Any]]:
        ids = {p.stem for p in self._dir().glob("j-*.json")}
        with self._lock:
            ids |= set(self._jobs)
        jobs = []
        for job_id in ids:
            try:
                jobs.append(self.status(job_id))
            except (ToolFailure, OSError, ValueError):
                continue
        return sorted(jobs, key=lambda j: j.get("created") or "", reverse=True)

    def cancel(self, job_id: str) -> dict[str, Any]:
        job = self._load(job_id)
        with self._lock:
            event = self._events.get(job_id)
            if job.get("status") in FINAL:
                return self.status(job_id)
            if event is not None:
                event.set()
                job["progress"]["message"] = "cancellation requested"
        return self.status(job_id)


class JobsMixin:
    """Mixed into KitconcTools; relies on ``self.jobs`` (JobManager) and the tool methods."""

    def job_start(
        self,
        tool: Annotated[str | None, Field(description="Run a single tool, e.g. 'result_enrich' or "
                                                      "'corpus_create'.")] = None,
        args: Annotated[dict[str, Any] | None, Field(description="Arguments for `tool`.")] = None,
        pipeline: Annotated[dict[str, Any] | None, Field(description="Run a pipeline (same JSON as "
                                                                     "pipeline_run).")] = None,
        recipe: Annotated[str | None, Field(description="Run a recipe by name.")] = None,
        params: ParamsArg = None,
    ) -> dict[str, Any]:
        """Start long work in the background (give exactly one of tool, pipeline or recipe) and return a
        job_id immediately. Poll with job_status; results are stored like any other result."""
        chosen = [x for x in (tool, pipeline, recipe) if x]
        if len(chosen) != 1:
            raise ToolFailure("INVALID_ARGUMENT", "Give exactly one of `tool`, `pipeline` or `recipe`.")
        if tool:
            if tool not in self._pipeline_tools():
                raise ToolFailure("INVALID_ARGUMENT", f"Tool '{tool}' cannot run as a job.",
                                  candidates=sorted(self._pipeline_tools()))
            call_args = dict(args or {})
            return self.jobs.start("tool", tool, {"args": call_args}, lambda: self._invoke(tool, call_args))
        if pipeline:
            from kitconc.agent.pipeline import validate_spec

            errors = validate_spec(pipeline, self._pipeline_tools(), params)
            if errors:
                raise ToolFailure("INVALID_PIPELINE", errors[0], candidates=errors)
            return self.jobs.start("pipeline", "pipeline", {"pipeline": pipeline, "params": params},
                                   lambda: self._run_pipeline(pipeline, params))
        self._recipe(recipe)  # fail fast on unknown names
        return self.jobs.start("recipe", recipe, {"params": params}, lambda: self.recipe_run(recipe, params))

    def job_status(
        self,
        job_id: Annotated[str | None, Field(description="Job id; omit to list recent jobs.")] = None,
        include_output: Annotated[bool, Field(description="Include the full output of a finished job.")] = False,
    ) -> dict[str, Any]:
        """Status, progress (fraction and current step), timings and result ids of a job; without job_id,
        the list of recent jobs. Read outputs with include_output=true or result_page."""
        if job_id is None:
            jobs = self.jobs.list()
            return {"jobs": jobs[:50], "total": len(jobs)}
        return self.jobs.status(job_id, include_output=include_output)

    def job_cancel(self, job_id: Annotated[str, Field(description="Job to cancel.")]) -> dict[str, Any]:
        """Request cancellation of a queued or running job (stops at the next checkpoint)."""
        return self.jobs.cancel(job_id)
