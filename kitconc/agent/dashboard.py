"""Local browser dashboard for the Kitconc MCP tool catalog.

One local process serves:

* ``/``                    the dashboard page;
* ``/mcp``                 MCP over Streamable HTTP;
* ``/sse`` + ``/messages`` MCP over SSE (legacy transport);
* ``/api/...``             a small JSON REST API over the same tools.
"""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version as package_version
from importlib.resources import files
import json
import os
import shutil
import sys
from threading import Thread
from typing import Any
import webbrowser

from mcp.types import CallToolResult
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import HTMLResponse, JSONResponse
import uvicorn

from kitconc.agent.mcp_server import _default_workspace, build_server
from kitconc.agent.tools import TOOL_SPECS


HOST = "127.0.0.1"
TOOL_GROUPS = {spec.name: spec.group for spec in TOOL_SPECS}


def _kitconc_version() -> str:
    try:
        return package_version("kitconc")
    except PackageNotFoundError:
        return "dev"


def _stdio_command(workspace: str, read_only: bool) -> list[str]:
    """Command an MCP client can spawn to talk to Kitconc over stdio."""
    executable = shutil.which("kitconc-mcp")
    command = [executable] if executable else [sys.executable, "-m", "kitconc.agent.mcp_server"]
    command += ["--transport", "stdio", "--workspace", workspace]
    if read_only:
        command.append("--read-only")
    return command


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def _payload(result: Any) -> tuple[bool, Any]:
    """Turn a tool call result into (is_error, JSON payload)."""
    if isinstance(result, CallToolResult):
        is_error, content = bool(result.isError), result.content
        if result.structuredContent is not None:
            return is_error, result.structuredContent
    elif isinstance(result, tuple):
        content, structured = result
        if structured is not None:
            return False, structured
        is_error = False
    else:
        is_error, content = False, result
    items = []
    for item in content:
        if getattr(item, "type", None) == "text":
            try:
                items.append(json.loads(item.text))
            except ValueError:
                items.append(item.text)
        else:
            items.append(item.model_dump(mode="json", exclude_none=True))
    return is_error, items[0] if len(items) == 1 else items


def build_dashboard(workspace: str | None = None, *, port: int = 8787, read_only: bool = False):
    workspace = _default_workspace(workspace, None)
    server = build_server(workspace=workspace, host=HOST, port=port, read_only=read_only)
    server.settings.stateless_http = True
    server.settings.json_response = True
    page = files(__package__).joinpath("dashboard.html").read_text(encoding="utf-8")
    info = {
        "name": "kitconc",
        "version": _kitconc_version(),
        "workspace": os.path.abspath(workspace),
        "read_only": read_only,
        "endpoints": {"streamable_http": "/mcp", "sse": "/sse", "rest": "/api"},
        "commands": {"stdio": _stdio_command(os.path.abspath(workspace), read_only)},
    }

    async def tool_catalog() -> list[dict[str, Any]]:
        catalog = []
        for tool in await server.list_tools():
            entry = tool.model_dump(mode="json", exclude_none=True)
            entry["group"] = TOOL_GROUPS.get(tool.name, "other")
            catalog.append(entry)
        return catalog

    @server.custom_route("/", methods=["GET"], include_in_schema=False)
    async def dashboard(request):
        return HTMLResponse(page, headers={"X-Frame-Options": "DENY", "Cache-Control": "no-store"})

    @server.custom_route("/api/info", methods=["GET"], include_in_schema=False)
    async def api_info(request):
        return JSONResponse({**info, "tool_count": len(await server.list_tools())})

    @server.custom_route("/api/tools", methods=["GET"], include_in_schema=False)
    async def api_tools(request):
        return JSONResponse({"tools": await tool_catalog()})

    @server.custom_route("/api/tools/{name}", methods=["GET", "POST"], include_in_schema=False)
    async def api_tool(request):
        name = request.path_params["name"]
        tool = next((entry for entry in await tool_catalog() if entry["name"] == name), None)
        if tool is None:
            return _error(404, "NOT_FOUND", f"Unknown tool: {name}")
        if request.method == "GET":
            return JSONResponse(tool)
        # Requiring a JSON body forces a CORS preflight, so other sites cannot trigger tools.
        content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type != "application/json":
            return _error(415, "UNSUPPORTED_MEDIA_TYPE", "Send the arguments as application/json.")
        body = await request.body()
        try:
            arguments = json.loads(body) if body.strip() else {}
        except ValueError as exc:
            return _error(400, "INVALID_JSON", f"Invalid JSON body: {exc}")
        if not isinstance(arguments, dict):
            return _error(400, "INVALID_ARGUMENT", "Arguments must be a JSON object.")
        try:
            result = await server.call_tool(name, arguments)
        except Exception as exc:  # noqa: BLE001 - argument validation errors
            return _error(400, "INVALID_ARGUMENT", str(exc))
        is_error, payload = _payload(result)
        return JSONResponse(payload, status_code=422 if is_error else 200)

    app = server.streamable_http_app()
    sse_routes = [route for route in server.sse_app().routes if getattr(route, "path", "") in {"/sse", "/messages"}]
    app.router.routes.extend(sse_routes)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=[HOST, "localhost"])
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Open the local Kitconc MCP tools dashboard")
    parser.add_argument("--workspace", help="Folder containing the corpora")
    parser.add_argument("--port", type=int, default=8787, help="Local port (default: 8787)")
    parser.add_argument("--read-only", action="store_true", help="Expose the read-only MCP catalog")
    parser.add_argument("--no-browser", action="store_true", help="Start without opening the browser")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    url = f"http://{HOST}:{args.port}/"
    app = build_dashboard(args.workspace, port=args.port, read_only=args.read_only)

    class DashboardServer(uvicorn.Server):
        async def startup(self, sockets=None):
            await super().startup(sockets=sockets)
            if self.started:
                print(f"Kitconc dashboard:        {url}", flush=True)
                print(f"MCP (Streamable HTTP):    {url}mcp", flush=True)
                print(f"MCP (SSE):                {url}sse", flush=True)
                print(f"REST API:                 {url}api/tools", flush=True)
                if not args.no_browser:
                    Thread(target=webbrowser.open, args=(url,), daemon=True).start()

    DashboardServer(uvicorn.Config(app, host=HOST, port=args.port, proxy_headers=False)).run()


if __name__ == "__main__":
    main()
