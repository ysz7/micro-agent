@echo off
REM Double-click this file to open a terminal with the agent running (REPL).
REM You can also drag a file onto it, or run:  start.cmd "your task"
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
title micro-agent

where uv >nul 2>nul
if %errorlevel%==0 (
    uv run agent %*
) else (
    python -m uv run agent %*
)

echo.
echo [agent exited] press any key to close...
pause >nul
