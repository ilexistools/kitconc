#!/usr/bin/env bash
# Start, stop or check the Kitconc MCP Console (kitconc-gui) on macOS and Linux.
#
#   scripts/kitconc-console.sh start   [--workspace DIR] [--port N] [--read-only] [--no-browser]
#   scripts/kitconc-console.sh stop    [--port N]
#   scripts/kitconc-console.sh status  [--port N]
#   scripts/kitconc-console.sh restart [same options as start]
#
# The server runs in the background; its output goes to kitconc-gui.log in the repository root.
# Set KITCONC_PORT to change the default port (8787).
# In Finder, double-click start-gui.command / stop-gui.command for the common case.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT/.kitconc-gui.pid"
LOG_FILE="$ROOT/kitconc-gui.log"

COMMAND=start
PORT="${KITCONC_PORT:-8787}"
WORKSPACE=""
READ_ONLY=0
NO_BROWSER=0

usage() {
    echo "Usage: kitconc-console.sh [start|stop|status|restart] [--workspace DIR] [--port N] [--read-only] [--no-browser]"
}

while [ $# -gt 0 ]; do
    case "$1" in
        start|stop|status|restart) COMMAND="$1" ;;
        --workspace) [ $# -ge 2 ] || { usage >&2; exit 2; }; WORKSPACE="$2"; shift ;;
        --port) [ $# -ge 2 ] || { usage >&2; exit 2; }; PORT="$2"; shift ;;
        --read-only) READ_ONLY=1 ;;
        --no-browser) NO_BROWSER=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

case "$PORT" in
    ''|*[!0-9]*) echo "Port must be a number." >&2; exit 2 ;;
esac
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then echo "Port must be between 1 and 65535." >&2; exit 2; fi
if [ -n "$WORKSPACE" ]; then
    case "$WORKSPACE" in /*) ;; *) WORKSPACE="$PWD/$WORKSPACE" ;; esac
fi
URL="http://127.0.0.1:${PORT}/"

if [ -t 1 ]; then GREEN=$'\033[32m'; RED=$'\033[31m'; YELLOW=$'\033[33m'; RESET=$'\033[0m'; else GREEN=""; RED=""; YELLOW=""; RESET=""; fi

# Prints the console's /api/info; fails when no Kitconc console answers on the port.
console_info() {
    local info
    info="$(curl -fsS --max-time 2 "${URL}api/info" 2>/dev/null)" || return 1
    case "$info" in *'"name":"kitconc"'*) printf '%s' "$info" ;; *) return 1 ;; esac
}

json_field() {  # json_field KEY JSON -> string value of a top-level field
    printf '%s' "$2" | sed -n "s/.*\"$1\":\"\\([^\"]*\\)\".*/\\1/p" | sed 's/\\\\/\\/g'
}

listener_pids() {
    if command -v lsof >/dev/null 2>&1; then
        lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null | sort -u || true
    fi
}

port_in_use() {
    [ -n "$(listener_pids)" ] && return 0
    curl -s --max-time 2 -o /dev/null "$URL" 2>/dev/null
}

open_browser() {
    [ "$NO_BROWSER" = 1 ] && return 0
    if command -v open >/dev/null 2>&1; then open "$URL"
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 &
    fi
}

show_endpoints() {
    echo
    echo "  Console            $URL"
    echo "  MCP (HTTP)         ${URL}mcp"
    echo "  MCP (SSE)          ${URL}sse"
    echo "  REST API           ${URL}api/tools"
    if [ -n "${1:-}" ]; then
        echo "  Workspace          $(json_field workspace "$1")"
        echo "  Version            $(json_field version "$1")"
    fi
    echo
}

# The background process recorded at start, ignoring a stale PID reused by another program.
saved_pid() {
    [ -f "$PID_FILE" ] || return 1
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    case "$pid" in ''|*[!0-9]*) return 1 ;; esac
    kill -0 "$pid" 2>/dev/null || return 1
    ps -p "$pid" -o command= 2>/dev/null | grep -q "kitconc.agent.dashboard" || return 1
    echo "$pid"
}

