#!/usr/bin/env python3
"""
Verify-OOPCode.py - comsect1 Architecture Gate for OOP Languages (VB.NET / C#)

Checks all three architecture layers (ida_, prx_, poi_) for dependency direction
violations, forbidden imports, and cross-feature reference violations.
Equivalent to Verify-Comsect1Code.py for C/C++ projects.

See: specs/A2_oop_adaptation.md (Appendix B)

Usage:
    python Verify-OOPCode.py -Root <project_root> [-Extensions .vb,.cs] [-ReportPath <path>]

Exit codes:
    0 - Gate passed (no violations)
    2 - Gate failed (violations found)
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Source file extensions to inspect
# ---------------------------------------------------------------------------
DEFAULT_EXTENSIONS = {".vb", ".cs"}

# ---------------------------------------------------------------------------
# Role detection: filename prefix -> architectural role
# ---------------------------------------------------------------------------
ROLE_PREFIXES = {
    "ida_": "idea",
    "prx_": "praxis",
    "poi_": "poiesis",
}

# Shared resource prefixes: these are NOT features and are excluded from
# cross-feature reference checks (A2.5.2: Shared Domain Utilities)
SHARED_RESOURCE_PREFIXES = {"cfg_", "db_", "stm_", "svc_", "mdw_", "hal_", "bsp_"}

# ---------------------------------------------------------------------------
# Rules for the 'idea' layer (A2.6.1: Idea importing external namespace)
# ---------------------------------------------------------------------------

# Forbidden namespace imports in ida_ files
# Key: rule ID, Value: (regex pattern, human message)
IDA_FORBIDDEN_IMPORTS_VB = {
    "ida-no-winforms":     (r"^\s*Imports\s+System\.Windows\.Forms", "Imports System.Windows.Forms (WinForms UI layer)"),
    "ida-no-drawing":      (r"^\s*Imports\s+System\.Drawing(?!\s*\.\s*Color\b)", "Imports System.Drawing (Graphics API)"),
    "ida-no-interop":      (r"^\s*Imports\s+Microsoft\.Office\.Interop", "Imports Microsoft.Office.Interop (COM Interop)"),
    "ida-no-serialport":   (r"^\s*Imports\s+System\.IO\.Ports", "Imports System.IO.Ports (SerialPort/hardware)"),
    "ida-no-fileio":       (r"^\s*Imports\s+System\.IO\b", "Imports System.IO (File I/O)"),
}

IDA_FORBIDDEN_IMPORTS_CS = {
    "ida-no-winforms":     (r"^\s*using\s+System\.Windows\.Forms\s*;", "using System.Windows.Forms (WinForms UI layer)"),
    "ida-no-drawing":      (r"^\s*using\s+System\.Drawing\s*;", "using System.Drawing (Graphics API)"),
    "ida-no-interop":      (r"^\s*using\s+Microsoft\.Office\.Interop", "using Microsoft.Office.Interop (COM Interop)"),
    "ida-no-serialport":   (r"^\s*using\s+System\.IO\.Ports\s*;", "using System.IO.Ports (SerialPort/hardware)"),
    "ida-no-fileio":       (r"^\s*using\s+System\.IO\s*;", "using System.IO (File I/O)"),
}

# Forbidden API call patterns in ida_ files (language-neutral)
IDA_FORBIDDEN_CALLS = {
    "ida-no-messagebox":   (r"\bMessageBox\.Show\s*\(", "MessageBox.Show (UI feedback must stay in prx_/poi_)"),
    "ida-no-invoke":       (r"\.(?:Begin)?Invoke\s*\(", ".Invoke / .BeginInvoke (UI thread marshal)"),
    "ida-no-threadsleep":  (r"\bThread\.Sleep\s*\(", "Thread.Sleep (blocking delay; use timing abstraction)"),
    "ida-no-processstart": (r"\bProcess\.Start\s*\(", "Process.Start (OS shell call)"),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_role(filename: str) -> str | None:
    """Return architectural role string if filename matches a known prefix, else None."""
    name = Path(filename).name.lower()
    for prefix, role in ROLE_PREFIXES.items():
        if name.startswith(prefix):
            return role
    return None


def get_prefix(filename: str) -> str | None:
    """Return the architectural prefix (e.g. 'ida_') if filename matches, else None."""
    name = Path(filename).name.lower()
    for prefix in ROLE_PREFIXES:
        if name.startswith(prefix):
            return prefix
    return None


def collect_source_files(root: Path, extensions: set[str]) -> list[Path]:
    files = []
    for ext in extensions:
        files.extend(root.rglob(f"*{ext}"))
    return sorted(set(files))


def add_finding(findings: list, severity: str, file_path: Path, line_no: int,
                rule: str, message: str) -> None:
    findings.append({
        "severity": severity,
        "file": str(file_path),
        "line": line_no,
        "rule": rule,
        "message": message,
    })


def extract_class_name(file_path: Path) -> str:
    """Extract the class/module name from filename by removing extension.
    e.g. ida_ColorConversion.vb -> ida_ColorConversion
    """
    return file_path.stem


def extract_feature_name(file_path: Path) -> str | None:
    """Extract the feature name from a prefixed filename.
    e.g. ida_ColorConversion.vb -> ColorConversion
         prx_LinProtocol.vb -> LinProtocol
    Returns None if no recognized prefix or if it's a shared resource.
    """
    stem = file_path.stem.lower()
    for prefix in ROLE_PREFIXES:
        if stem.startswith(prefix):
            return file_path.stem[len(prefix):]
    return None


def is_shared_resource(file_path: Path) -> bool:
    """Return True if the file is a shared resource (cfg_, db_, stm_, svc_, etc.).
    Shared resources are not features and are excluded from cross-feature checks.
    See A2.5.2: Shared Domain Utilities.
    """
    name = file_path.name.lower()
    return any(name.startswith(prefix) for prefix in SHARED_RESOURCE_PREFIXES)


# ---------------------------------------------------------------------------
# Build reference maps for dependency direction checking
# ---------------------------------------------------------------------------

def build_class_map(files: list[Path]) -> dict[str, list[Path]]:
    """Build mapping: role -> list of (class_name, file_path) for all recognized files."""
    role_map: dict[str, list[tuple[str, Path]]] = {"idea": [], "praxis": [], "poiesis": []}
    for f in files:
        role = get_role(f.name)
        if role and role in role_map:
            role_map[role].append((extract_class_name(f), f))
    return role_map


# ---------------------------------------------------------------------------
# Stage 1: Idea layer verification (existing)
# ---------------------------------------------------------------------------

def verify_idea_file(file_path: Path, findings: list) -> None:
    """Check ida_ files for forbidden imports and API calls."""
    ext = file_path.suffix.lower()
    import_rules = IDA_FORBIDDEN_IMPORTS_VB if ext == ".vb" else IDA_FORBIDDEN_IMPORTS_CS

    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        add_finding(findings, "error", file_path, 0, "file-read-error", str(e))
        return

    compiled_imports = {rid: re.compile(pat, re.IGNORECASE) for rid, (pat, _) in import_rules.items()}
    compiled_calls   = {rid: re.compile(pat) for rid, (pat, _) in IDA_FORBIDDEN_CALLS.items()}

    for line_no, line in enumerate(lines, start=1):
        # Check forbidden imports
        for rule_id, regex in compiled_imports.items():
            if regex.search(line):
                _, msg = import_rules[rule_id]
                add_finding(findings, "error", file_path, line_no, rule_id,
                            f"Forbidden in ida_: {msg}")

        # Check forbidden API calls
        for rule_id, regex in compiled_calls.items():
            if regex.search(line):
                _, msg = IDA_FORBIDDEN_CALLS[rule_id]
                add_finding(findings, "error", file_path, line_no, rule_id,
                            f"Forbidden in ida_: {msg}")


# ---------------------------------------------------------------------------
# Stage 2: Reverse dependency checks (A2.3.2, A2.6.2, A2.6.3)
# ---------------------------------------------------------------------------

def verify_reverse_dependencies(file_path: Path, role: str, role_map: dict,
                                findings: list) -> None:
    """Check that prx_ does not reference ida_, and poi_ does not reference ida_/prx_."""
    if role not in ("praxis", "poiesis"):
        return

    # Determine which roles are forbidden to reference
    if role == "praxis":
        forbidden_roles = ["idea"]
    else:  # poiesis
        forbidden_roles = ["idea", "praxis"]

    # Build list of forbidden class names
    forbidden_names: list[tuple[str, str]] = []  # (class_name, role_label)
    for frole in forbidden_roles:
        for class_name, _ in role_map.get(frole, []):
            forbidden_names.append((class_name, frole))

    if not forbidden_names:
        return

    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        add_finding(findings, "error", file_path, 0, "file-read-error", str(e))
        return

    # Build regex patterns for each forbidden class name
    # Match word-boundary class name references (not inside comments ideally,
    # but comment-aware parsing is out of scope for this gate)
    forbidden_patterns: list[tuple[re.Pattern, str, str]] = []
    for class_name, role_label in forbidden_names:
        # Skip if the forbidden class name is a substring of the current file's class name
        # (avoid self-matching in edge cases)
        own_name = extract_class_name(file_path)
        if class_name == own_name:
            continue
        pattern = re.compile(r"\b" + re.escape(class_name) + r"\b")
        forbidden_patterns.append((pattern, class_name, role_label))

    role_prefix = get_prefix(file_path.name)
    for line_no, line in enumerate(lines, start=1):
        # Skip comment lines (basic heuristic)
        stripped = line.strip()
        if stripped.startswith("'") or stripped.startswith("//") or stripped.startswith("/*"):
            continue

        for pattern, class_name, role_label in forbidden_patterns:
            if pattern.search(line):
                rule_id = f"{role_prefix}no-{role_label}-ref"
                add_finding(findings, "error", file_path, line_no, rule_id,
                            f"Reverse dependency: {role_prefix} references {class_name} ({role_label} layer)")


# ---------------------------------------------------------------------------
# Stage 3: Cross-feature layer reference check (A2.6.5)
# ---------------------------------------------------------------------------

def verify_cross_feature_references(file_path: Path, role: str, all_layer_files: list[Path],
                                    findings: list) -> None:
    """Check that feature layer files do not reference layer files from other features.

    Shared resources (cfg_, db_, stm_, svc_, mdw_, hal_, bsp_) are excluded from
    this check per A2.5.2 (Shared Domain Utilities). They belong to the capability
    plane or data plane, not to any specific feature.
    """
    # Skip shared resource files — they are not features
    if is_shared_resource(file_path):
        return

    own_feature = extract_feature_name(file_path)
    if own_feature is None:
        return

    # Collect layer class names from OTHER features (excluding shared resources)
    cross_feature_names: list[tuple[str, str]] = []  # (class_name, feature_name)
    for other_file in all_layer_files:
        # Skip shared resources — they are accessible from any layer per dependency rules
        if is_shared_resource(other_file):
            continue
        other_feature = extract_feature_name(other_file)
        if other_feature is None:
            continue
        # Same feature is allowed
        if other_feature.lower() == own_feature.lower():
            continue
        other_class = extract_class_name(other_file)
        # Only flag ida_/prx_/poi_ cross-references
        other_role = get_role(other_file.name)
        if other_role:
            cross_feature_names.append((other_class, other_feature))

    if not cross_feature_names:
        return

    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        add_finding(findings, "error", file_path, 0, "file-read-error", str(e))
        return

    cross_patterns: list[tuple[re.Pattern, str, str]] = []
    for class_name, feature_name in cross_feature_names:
        pattern = re.compile(r"\b" + re.escape(class_name) + r"\b")
        cross_patterns.append((pattern, class_name, feature_name))

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("'") or stripped.startswith("//") or stripped.startswith("/*"):
            continue

        for pattern, class_name, feature_name in cross_patterns:
            if pattern.search(line):
                add_finding(findings, "error", file_path, line_no, "cross-feature-layer-ref",
                            f"Cross-feature reference: references {class_name} from feature '{feature_name}' (use stm_ data plane)")


# ---------------------------------------------------------------------------
# Stage 4: Red Flag heuristics (advisory, per §11.8)
# ---------------------------------------------------------------------------

# Minimum non-comment lines expected in an ida_ file.
# Fewer suggests an "Empty Idea" pass-through.
MIN_IDA_LINES = 10

# Patterns that indicate domain-meaningful conditionals in poi_ files.
# Their presence suggests business logic that belongs in ida_ or prx_.
DOMAIN_CONDITIONAL_RE = re.compile(
    r"\b(?:if|switch|case)\b.*\b(?:mode|state|status|level|type|flag|enable|disable|active|threshold)\b",
    re.IGNORECASE,
)


def count_code_lines(file_path: Path) -> int:
    """Count non-blank, non-comment lines in a source file."""
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return 0

    count = 0
    in_block_comment = False
    for line in lines:
        stripped = line.strip()
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("/*"):
            in_block_comment = True
            continue
        if not stripped or stripped.startswith("'") or stripped.startswith("//"):
            continue
        count += 1
    return count


def verify_red_flags(ida_files: list[Path], prx_files: list[Path],
                     poi_files: list[Path], findings: list) -> None:
    """Check for §11.8 Red Flag patterns (advisory severity only)."""
    # Red Flag: Empty Idea
    for f in ida_files:
        code_lines = count_code_lines(f)
        if code_lines < MIN_IDA_LINES:
            add_finding(findings, "warning", f, 0, "red-flag-empty-idea",
                        f"Possible Empty Idea: only {code_lines} code line(s) "
                        f"(threshold: {MIN_IDA_LINES}). Verify that domain logic is not in prx_/poi_.")

    # Red Flag: Fat Poiesis (domain conditionals in poi_)
    for f in poi_files:
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("'") or stripped.startswith("//"):
                continue
            if DOMAIN_CONDITIONAL_RE.search(line):
                add_finding(findings, "warning", f, line_no, "red-flag-fat-poiesis",
                            "Possible Fat Poiesis: domain-meaningful conditional in poi_ file. "
                            "Consider moving business logic to ida_ or prx_.")
                break  # One warning per file is sufficient


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run(root: Path, extensions: set[str], report_path: Path | None) -> int:
    findings: list[dict] = []

    files = collect_source_files(root, extensions)
    role_map = build_class_map(files)

    # Collect all layer files for cross-feature check
    all_layer_files = [f for f in files if get_role(f.name) is not None]

    ida_files = [f for _, fl in role_map.items() for _, f in fl if get_role(f.name) == "idea"]
    prx_files = [f for _, fl in role_map.items() for _, f in fl if get_role(f.name) == "praxis"]
    poi_files = [f for _, fl in role_map.items() for _, f in fl if get_role(f.name) == "poiesis"]

    total_checked = len(ida_files) + len(prx_files) + len(poi_files)

    if total_checked == 0:
        print(f"[INFO] No ida_/prx_/poi_ files found under {root}")
        return 0

    # Stage 1: Idea layer - forbidden imports and API calls
    for f in ida_files:
        verify_idea_file(f, findings)

    # Stage 2: Reverse dependency checks (prx_ -> ida_, poi_ -> ida_/prx_)
    for f in prx_files:
        verify_reverse_dependencies(f, "praxis", role_map, findings)
    for f in poi_files:
        verify_reverse_dependencies(f, "poiesis", role_map, findings)

    # Stage 3: Cross-feature layer references
    for f in all_layer_files:
        role = get_role(f.name)
        if role:
            verify_cross_feature_references(f, role, all_layer_files, findings)

    # Stage 4: Red Flag heuristics (advisory)
    verify_red_flags(ida_files, prx_files, poi_files, findings)

    # Sort for deterministic output
    findings.sort(key=lambda x: (x["file"], x["line"], x["rule"]))

    # Deduplicate (same file+line+rule)
    seen = set()
    unique_findings = []
    for f in findings:
        key = (f["file"], f["line"], f["rule"])
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)
    findings = unique_findings

    # Console output
    errors = [f for f in findings if f["severity"] == "error"]

    if findings:
        print(f"\n{'='*60}")
        print(f"  comsect1 OOP Gate - {'FAILED' if errors else 'PASSED (with warnings)'}"
              f"  ({len(errors)} error(s), {len(findings) - len(errors)} warning(s))")
        print(f"{'='*60}")
        for f in findings:
            sev = "FAIL" if f["severity"] == "error" else "WARN"
            try:
                rel = Path(f["file"]).relative_to(root)
            except ValueError:
                rel = Path(f["file"]).name
            print(f"  [{sev}] {rel}:{f['line']}  [{f['rule']}]  {f['message']}")
        print()
    else:
        print(f"\n  comsect1 OOP Gate - PASSED  ({total_checked} file(s) verified, 0 violations)\n")

    # JSON report
    if report_path:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "root": str(root),
            "ida_files_checked": len(ida_files),
            "prx_files_checked": len(prx_files),
            "poi_files_checked": len(poi_files),
            "violation_count": len(errors),
            "warning_count": len(findings) - len(errors),
            "gate_passed": len(errors) == 0,
            "findings": findings,
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Report written: {report_path}\n")

    return 0 if not errors else 2

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="comsect1 OOP architecture gate (VB.NET / C#)"
    )
    parser.add_argument("-Root", required=True, help="Project root directory to scan")
    parser.add_argument("-Extensions", default=".vb,.cs",
                        help="Comma-separated file extensions (default: .vb,.cs)")
    parser.add_argument("-ReportPath", default=None, help="Path for JSON report output")
    args = parser.parse_args()

    root = Path(args.Root).resolve()
    if not root.is_dir():
        print(f"[ERROR] Root directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    extensions = {e.strip() if e.startswith(".") else f".{e.strip()}"
                  for e in args.Extensions.split(",")}
    report_path = Path(args.ReportPath).resolve() if args.ReportPath else None

    sys.exit(run(root, extensions, report_path))


if __name__ == "__main__":
    main()
