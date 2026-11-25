@echo off
cd /d "%~dp0"
uv run --locked --python 3.12 kitconc-gui %*
if errorlevel 1 pause
