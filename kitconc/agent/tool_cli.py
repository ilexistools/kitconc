# -*- coding: utf-8 -*-
"""Command-line access to the curated Kitconc tools (``kitconc-tool``).

Runs the same tools as the MCP server, in-process, and prints JSON. Useful for agents and scripts
where the MCP server is not configured::

    kitconc-tool --workspace ./kitconc_workspace workspace_info
    kitconc-tool analyze_kwic '{"corpus": "ads", "node": "experience", "sample": 10}'
    kitconc-tool recipe_run '{"name": "glossary-candidates", "params": {"corpus": "ads"}}'
    echo '{"corpus": "ads"}' | kitconc-tool corpus_qa -
    kitconc-tool --list

Each invocation is a separate process: results persist in the workspace (``result_id`` values can
be reused by later calls), but background jobs cannot outlive the call, so ``job_start`` is not
available here — run pipelines and recipes directly instead.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from kitconc.agent import progress
from kitconc.agent.actions import KitconcActions
from kitconc.agent.mcp_server import _default_workspace
from kitconc.agent.results import ToolFailure, clean
from kitconc.agent.tools import TOOL_SPECS, KitconcTools, _map_exception

UNAVAILABLE = {"job_start": "Background jobs need a running server; call the tool, pipeline or recipe directly."}


def _parse_args(raw: str | None) -> dict[str, Any]:
    if raw is None or raw.strip() == "":
        return {}
    if raw.strip() == "-":
        raw = sys.stdin.read()
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise ToolFailure("INVALID_ARGUMENT", f"Arguments must be a JSON object: {exc}") from exc
    if not isinstance(value, dict):
        raise ToolFailure("INVALID_ARGUMENT", "Arguments must be a JSON object.")
    return value


def _print(payload: Any, pretty: bool) -> None:
    text = json.dumps(clean(payload), ensure_ascii=False, indent=2 if pretty else None, default=str)
    sys.stdout.buffer.write(text.encode("utf-8") + b"\n")
    sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kitconc-tool",
        description="Run a Kitconc agent tool and print its JSON result.",
        epilog="Tool reference: kitconc-tool --list; guides: kitconc-tool guide_read '{\"topic\": \"overview\"}'",
    )
    parser.add_argument("tool", nargs="?", help="Tool name, e.g. workspace_info, analyze_kwic, recipe_run")
    parser.add_argument("arguments", nargs="?", help="JSON object with the tool arguments, or '-' for stdin")
    parser.add_argument("--workspace", default=None, help="Workspace folder (default: kitconc.tmp or ./kitconc_workspace)")
    parser.add_argument("--workspace-file", default=None, help="File containing the workspace path")
    parser.add_argument("--list", action="store_true", help="List the available tools")
    parser.add_argument("--pretty", action="store_true", help="Indent the JSON output")
    parser.add_argument("--progress", action="store_true", help="Print progress messages to stderr")
    args = parser.parse_args(argv)

    specs = {spec.name: spec for spec in TOOL_SPECS if spec.name not in UNAVAILABLE}
    if args.list or not args.tool:
        listing = []
        for name, spec in specs.items():
            method = getattr(KitconcTools, name)
            paragraph = (method.__doc__ or "").strip().split("\n\n")[0]
            doc = " ".join(line.strip() for line in paragraph.splitlines())
            listing.append({"tool": name, "group": spec.group, "read_only": bool(spec.annotations.readOnlyHint),
                            "summary": doc})
        _print({"tools": listing}, args.pretty)
        return 0

    workspace = _default_workspace(args.workspace, args.workspace_file)
    tools = KitconcTools(KitconcActions(workspace))
    try:
        if args.tool in UNAVAILABLE:
            raise ToolFailure("INVALID_ARGUMENT", f"'{args.tool}' is not available from the CLI.",
                              hint=UNAVAILABLE[args.tool])
        if args.tool not in specs:
            raise ToolFailure("NOT_FOUND", f"Unknown tool: {args.tool}", hint="Run kitconc-tool --list.",
                              candidates=sorted(specs))
        call_args = _parse_args(args.arguments)

        def sink(fraction: float, message: str) -> None:
            sys.stderr.write(f"[{fraction * 100:5.1f}%] {message}\n")

        with progress.install(sink if args.progress else None):
            result = tools._invoke(args.tool, call_args)
        _print(result, args.pretty)
        return 0
    except Exception as exc:  # noqa: BLE001 - reported as structured JSON
        _print(_map_exception(exc, tools).payload(), args.pretty)
        return 1


if __name__ == "__main__":
    sys.exit(main())