do_start() {
    local info pid i
    if info="$(console_info)"; then
        echo "${GREEN}Kitconc MCP Console is already running.${RESET}"
        show_endpoints "$info"
        open_browser
        return 0
    fi
    if port_in_use; then
        echo "${RED}Port $PORT is used by another program. Choose another one with --port.${RESET}" >&2
        return 1
    fi
    if ! command -v uv >/dev/null 2>&1; then
        echo "${RED}uv was not found. Install it from https://docs.astral.sh/uv/ and try again.${RESET}" >&2
        return 1
    fi
    if ! command -v curl >/dev/null 2>&1; then
        echo "${RED}curl was not found.${RESET}" >&2
        return 1
    fi

    cd "$ROOT"
    # Install or update the environment first. If that fails while a usable environment exists
    # (typically because another Kitconc process is using .venv), start with it anyway.
    echo "Preparing the Python environment (the first run can take a few minutes)..."
    if ! uv sync --locked --python 3.12 >"$LOG_FILE" 2>&1; then
        if [ -x "$ROOT/.venv/bin/python" ] || [ -x "$ROOT/.venv/Scripts/python.exe" ]; then
            echo "${YELLOW}Could not update the environment (is another Kitconc process running?); using the existing one.${RESET}"
        else
            echo "${RED}uv could not create the environment:${RESET}" >&2
            tail -n 20 "$LOG_FILE" | sed 's/^/  /' >&2
            return 1
        fi
    fi

    local args=(run --locked --python 3.12 --no-sync python -m kitconc.agent.dashboard --no-browser --port "$PORT")
    if [ -n "$WORKSPACE" ]; then args+=(--workspace "$WORKSPACE"); fi
    if [ "$READ_ONLY" = 1 ]; then args+=(--read-only); fi
    nohup uv "${args[@]}" >>"$LOG_FILE" 2>&1 </dev/null &
    pid=$!
    echo "$pid" >"$PID_FILE"

    printf "Starting Kitconc MCP Console"
    info=""
    for i in $(seq 1 300); do
        if info="$(console_info)"; then break; fi
        info=""
        kill -0 "$pid" 2>/dev/null || break
        printf "."
        sleep 1
    done
    echo
    if [ -z "$info" ]; then
        echo "${RED}The console did not start. Last lines of kitconc-gui.log:${RESET}" >&2
        tail -n 20 "$LOG_FILE" | sed 's/^/  /' >&2
        kill "$pid" 2>/dev/null || true
        rm -f "$PID_FILE"
        return 1
    fi
    echo "${GREEN}Kitconc MCP Console is running.${RESET}"
    show_endpoints "$info"
    echo "Stop it with stop-gui.command (or: scripts/kitconc-console.sh stop --port $PORT)."
    open_browser
}

wait_until_stopped() {
    local i
    for i in $(seq 1 20); do
        console_info >/dev/null || return 0
        sleep 0.5
    done
    return 1
}

do_stop() {
    local stopped=0 pid
    if pid="$(saved_pid)"; then
        kill -TERM "$pid" 2>/dev/null || true
        stopped=1
        wait_until_stopped || true
    fi
    rm -f "$PID_FILE"

    # Also stop a console started another way (e.g. kitconc-gui in a terminal), but only after
    # confirming that the program on the port really is Kitconc.
    if console_info >/dev/null; then
        for pid in $(listener_pids); do kill -TERM "$pid" 2>/dev/null || true; stopped=1; done
        if ! wait_until_stopped; then
            for pid in $(listener_pids); do kill -KILL "$pid" 2>/dev/null || true; done
        fi
    fi

    if console_info >/dev/null; then
        echo "${RED}Could not stop the console on port $PORT.${RESET}" >&2
        return 1
    elif [ "$stopped" = 1 ]; then
        echo "${GREEN}Kitconc MCP Console stopped (port $PORT).${RESET}"
    else
        echo "Kitconc MCP Console is not running on port $PORT."
    fi
}

do_status() {
    local info
    if info="$(console_info)"; then
        echo "${GREEN}Kitconc MCP Console is running.${RESET}"
        show_endpoints "$info"
        return 0
    fi
    echo "Kitconc MCP Console is not running on port $PORT."
    return 3
}

case "$COMMAND" in
    start) do_start ;;
    stop) do_stop ;;
    status) do_status ;;
    restart) do_stop >/dev/null; do_start ;;
esac
