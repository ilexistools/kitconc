@echo off
rem Stop the Kitconc MCP Console started with start-gui.cmd (option: --port N).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\kitconc-console.ps1" stop %*
if errorlevel 1 pause
