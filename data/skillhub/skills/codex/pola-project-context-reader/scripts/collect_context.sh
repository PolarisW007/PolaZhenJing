#!/usr/bin/env bash
set -euo pipefail

root="${1:-.}"
cd "$root"

echo "== top-level =="
find . \( -path './.git' -o -path './node_modules' -o -path './dist' -o -path './build' -o -path './coverage' -o -path './.venv' -o -path './__pycache__' \) -prune -o -maxdepth 2 -type d -print | sort | sed -n '1,120p'

echo
echo "== important files =="
find . \( -path './.git' -o -path './node_modules' -o -path './dist' -o -path './build' -o -path './coverage' -o -path './.venv' -o -path './__pycache__' \) -prune -o -maxdepth 3 -type f \( \
  -iname 'readme*' -o -name 'AGENTS.md' -o -name 'CLAUDE.md' -o -name 'CONTRIBUTING.md' \
  -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'go.mod' -o -name 'Cargo.toml' \
  -o -name 'Dockerfile' -o -name 'docker-compose.yml' -o -name 'compose.yaml' -o -name 'Makefile' \
  -o -name 'Taskfile.yml' -o -name 'justfile' -o -path './.github/workflows/*' -o -name 'SKILL.md' \) -print | sort | sed -n '1,220p'
