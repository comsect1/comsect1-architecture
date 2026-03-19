#!/usr/bin/env bash
# Run the unified AIAD gate against a target codebase.
# Usage: run-gates.sh [code-root]
#   code-root  Path to the comsect1 code directory (optional, skips code gate if omitted)

set -euo pipefail

SPEC_ROOT="{{COMSECT1_ROOT}}"
SCRIPT_DIR="$SPEC_ROOT/scripts"
REPORT_PATH=".aiad-gate-report.json"

CODE_ROOT="${1:-}"

if [[ -n "$CODE_ROOT" ]]; then
    python "$SCRIPT_DIR/Verify-AIADGate.py" \
        -CodeRoot "$CODE_ROOT" \
        -ReportPath "$REPORT_PATH"
else
    python "$SCRIPT_DIR/Verify-AIADGate.py" \
        -SkipCode \
        -ReportPath "$REPORT_PATH"
fi

echo "--- Gate report: $REPORT_PATH ---"
cat "$REPORT_PATH"
