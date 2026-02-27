#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_CMD=("$PYTHON_BIN")
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=("python3")
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=("python")
else
  echo "Python 3 is required to run comsect1 AI tooling." >&2
  exit 2
fi

exec "${PYTHON_CMD[@]}" "$REPO_ROOT/scripts/comsect1_ai_tooling.py" bootstrap --tool codex --project-root "${1:-.}"
