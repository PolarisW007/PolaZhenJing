#!/usr/bin/env bash
set -euo pipefail

failures=()

run_cmd() {
  local label="$1"
  shift
  echo "== $label =="
  if ! "$@"; then
    failures+=("$label")
  fi
}

run_if_script() {
  local manager="$1"
  local script="$2"
  if [ -f package.json ] && node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts['$script'] ? 0 : 1)" 2>/dev/null; then
    run_cmd "$manager run $script" "$manager" run "$script"
  fi
}

if [ -f package.json ]; then
  if [ -f pnpm-lock.yaml ] && command -v pnpm >/dev/null 2>&1; then
    pm=pnpm
  elif [ -f yarn.lock ] && command -v yarn >/dev/null 2>&1; then
    pm=yarn
  else
    pm=npm
  fi
  run_if_script "$pm" lint
  run_if_script "$pm" typecheck
  run_if_script "$pm" test
  run_if_script "$pm" build
fi

if [ -f pyproject.toml ] || [ -f pytest.ini ] || [ -d tests ]; then
  if command -v pytest >/dev/null 2>&1; then
    run_cmd "pytest" pytest
  else
    echo "pytest not found"
  fi
fi

if [ -f go.mod ]; then
  run_cmd "go test ./..." go test ./...
fi

if [ -f Cargo.toml ]; then
  run_cmd "cargo test" cargo test
fi

if [ "${#failures[@]}" -gt 0 ]; then
  echo
  echo "== failed quality gates =="
  printf '%s\n' "${failures[@]}"
  exit 1
fi

echo
echo "All discovered quality gates passed."
