#!/usr/bin/env python3
"""Shared helpers for comsect1 gate verification scripts.

Provides constants, utilities, and analysis functions shared between
Verify-Comsect1Code.py (C/embedded) and Verify-OOPCode.py (OOP).
See: specs/11_checklist.md (Red Flags), v1.0.1 Layer Balance Invariant.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

MIN_IDA_LINES = 10
MIN_PRX_LINES_FOR_FAT_CHECK = 5
MIN_POI_WRAPPER_COUNT = 2

DOMAIN_CONDITIONAL_RE = re.compile(
    r"\b(?:if|switch|case)\b.*\b(?:mode|state|status|level|type|flag|enable|disable|active|threshold)\b",
    re.IGNORECASE,
)

# Detect Poi_ functions whose body is a single pass-through call to a Prx_ function.
# Matches: ReturnType Poi_Name(args) { [return] Prx_Name(args); }
# Excludes nested braces (complex bodies won't match).
_POI_WRAPPER_BODY_RE = re.compile(r"\bPoi_\w+\s*\([^()]*\)\s*\{([^{}]*)\}", re.DOTALL)
_PRX_SINGLE_CALL_RE = re.compile(r"^\s*(?:return\s+)?Prx_\w+\s*\([^;]*\)\s*;\s*$", re.DOTALL)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def resolve_repo_root(script_path: Path, repo_root_arg: str | None) -> Path:
    """Resolve the repository root from script location or explicit argument."""
    if repo_root_arg:
        return Path(repo_root_arg).resolve()
    return (script_path.parent / "..").resolve()


def add_finding(
    findings: list[dict[str, object]],
    severity: str,
    file_path: str | Path,
    line: int,
    rule: str,
    message: str,
) -> None:
    """Append a normalized finding dict (lowercase keys)."""
    findings.append({
        "severity": severity,
        "file": str(file_path),
        "line": line,
        "rule": rule,
        "message": message,
    })


def collect_source_files(root: Path, extensions: set[str]) -> list[Path]:
    """Recursively collect files matching given extensions."""
    files = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in extensions:
            files.append(p)
    return sorted(set(files))


def has_comsect1_boundary(root: Path) -> bool:
    """Return True when *root* is the dedicated comsect1 boundary or beneath it."""
    return any(part.lower() == "comsect1" for part in root.parts)


def validate_comsect1_root_boundary(root: Path) -> str | None:
    """Validate the dedicated /comsect1 root-folder convention.

    Downstream implementation gates must be pointed at the dedicated `comsect1`
    boundary (e.g. `codes/comsect1`) or at a nested architecture sub-root
    beneath that boundary (e.g. `codes/comsect1/embedded`).
    """
    if has_comsect1_boundary(root):
        return None
    return (
        "Root path must be the dedicated /comsect1 boundary or a nested "
        "architecture sub-root beneath it. "
        f"Current root does not contain a 'comsect1' path segment: {root}. "
        "Pass the /comsect1 directory itself, not the parent project or "
        "library root."
    )


def verify_folder_structure(
    root: Path,
    findings: list[dict[str, object]],
) -> None:
    """Check that the canonical comsect1 folder skeleton is present (Section 7.3, 7.5, 7.10).

    Applies to all comsect1 units regardless of language (C, OOP, or mixed).
    A2 invariants explicitly state folder structure rules are not relaxed for OOP.
    """
    def err(rule: str, message: str) -> None:
        add_finding(findings, "error", str(root), 1, rule, message)

    api_dir = root / "api"
    project_dir = root / "project"
    project_features_dir = root / "project" / "features"
    deps_middleware_dir = root / "deps" / "middleware"
    examples_inside = root / "examples"

    if not api_dir.is_dir():
        err("layout.required",
            f"Missing required /api public membrane: {api_dir}. "
            "Every comsect1 unit must expose its public interface through /api (Section 7.3).")

    if not project_dir.is_dir():
        err("layout.required",
            f"Missing required /project directory: {project_dir}.")

    if not project_features_dir.is_dir():
        err("layout.required",
            f"Missing required /project/features directory: {project_features_dir}.")

    if examples_inside.is_dir():
        err("layout.examples_misplaced",
            f"'examples/' must not reside inside the /comsect1 boundary: {examples_inside}. "
            "Move to project root (sibling of /comsect1). See Section 7.10.")

    if not api_dir.is_dir() and deps_middleware_dir.is_dir():
        for mdw_unit in sorted(deps_middleware_dir.iterdir()):
            if mdw_unit.is_dir():
                nested_api = mdw_unit / "api"
                if nested_api.is_dir():
                    err("layout.api-misplaced",
                        f"Public API found under deps/middleware/{mdw_unit.name}/api/ "
                        "but no root-level /api exists. "
                        "In a standalone middleware repo the public API must be at /api "
                        "(Section 7.3, Section 7.10, Section 13.4.2). "
                        "deps/middleware/<name>/api/ is the consumer project view of an "
                        "installed dependency -- not the standalone repo layout.")


def count_code_lines(
    path: Path,
    *,
    line_comment_prefixes: tuple[str, ...] = ("//",),
    skip_preprocessor: bool = False,
) -> int:
    """Count non-blank, non-comment lines.  Handles ``/* */`` block comments.

    Args:
        path: Source file to analyse.
        line_comment_prefixes: Prefixes that start a single-line comment
            (e.g. ``"//"`` for C/C#, ``"'"`` for VB.NET).
        skip_preprocessor: If True, skip lines starting with ``#``
            (C preprocessor directives).
    """
    count = 0
    in_block_comment = False
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                stripped = line.strip()
                if in_block_comment:
                    if "*/" in stripped:
                        in_block_comment = False
                    continue
                if stripped.startswith("/*"):
                    if "*/" not in stripped[2:]:
                        in_block_comment = True
                    continue  # single-line /* … */ also skipped
                if not stripped:
                    continue
                if any(stripped.startswith(p) for p in line_comment_prefixes):
                    continue
                if skip_preprocessor and stripped.startswith("#"):
                    continue
                count += 1
    except OSError:
        pass
    return count


# ---------------------------------------------------------------------------
# Layer Balance Invariant (v1.0.1, error severity)
# ---------------------------------------------------------------------------

def verify_layer_balance(
    ida_files: list[Path],
    poi_files: list[Path],
    findings: list[dict[str, object]],
    *,
    extract_feature: Callable[[Path], str | None],
    count_lines: Callable[[Path], int],
) -> None:
    """Check that ida_ contains domain decisions, not just pass-through.

    ida_ MUST contain domain decisions.  Empty forwarding-only ida_ paired
    with domain-semantic conditionals in poi_ is a structural violation equal
    in severity to dependency direction errors.
    """
    features: dict[str, dict[str, list[Path]]] = {}
    for f in ida_files:
        feat = extract_feature(f)
        if feat:
            key = feat.lower()
            features.setdefault(key, {"idea": [], "poiesis": []})
            features[key]["idea"].append(f)
    for f in poi_files:
        feat = extract_feature(f)
        if feat:
            key = feat.lower()
            features.setdefault(key, {"idea": [], "poiesis": []})
            features[key]["poiesis"].append(f)

    for _feat, roles in features.items():
        if not roles["idea"]:
            continue

        all_ida_empty = all(
            count_lines(f) < MIN_IDA_LINES for f in roles["idea"]
        )
        if not all_ida_empty:
            continue

        fat_poi_file: Path | None = None
        fat_poi_hits = 0
        for pf in roles["poiesis"]:
            try:
                text = pf.read_text(encoding="utf-8", errors="replace")
                hits = DOMAIN_CONDITIONAL_RE.findall(text)
                if hits:
                    fat_poi_file = pf
                    fat_poi_hits = len(hits)
                    break
            except OSError:
                continue

        if fat_poi_file is not None:
            for ida_file in roles["idea"]:
                code_lines = count_lines(ida_file)
                add_finding(
                    findings, "error", ida_file, 0, "layer-balance",
                    f"Layer Balance Invariant violation: ida_ has {code_lines} code line(s) "
                    f"while poi_ ({fat_poi_file.name}) contains {fat_poi_hits} "
                    "domain-semantic conditional(s). "
                    "ida_ must contain domain decisions -- "
                    "forwarding-only Idea is a structural violation.",
                )


# ---------------------------------------------------------------------------
# Red Flag heuristics (§11.8, advisory severity)
# ---------------------------------------------------------------------------

def verify_red_flags_common(
    ida_files: list[Path],
    prx_files: list[Path],
    poi_files: list[Path],
    findings: list[dict[str, object]],
    *,
    count_lines: Callable[[Path], int],
) -> None:
    """Three universal Red Flag checks: Empty Idea, Fat Poiesis, Fat Praxis.

    Language-specific red flags (e.g. OOP mutable-field check) are NOT
    included here -- each gate script adds its own extras after calling this.
    """
    # Red Flag: Empty Idea
    for f in ida_files:
        code_lines = count_lines(f)
        if code_lines < MIN_IDA_LINES:
            add_finding(
                findings, "warning", f, 0, "red-flag-empty-idea",
                f"Possible Empty Idea: only {code_lines} code line(s) "
                f"(threshold: {MIN_IDA_LINES}). "
                "Verify that domain logic is not in prx_/poi_.",
            )

    # Red Flag: Fat Poiesis
    for f in poi_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            hits = DOMAIN_CONDITIONAL_RE.findall(text)
            if hits:
                add_finding(
                    findings, "warning", f, 0, "red-flag-fat-poiesis",
                    f"Possible Fat Poiesis: poi_ contains {len(hits)} "
                    "domain-meaningful conditional(s). "
                    "Consider moving business logic to ida_ or prx_.",
                )
        except OSError:
            pass

    # Red Flag: Fat Praxis
    for f in prx_files:
        code_lines = count_lines(f)
        if code_lines >= MIN_PRX_LINES_FOR_FAT_CHECK:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
                if "PRX_EXISTENCE_CONDITION" in text:
                    continue  # documented type-coupling justification suppresses advisory
                hits = DOMAIN_CONDITIONAL_RE.findall(text)
                if not hits:
                    add_finding(
                        findings, "warning", f, 0, "red-flag-fat-praxis",
                        f"prx_ source has {code_lines} code lines but no "
                        "domain-semantic conditionals. "
                        "Praxis without domain interpretation may belong "
                        "in poi_ instead.",
                    )
            except OSError:
                pass

    # Red Flag: Poi Wrapper
    # poi_ functions that are pure single-call pass-throughs to prx_ indicate
    # that the ops table or callback registration should reference the prx_
    # function pointer directly rather than routing through a poi_ intermediary.
    for f in poi_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            wrapper_count = sum(
                1 for m in _POI_WRAPPER_BODY_RE.finditer(text)
                if _PRX_SINGLE_CALL_RE.match(m.group(1))
            )
            if wrapper_count >= MIN_POI_WRAPPER_COUNT:
                add_finding(
                    findings, "warning", f, 0, "red-flag-poi-wrapper",
                    f"poi_ contains {wrapper_count} function(s) that are pure "
                    "pass-throughs to prx_. "
                    "Register prx_ function pointers directly in the ops table "
                    "instead of wrapping them in poi_.",
                )
        except OSError:
            pass
