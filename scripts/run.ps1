# Launch this agent. Usage: ./scripts/run.ps1 "your task"   (no task -> REPL)
param([Parameter(ValueFromRemainingArguments = $true)] $Args)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)   # agent root (parent of scripts/)
$env:PYTHONUTF8 = "1"

if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv run agent @Args
} else {
    python -m uv run agent @Args
}
