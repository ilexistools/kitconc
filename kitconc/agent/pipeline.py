# -*- coding: utf-8 -*-
"""Declarative pipelines: run several tools in one call, wiring outputs into inputs.

A pipeline is JSON::

    {
      "params": {"corpus": {"type": "string", "required": true, "description": "Corpus id"},
                 "top":    {"type": "integer", "default": 100}},
      "steps": [
        {"id": "terms", "tool": "term_candidates", "args": {"corpus": "$params.corpus", "limit": 0}},
        {"id": "ranked", "tool": "result_derive",
         "args": {"result_id": "$terms.result_id", "columns": {"CVALUE": "c_value(TERM, FREQUENCY)"}}},
        {"id": "top", "tool": "result_filter",
         "args": {"result_id": "$ranked.result_id", "sort_by": "CVALUE", "keep": "$params.top"}}
      ],
      "output": "top"
    }

References:
- ``"$params.name"`` / ``"$step_id.path.to.value"`` as a whole string pass the referenced value with its
  type (number, list, object...). Paths walk object keys and list indexes.
- ``"${params.name}"`` inside a longer string interpolates text, e.g. ``"exports/${params.corpus}.xlsx"``.
- ``foreach`` runs a step once per item of a list (``"foreach": "$params.words"``); the item is
  available as ``$item`` (or the name given in ``"as"``) and its position as ``$index``. The step
  output is ``{"items": [...], "result_ids": [...], "errors": [...]}``.
- ``"when": "$params.x"`` skips the step (output null, status "skipped") when the value is empty,
  false, 0 or null.
- ``"continue_on_error": true`` records the error and keeps going (the step output is null).
"""

from __future__ import annotations

import re
import time
from typing import Annotated, Any

from pydantic import Field, ValidationError as PydanticValidationError, validate_call

from kitconc.agent import progress
from kitconc.agent.results import ToolFailure

MAX_STEPS = 60
MAX_FOREACH = 500

_REF_RE = re.compile(r"^\$([A-Za-z_]\w*)((?:\.[\w-]+)*)$")
_INTERP_RE = re.compile(r"\$\{([A-Za-z_]\w*)((?:\.[\w-]+)*)\}")
_ID_RE = re.compile(r"^[A-Za-z_]\w*$")
_RESERVED = {"params", "item", "index"}

PipelineArg = Annotated[dict[str, Any], Field(description="Pipeline JSON: {params?, steps: [{id, tool, args, "
                                                          "foreach?, as?, continue_on_error?}], output?}. See "
                                                          "guide_read('pipelines').")]
ParamsArg = Annotated[dict[str, Any] | None, Field(description="Values for the pipeline/recipe params.")]


def _walk(value: Any, path: str, ref: str) -> Any:
    for part in [p for p in path.split(".") if p]:
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.lstrip("-").isdigit() and -len(value) <= int(part) < len(value):
            value = value[int(part)]
        else:
            raise ToolFailure("INVALID_REFERENCE", f"Cannot resolve '{ref}': no '{part}'.")
    return value


def resolve(value: Any, scope: dict[str, Any]) -> Any:
    """Replaces $references in a nested argument structure."""
    if isinstance(value, dict):
        return {k: resolve(v, scope) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, scope) for v in value]
    if not isinstance(value, str) or "$" not in value:
        return value
    match = _REF_RE.match(value)
    if match:
        root, path = match.group(1), match.group(2)
        if root not in scope:
            raise ToolFailure("INVALID_REFERENCE", f"Unknown reference '{value}'.",
                              candidates=sorted(scope))
        return _walk(scope[root], path, value)

    def interpolate(m):
        root, path = m.group(1), m.group(2)
        if root not in scope:
            raise ToolFailure("INVALID_REFERENCE", f"Unknown reference '{m.group(0)}'.", candidates=sorted(scope))
        return str(_walk(scope[root], path, m.group(0)))

    return _INTERP_RE.sub(interpolate, value)


def _references(value: Any) -> set[str]:
    roots: set[str] = set()
    if isinstance(value, dict):
        for v in value.values():
            roots |= _references(v)
    elif isinstance(value, list):
        for v in value:
            roots |= _references(v)
    elif isinstance(value, str) and "$" in value:
        match = _REF_RE.match(value)
        if match:
            roots.add(match.group(1))
        roots |= {m.group(1) for m in _INTERP_RE.finditer(value)}
    return roots


