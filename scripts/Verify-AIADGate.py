#!/usr/bin/env python3
"""Unified AIAD gate runner for comsect1."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path


def add_stage_result(
    report: dict[str, object],
    *,
    name: str,
    status: str,
    exit_code: int,
    note: str,
    output_path: str | None,
) -> None:
    stage = {
        "name": name,
        "status": status,
        "exitCode": exit_code,
        "note": note,
        "outputPath": output_path,
    }
    stages = report.setdefault("stages", [])
    assert isinstance(stages, list)
    stages.append(stage)
    if status == "failed":
        report["gatePassed"] = False


def run_child(cmd: list[str]) -> int:
    result = subprocess.run(cmd, check=False)
    return int(result.returncode)


def resolve_repo_root(script_dir: Path, repo_root_arg: str | None) -> Path:
    if repo_root_arg:
        return Path(repo_root_arg).resolve()
    return (script_dir / "..").resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run spec/code gates and emit AIAD report.")
    parser.add_argument("-RepoRoot", dest="repo_root", default=None)
    parser.add_argument("-CodeRoot", dest="code_root", default=None)
    parser.add_argument("-ReportPath", dest="report_path", default=None)
    parser.add_argument("-SkipSpec", dest="skip_spec", action="store_true")
    parser.add_argument("-SkipCode", dest="skip_code", action="store_true")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    script_dir = script_path.parent

    repo_root = resolve_repo_root(script_dir, args.repo_root)

    report_path = Path(args.report_path) if args.report_path else (repo_root / ".aiad-gate-report.json")
    if not report_path.is_absolute():
        report_path = (repo_root / report_path).resolve()

    verify_spec = script_dir / "Verify-Spec.py"
    verify_code = script_dir / "Verify-Comsect1Code.py"

    if not verify_spec.is_file():
        raise RuntimeError(f"Missing script: {verify_spec}")
    if not verify_code.is_file():
        raise RuntimeError(f"Missing script: {verify_code}")

    report: dict[str, object] = {
        "generatedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "repoRoot": str(repo_root),
        "stages": [],
        "gatePassed": True,
    }

    # Stage 1: Spec verification
    if not args.skip_spec:
        print("[AIAD Gate] Stage 1/2: Verify-Spec")
        spec_cmd = [sys.executable, str(verify_spec), "-RepoRoot", str(repo_root)]
        spec_exit = run_child(spec_cmd)
        if spec_exit == 0:
            add_stage_result(
                report,
                name="spec",
                status="passed",
                exit_code=spec_exit,
                note="Verify-Spec passed",
                output_path=None,
            )
        else:
            add_stage_result(
                report,
                name="spec",
                status="failed",
                exit_code=spec_exit,
                note="Verify-Spec reported issues",
                output_path=None,
            )
    else:
        add_stage_result(
            report,
            name="spec",
            status="skipped",
            exit_code=0,
            note="Skipped by flag",
            output_path=None,
        )

    # Stage 2: Code architecture verification
    if not args.skip_code:
        code_root: Path | None = None
        if args.code_root:
            candidate = Path(args.code_root)
            if not candidate.is_absolute():
                candidate = repo_root / candidate
            code_root = candidate.resolve()
        else:
            default_code_root = (repo_root / "codes" / "comsect1").resolve()
            if default_code_root.is_dir():
                code_root = default_code_root

        if not code_root or not code_root.is_dir():
            add_stage_result(
                report,
                name="code",
                status="skipped",
                exit_code=0,
                note="Code root not provided/found; skipped code architecture stage",
                output_path=None,
            )
        else:
            report_dir_for_code = report_path.parent if report_path.parent else repo_root
            code_json = report_dir_for_code / "aiad-code-verify.json"
            print("[AIAD Gate] Stage 2/2: Verify-Comsect1Code")
            code_cmd = [
                sys.executable,
                str(verify_code),
                "-Root",
                str(code_root),
                "-JsonOut",
                str(code_json),
            ]
            code_exit = run_child(code_cmd)
            if code_exit == 0:
                add_stage_result(
                    report,
                    name="code",
                    status="passed",
                    exit_code=code_exit,
                    note="Verify-Comsect1Code passed",
                    output_path=str(code_json),
                )
            else:
                add_stage_result(
                    report,
                    name="code",
                    status="failed",
                    exit_code=code_exit,
                    note="Verify-Comsect1Code reported errors",
                    output_path=str(code_json),
                )
    else:
        add_stage_result(
            report,
            name="code",
            status="skipped",
            exit_code=0,
            note="Skipped by flag",
            output_path=None,
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[AIAD Gate] Report: {report_path}")
    print(f"[AIAD Gate] Status: {'PASSED' if report.get('gatePassed') else 'FAILED'}")

    return 0 if report.get("gatePassed") else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
