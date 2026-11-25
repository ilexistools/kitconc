"""Local browser dashboard for the Kitconc MCP tool catalog."""

from __future__ import annotations

import argparse
from importlib.resources import files
from threading import Thread
import webbrowser

from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import HTMLResponse
import uvicorn

from kitconc.agent.mcp_server import build_server


HOST = "127.0.0.1"


def build_dashboard(workspace: str | None = None, *, port: int = 8787, read_only: bool = False):
    server = build_server(workspace=workspace, host=HOST, port=port, read_only=read_only)
    server.settings.stateless_http = True
    server.settings.json_response = True
    page = files(__package__).joinpath("dashboard.html").read_text(encoding="utf-8")

    @server.custom_route("/", methods=["GET"], include_in_schema=False)
    async def dashboard(request):
        return HTMLResponse(page, headers={"X-Frame-Options": "DENY"})

    app = server.streamable_http_app()
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
                print(f"Kitconc dashboard: {url}", flush=True)
                if not args.no_browser:
                    Thread(target=webbrowser.open, args=(url,), daemon=True).start()

    DashboardServer(uvicorn.Config(app, host=HOST, port=args.port, proxy_headers=False)).run()


if __name__ == "__main__":
    main()
