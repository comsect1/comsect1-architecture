#!/usr/bin/env python3
"""Unified AIAD gate runner for comsect1."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

OOP_EXTENSIONS = {".cs", ".vb"}


def check_spec_modifications(repo_root: Path) -> list[str]:
    """Return list of spec files that have uncommitted or staged changes."""
    specs_dir = repo_root / "specs"
    if not specs_dir.is_dir():
        return []
    modified: list[str] = []
    try:
        # Staged changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--", "specs/*.md"],
            cwd=str(repo_root), capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            modified.extend(
                line.strip() for line in result.stdout.splitlines() if line.strip()
            )
        # Unstaged changes
        result = subprocess.run(
            ["git", "diff", "--name-only", "--", "specs/*.md"],
            cwd=str(repo_root), capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            modified.extend(
                line.strip() for line in result.stdout.splitlines() if line.strip()
            )
    except FileNotFoundError:
        pass  # git not available
    return sorted(set(modified))


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


def resolve_root_arg(raw: str | None, repo_root: Path) -> Path | None:
    """Resolve a user-supplied root path, making relative paths absolute against repo_root."""
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def has_oop_files(root: Path) -> bool:
    """Return True if *root* contains at least one OOP source file."""
    for ext in OOP_EXTENSIONS:
        if next(root.rglob(f"*{ext}"), None) is not None:
            return True
    return False


def determine_stage_total(args: argparse.Namespace, code_root: Path | None,
                          oop_root: Path | None) -> int:
    """Calculate total number of active stages for progress display."""
    total = 0
    if not args.skip_spec:
        total += 1
    if not args.skip_code and code_root and code_root.is_dir():
        total += 1
    if not args.skip_oop and oop_root and oop_root.is_dir() and has_oop_files(oop_root):
        total += 1
    return max(total, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run spec/code/OOP gates and emit AIAD report.")
    parser.add_argument("-RepoRoot", dest="repo_root", default=None)
    parser.add_argument("-CodeRoot", dest="code_root", default=None)
    parser.add_argument("-OOPRoot", dest="oop_root", default=None,
                        help="Root directory for OOP architecture check (auto-detected from CodeRoot if omitted)")
    parser.add_argument("-ReportPath", dest="report_path", default=None)
    parser.add_argument("-SkipSpec", dest="skip_spec", action="store_true")
    parser.add_argument("-SkipCode", dest="skip_code", action="store_true")
    parser.add_argument("-SkipOOP", dest="skip_oop", action="store_true",
                        help="Skip OOP architecture verification stage")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    script_dir = script_path.parent

    repo_root = resolve_repo_root(script_dir, args.repo_root)

    report_path = Path(args.report_path) if args.report_path else (repo_root / ".aiad-gate-report.json")
    if not report_path.is_absolute():
        report_path = (repo_root / report_path).resolve()

    verify_spec = script_dir / "Verify-Spec.py"
    verify_code = script_dir / "Verify-Comsect1Code.py"
    verify_oop = script_dir / "Verify-OOPCode.py"

    if not verify_spec.is_file():
        raise RuntimeError(f"Missing script: {verify_spec}")
    if not verify_code.is_file():
        raise RuntimeError(f"Missing script: {verify_code}")

    # Resolve code root
    code_root: Path | None = resolve_root_arg(args.code_root, repo_root)
    if code_root is None:
        default_code_root = (repo_root / "codes" / "comsect1").resolve()
        if default_code_root.is_dir():
            code_root = default_code_root

    # Resolve OOP root: explicit arg > CodeRoot fallback > default
    oop_root: Path | None = resolve_root_arg(args.oop_root, repo_root)
    if oop_root is None and code_root and code_root.is_dir():
        oop_root = code_root

    stage_total = determine_stage_total(args, code_root, oop_root)
    stage_num = 0

    report: dict[str, object] = {
        "generatedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "repoRoot": str(repo_root),
        "stages": [],
        "gatePassed": True,
    }

    report_dir = report_path.parent if report_path.parent else repo_root

    # Stage 0: Meta-evaluation advisory (non-blocking)
    modified_specs = check_spec_modifications(repo_root)
    if modified_specs:
        file_list = ", ".join(modified_specs)
        advisory_note = (
            f"Spec modifications detected ({file_list}). "
            "Consider upstream alignment check (see guides/04_Meta_Evaluation/)."
        )
        print(f"[AIAD Gate] Stage 0 (advisory): {advisory_note}")
        add_stage_result(
            report,
            name="meta-advisory",
            status="advisory",
            exit_code=0,
            note=advisory_note,
            output_path=None,
        )
    else:
        add_stage_result(
            report,
            name="meta-advisory",
            status="clean",
            exit_code=0,
            note="No spec modifications detected",
            output_path=None,
        )

    # Stage 1: Spec verification
    if not args.skip_spec:
        stage_num += 1
        print(f"[AIAD Gate] Stage {stage_num}/{stage_total}: Verify-Spec")
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

    # Stage 2: C/embedded code architecture verification
    if not args.skip_code:
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
            stage_num += 1
            code_json = report_dir / "aiad-code-verify.json"
            print(f"[AIAD Gate] Stage {stage_num}/{stage_total}: Verify-Comsect1Code")
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

    # Stage 3: OOP architecture verification
    if not args.skip_oop:
        if not verify_oop.is_file():
            add_stage_result(
                report,
                name="oop",
                status="skipped",
                exit_code=0,
                note="Verify-OOPCode.py not found; skipped OOP stage",
                output_path=None,
            )
        elif not oop_root or not oop_root.is_dir():
            add_stage_result(
                report,
                name="oop",
                status="skipped",
                exit_code=0,
                note="OOP root not provided/found; skipped OOP stage",
                output_path=None,
            )
        elif not has_oop_files(oop_root):
            add_stage_result(
                report,
                name="oop",
                status="skipped",
                exit_code=0,
                note=f"No OOP source files ({', '.join(sorted(OOP_EXTENSIONS))}) found under {oop_root}",
                output_path=None,
            )
        else:
            stage_num += 1
            oop_json = report_dir / "aiad-oop-verify.json"
            print(f"[AIAD Gate] Stage {stage_num}/{stage_total}: Verify-OOPCode")
            oop_cmd = [
                sys.executable,
                str(verify_oop),
                "-Root",
                str(oop_root),
                "-ReportPath",
                str(oop_json),
            ]
            oop_exit = run_child(oop_cmd)
            if oop_exit == 0:
                add_stage_result(
                    report,
                    name="oop",
                    status="passed",
                    exit_code=oop_exit,
                    note="Verify-OOPCode passed",
                    output_path=str(oop_json),
                )
            else:
                add_stage_result(
                    report,
                    name="oop",
                    status="failed",
                    exit_code=oop_exit,
                    note="Verify-OOPCode reported errors",
                    output_path=str(oop_json),
                )
    else:
        add_stage_result(
            report,
            name="oop",
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