def validate_spec(spec: Any, tool_names: set[str], params: dict[str, Any] | None = None) -> list[str]:
    """Static checks: structure, unique ids, known tools and references to params or earlier steps."""
    errors: list[str] = []
    if not isinstance(spec, dict):
        return ["Pipeline must be an object."]
    steps = spec.get("steps")
    if not isinstance(steps, list) or not steps:
        return ["'steps' must be a non-empty list."]
    if len(steps) > MAX_STEPS:
        errors.append(f"Too many steps ({len(steps)} > {MAX_STEPS}).")
    declared = spec.get("params") or {}
    if not isinstance(declared, dict):
        errors.append("'params' must be an object of parameter declarations.")
        declared = {}
    known_params = set(declared) | set(params or {})
    seen: list[str] = []
    for i, step in enumerate(steps):
        label = f"step {i + 1}"
        if not isinstance(step, dict):
            errors.append(f"{label}: must be an object.")
            continue
        step_id = step.get("id") or f"step{i + 1}"
        label = f"step '{step_id}'"
        if not _ID_RE.match(str(step_id)) or step_id in _RESERVED:
            errors.append(f"{label}: id must be an identifier other than params, item or index.")
        if step_id in seen:
            errors.append(f"{label}: duplicate id.")
        tool = step.get("tool")
        if tool not in tool_names:
            errors.append(f"{label}: unknown or disallowed tool '{tool}'.")
        args = step.get("args", {})
        if not isinstance(args, dict):
            errors.append(f"{label}: 'args' must be an object.")
            args = {}
        loop_var = step.get("as", "item")
        allowed = set(seen) | {"params"} | ({loop_var, "index"} if "foreach" in step else set())
        refs = _references(args) | _references(step.get("foreach")) | _references(step.get("when"))
        for root in refs:
            if root not in allowed:
                errors.append(f"{label}: reference to '{root}' is not a param or an earlier step.")
        for ref in _params_used(args) | _params_used(step.get("foreach")) | _params_used(step.get("when")):
            if ref not in known_params:
                errors.append(f"{label}: '$params.{ref}' is not declared.")
        seen.append(step_id)
    output = spec.get("output")
    if output is not None and output not in seen:
        errors.append(f"'output' refers to unknown step '{output}'.")
    return errors


