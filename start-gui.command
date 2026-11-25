#!/usr/bin/env bash
# macOS: double-click in Finder to start the Kitconc MCP Console in the background and open it in
# the browser. From a terminal: ./start-gui.command [--workspace DIR] [--port N] [--read-only] [--no-browser]
# Stop it with stop-gui.command.
cd "$(dirname "$0")" || exit 1
exec bash scripts/kitconc-console.sh start "$@"
