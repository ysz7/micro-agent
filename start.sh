#!/usr/bin/env bash
# Double-click (or run ./start.sh) to open the agent REPL.
# Pass a task to run once:  ./start.sh "your task"
cd "$(dirname "$0")"
export PYTHONUTF8=1

if command -v uv >/dev/null 2>&1; then
  uv run agent "$@"
else
  python3 -m uv run agent "$@"
fi