def _params_used(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        for v in value.values():
            names |= _params_used(v)
    elif isinstance(value, list):
        for v in value:
            names |= _params_used(v)
    elif isinstance(value, str):
        for m in list(_INTERP_RE.finditer(value)) + ([_REF_RE.match(value)] if _REF_RE.match(value) else []):
            if m.group(1) == "params" and m.group(2):
                names.add(m.group(2).split(".")[1])
    return names


def bind_params(spec: dict[str, Any], params: dict[str, Any] | None) -> dict[str, Any]:
    """Applies declared defaults and checks required params."""
    declared = spec.get("params") or {}
    values = dict(params or {})
    missing = []
    for name, decl in declared.items():
        decl = decl if isinstance(decl, dict) else {"default": decl}
        if name not in values:
            if "default" in decl:
                values[name] = decl["default"]
            elif decl.get("required", False):
                missing.append(name)
            else:
                values[name] = None
    if missing:
        raise ToolFailure("MISSING_PARAMS", f"Missing required params: {', '.join(missing)}",
                          hint="Pass them in `params`.", candidates=missing)
    return values


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in ("", "false", "0", "no", "none", "null")
    return bool(value)


def _digest(output: Any) -> dict[str, Any]:
    if isinstance(output, dict):
        keys = ("result_id", "total", "columns", "returned", "created", "deleted", "zip_path", "output_path",
                "rows_written", "ok", "summary", "stats_result_id", "result_ids")
        return {k: output[k] for k in keys if k in output}
    return {}


class PipelineMixin:
    """Mixed into KitconcTools; relies on ``self._failure`` and the tool methods."""

    _validators: dict[str, Any]

    def _pipeline_tools(self) -> set[str]:
        from kitconc.agent.tools import PIPELINE_TOOLS

        return set(PIPELINE_TOOLS)

    def _invoke(self, name: str, args: dict[str, Any]) -> Any:
        if not hasattr(self, "_validators"):
            self._validators = {}
        fn = self._validators.get(name)
        if fn is None:
            fn = validate_call(getattr(self, name))
            self._validators[name] = fn
        try:
            return fn(**args)
        except PydanticValidationError as exc:
            details = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()[:5])
            raise ToolFailure("INVALID_ARGUMENT", f"{name}: {details}") from exc

    def _run_pipeline(self, spec: dict[str, Any], params: dict[str, Any] | None) -> dict[str, Any]:
        if isinstance(spec, dict) and isinstance(spec.get("params") or {}, dict):
            values = bind_params(spec, params)  # missing required params are the most actionable error
        else:
            values = dict(params or {})
        errors = validate_spec(spec, self._pipeline_tools(), values)
        if errors:
            raise ToolFailure("INVALID_PIPELINE", errors[0], hint="Fix the pipeline; all problems listed.",
                              candidates=errors)
        scope: dict[str, Any] = {"params": values}
        report: list[dict[str, Any]] = []
        steps = spec["steps"]
        last_id = None
        for i, step in enumerate(steps):
            step_id = step.get("id") or f"step{i + 1}"
            tool = step["tool"]
            started = time.time()
            entry: dict[str, Any] = {"id": step_id, "tool": tool}
            if "when" in step and not _truthy(resolve(step["when"], scope)):
                entry.update(status="skipped", seconds=0.0)
                scope[step_id] = None
                report.append(entry)
                continue
            with progress.scope(i, len(steps), f"{step_id} ({tool})"):
                try:
                    if "foreach" in step:
                        output = self._run_foreach(step, scope)
                        entry["items"] = len(output["items"])
                        if output["errors"]:
                            entry["item_errors"] = len(output["errors"])
                    else:
                        output = self._invoke(tool, resolve(step.get("args", {}), scope))
                    entry["status"] = "ok"
                    entry.update(_digest(output))
                except progress.Cancelled:
                    raise
                except Exception as exc:  # noqa: BLE001 - reported per step
                    failure = self._failure(exc)
                    if not step.get("continue_on_error"):
                        failure.message = f"Step '{step_id}' ({tool}) failed: {failure.message}"
                        failure.candidates = (failure.candidates or []) + [{"completed_steps": report}]
                        raise failure from exc
                    output = None
                    entry["status"] = "error"
                    entry["error"] = failure.payload()["error"]
            entry["seconds"] = round(time.time() - started, 2)
            scope[step_id] = output
            report.append(entry)
            last_id = step_id
        output_id = spec.get("output") or last_id
        return {"steps": report, "output_step": output_id, "output": scope.get(output_id),
                "result_ids": {e["id"]: e["result_id"] for e in report if "result_id" in e}}

    def _run_foreach(self, step: dict[str, Any], scope: dict[str, Any]) -> dict[str, Any]:
        items = resolve(step["foreach"], scope)
        if not isinstance(items, list):
            raise ToolFailure("INVALID_PIPELINE", f"foreach of step '{step.get('id')}' did not resolve to a list.")
        if len(items) > MAX_FOREACH:
            raise ToolFailure("INVALID_PIPELINE", f"foreach has {len(items)} items (max {MAX_FOREACH}).",
                              hint="Run it as a job in batches or filter the list first.")
        var = step.get("as", "item")
        outputs, result_ids, errors = [], [], []
        for j, item in enumerate(items):
            with progress.scope(j, len(items), str(item)[:40]):
                local = dict(scope, **{var: item, "index": j})
                try:
                    out = self._invoke(step["tool"], resolve(step.get("args", {}), local))
                except progress.Cancelled:
                    raise
                except Exception as exc:  # noqa: BLE001
                    if not step.get("continue_on_error"):
                        raise
                    errors.append({"item": item, **self._failure(exc).payload()["error"]})
                    out = None
            outputs.append(out)
            if isinstance(out, dict) and "result_id" in out:
                result_ids.append(out["result_id"])
        return {"items": outputs, "result_ids": result_ids, "errors": errors}

    # -- tools -------------------------------------------------------------------------

    def pipeline_run(self, pipeline: PipelineArg, params: ParamsArg = None) -> dict[str, Any]:
        """Run several tools in one call, passing outputs between steps ($step.result_id, $params.x,
        foreach). Returns a per-step report, every result_id and the output step's payload. Use job_start
        for pipelines that take minutes."""
        return self._run_pipeline(pipeline, params)

    def pipeline_validate(self, pipeline: PipelineArg, params: ParamsArg = None) -> dict[str, Any]:
        """Check a pipeline without running it: structure, tool names and references."""
        errors = validate_spec(pipeline, self._pipeline_tools(), params)
        return {"valid": not errors, "errors": errors,
                "steps": [s.get("id") or f"step{i + 1}" for i, s in enumerate(pipeline.get("steps") or [])
                          if isinstance(s, dict)] if isinstance(pipeline, dict) else []}
