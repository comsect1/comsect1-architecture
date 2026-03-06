#!/usr/bin/env python3
"""Verify generated AI tooling surfaces and managed guide blocks remain aligned."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from comsect1_ai_tooling import verify_repo_tooling
from comsect1_gate_helpers import resolve_repo_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify comsect1 AI tooling consistency.")
    parser.add_argument("-RepoRoot", dest="repo_root", default=None)
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = resolve_repo_root(script_path, args.repo_root)

    issues = verify_repo_tooling(repo_root)

    print("Tooling consistency verification complete.")
    print(f"Issues: {len(issues)}")
    for issue in issues:
        print(f"- {issue}")

    if issues:
        print(f"\nGate FAILED -- {len(issues)} issue(s) must be resolved.")
        return 2

    print("\nGate passed -- no issues found.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
