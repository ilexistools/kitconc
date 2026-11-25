@echo off
rem Start the Kitconc MCP Console in the background and open it in the browser.
rem Options: --workspace DIR  --port N  --read-only  --no-browser   (stop with stop-gui.cmd)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\kitconc-console.ps1" start %*
if errorlevel 1 pause
