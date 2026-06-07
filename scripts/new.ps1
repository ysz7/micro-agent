# Scaffold a new vertical agent folder from this template.
# Usage: ./scripts/new.ps1 <agent-name>  ->  creates ..\<agent-name>
param([Parameter(Mandatory = $true)] [string] $Name)
$ErrorActionPreference = "Stop"

$src  = Split-Path $PSScriptRoot -Parent              # agent root (parent of scripts/)
$dest = Join-Path (Split-Path $src -Parent) $Name     # sibling of the agent root

if (Test-Path $dest) {
    Write-Error "refusing: $dest already exists"
    exit 1
}

New-Item -ItemType Directory -Path $dest, "$dest\tools", "$dest\workspace" -Force | Out-Null

# The frozen engine + the management scripts.
Copy-Item "$src\agent"   "$dest\agent"   -Recurse
Copy-Item "$src\scripts" "$dest\scripts" -Recurse

# Editable per-agent files + root launchers (NOT .env, workspace, or examples).
$files = @("pyproject.toml", "uv.lock", "README.md", "persona.md", "settings.yaml",
    ".env.example", "schedule.example", "start.cmd", "start.sh", ".gitignore",
    "Dockerfile", "docker-compose.yml", ".dockerignore")
foreach ($f in $files) {
    if (Test-Path "$src\$f") { Copy-Item "$src\$f" "$dest\$f" }
}
if (Test-Path "$src\tools\_example.py") { Copy-Item "$src\tools\_example.py" "$dest\tools\_example.py" }

# Name the new agent after its folder.
$sp = "$dest\settings.yaml"
if (Test-Path $sp) {
    (Get-Content $sp) -replace '^name:.*', "name: $Name" | Set-Content $sp -Encoding utf8
}

Write-Host "OK  new agent scaffolded at $dest"
Write-Host ""
Write-Host "  cd $dest"
Write-Host "  cp .env.example .env        # set PROVIDER / MODEL / API_KEY"
Write-Host "  edit persona.md             # describe the vertical"
Write-Host "  # drop tools into tools\*.py"
Write-Host "  ./start.cmd                 # or  ./scripts/run.ps1 'your task'"
