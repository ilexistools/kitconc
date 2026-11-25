#!/usr/bin/env bash
# macOS: double-click in Finder to stop the Kitconc MCP Console started with start-gui.command.
# From a terminal: ./stop-gui.command [--port N]
cd "$(dirname "$0")" || exit 1
exec bash scripts/kitconc-console.sh stop "$@"
