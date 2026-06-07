#!/usr/bin/env bash
# Scaffold a new vertical agent folder from this template.
# Usage: ./scripts/new.sh <agent-name>  ->  creates ../<agent-name>
set -euo pipefail

name="${1:?usage: ./scripts/new.sh <agent-name>}"
src="$(cd "$(dirname "$0")/.." && pwd)"     # agent root (parent of scripts/)
dest="$(dirname "$src")/$name"              # sibling of the agent root

if [ -e "$dest" ]; then
  echo "refusing: $dest already exists" >&2
  exit 1
fi

mkdir -p "$dest/tools" "$dest/workspace"

# The frozen engine + the management scripts.
cp -r "$src/agent"   "$dest/agent"
cp -r "$src/scripts" "$dest/scripts"

# Editable per-agent files + root launchers. NOT .env, workspace, or examples.
for f in pyproject.toml uv.lock README.md persona.md settings.yaml \
         .env.example schedule.example start.cmd start.sh .gitignore \
         Dockerfile docker-compose.yml .dockerignore; do
  [ -e "$src/$f" ] && cp "$src/$f" "$dest/$f"
done
[ -e "$src/tools/_example.py" ] && cp "$src/tools/_example.py" "$dest/tools/_example.py"

# Name the new agent after its folder.
if [ -f "$dest/settings.yaml" ]; then
  sed -i.bak "s/^name:.*/name: $name/" "$dest/settings.yaml" && rm -f "$dest/settings.yaml.bak"
fi

echo "✓ new agent scaffolded at $dest"
echo
echo "  cd $dest"
echo "  cp .env.example .env        # set PROVIDER / MODEL / API_KEY"
echo "  \$EDITOR persona.md          # describe the vertical"
echo "  # drop tools into tools/*.py"
echo "  ./start.sh                  # or  ./scripts/run.sh \"your task\""
