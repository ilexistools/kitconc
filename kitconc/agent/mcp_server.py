# -*- coding: utf-8 -*-
"""MCP server exposing KitconcActions tools."""

from __future__ import annotations

import argparse
import dataclasses
import inspect
import json
from pathlib import Path
from typing import Any

from kitconc.agent.actions import (
    ActionLayerError,
    KitconcActions,
    NotFoundError,
    StateError,
    ValidationError,
)

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - optional dependency at runtime
    FastMCP = None


def _default_workspace(workspace: str | None, workspace_file: str | None) -> str:
    if workspace is not None and workspace.strip() != "":
        return workspace
    if workspace_file is not None and Path(workspace_file).exists():
        return Path(workspace_file).read_text(encoding="utf-8").strip()
    if Path("kitconc.tmp").exists():
        return Path("kitconc.tmp").read_text(encoding="utf-8").strip()
    return str((Path.cwd() / "kitconc_workspace").resolve())


def _serialize(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, tuple):
        return [_serialize(v) for v in value]
    return value


def _register_tools(server, actions: KitconcActions) -> None:
    for tool in actions.mcp_tool_catalog():
        name = tool["name"]
        description = tool["description"]
        input_schema = tool["inputSchema"]

        def make_handler(method_name: str, method_description: str, method_input_schema: dict[str, Any]):
            action_method = getattr(actions, method_name)

            def _handler(**kwargs):
                try:
                    result = action_method(**kwargs)
                    return _serialize(result)
                except (ValidationError, NotFoundError, StateError) as exc:
                    raise ValueError(str(exc)) from exc
                except ActionLayerError as exc:
                    raise RuntimeError(str(exc)) from exc

            _handler.__name__ = f"tool_{method_name}"
            _handler.__doc__ = f"{method_description}\n\nInput: {json.dumps(method_input_schema)}"
            # FastMCP builds the tool input model from inspect.signature(fn).
            # Ensure each dynamic handler exposes the original action signature
            # instead of a generic (**kwargs), which would create a required
            # `kwargs` field and break tool invocation.
            _handler.__signature__ = inspect.signature(action_method, eval_str=True)
            return _handler

        server.tool(name=name, description=description, structured_output=False)(
            make_handler(name, description, input_schema)
        )


def build_server(
    workspace: str | None = None,
    workspace_file: str | None = None,
    host: str = "127.0.0.1",
    port: int = 8001,
):
    if FastMCP is None:
        raise RuntimeError(
            "MCP runtime not installed. Install with: pip install mcp"
        )
    resolved_workspace = _default_workspace(workspace, workspace_file)
    actions = KitconcActions(resolved_workspace)
    init_params = inspect.signature(FastMCP.__init__).parameters
    server_kwargs: dict[str, Any] = {}
    if "host" in init_params:
        server_kwargs["host"] = host
    if "port" in init_params:
        server_kwargs["port"] = port
    server = FastMCP("kitconc", **server_kwargs)
    _register_tools(server, actions)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Kitconc MCP server")
    parser.add_argument("--workspace", type=str, default=None, help="Workspace path")
    parser.add_argument(
        "--workspace-file",
        type=str,
        default=None,
        help="File containing workspace path (default checks kitconc.tmp)",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http", "streamable_http"],
        default="stdio",
        help="MCP transport",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for SSE transport")
    parser.add_argument("--port", type=int, default=8001, help="Port for SSE transport")
    args = parser.parse_args()
    transport = "streamable-http" if args.transport == "streamable_http" else args.transport

    server = build_server(args.workspace, args.workspace_file, args.host, args.port)
    if transport == "stdio":
        server.run(transport="stdio")
    elif transport == "sse":
        run_params = inspect.signature(server.run).parameters
        if "host" in run_params and "port" in run_params:
            server.run(transport="sse", host=args.host, port=args.port)
        else:
            server.run(transport="sse")
    else:
        server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
