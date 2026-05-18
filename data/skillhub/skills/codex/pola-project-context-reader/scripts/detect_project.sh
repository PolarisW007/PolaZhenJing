#!/usr/bin/env bash
set -euo pipefail

root="${1:-.}"
cd "$root"

echo "== Pola Project Detection =="
echo "root: $(pwd)"

echo
echo "== manifests =="
for f in package.json pnpm-lock.yaml yarn.lock package-lock.json pyproject.toml requirements.txt poetry.lock go.mod Cargo.toml pom.xml build.gradle build.gradle.kts Dockerfile docker-compose.yml compose.yaml Makefile Taskfile.yml justfile; do
  [ -e "$f" ] && echo "$f"
done

echo
echo "== likely package manager =="
if [ -f pnpm-lock.yaml ]; then echo "pnpm";
elif [ -f yarn.lock ]; then echo "yarn";
elif [ -f package-lock.json ]; then echo "npm";
elif [ -f pyproject.toml ]; then echo "python/pyproject";
elif [ -f requirements.txt ]; then echo "python/requirements";
elif [ -f go.mod ]; then echo "go";
elif [ -f Cargo.toml ]; then echo "rust";
elif [ -f pom.xml ]; then echo "maven";
elif [ -f build.gradle ] || [ -f build.gradle.kts ]; then echo "gradle";
else echo "unknown"; fi

echo
echo "== package scripts =="
if [ -f package.json ]; then
  node -e "const p=require('./package.json'); for (const [k,v] of Object.entries(p.scripts||{})) console.log(k+': '+v)" 2>/dev/null || true
fi

echo
echo "== docs =="
find . -maxdepth 3 -type f \( -iname 'readme*' -o -name 'AGENTS.md' -o -name 'CLAUDE.md' -o -name 'CONTRIBUTING.md' -o -name 'ARCHITECTURE.md' -o -name '开发日志.md' -o -name 'DEVLOG.md' -o -path './docs/*.md' -o -path './docs/*/*.md' \) | sort | sed -n '1,160p'

echo
echo "== ci =="
find . -maxdepth 3 -type f \( -path './.github/workflows/*' -o -path './.gitlab-ci.yml' -o -name 'Jenkinsfile' \) | sort

echo
echo "== git =="
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git branch --show-current
  git status --short
else
  echo "not a git repository"
fi
