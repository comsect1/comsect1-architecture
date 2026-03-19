#!/usr/bin/env python3
"""
Verify-OOPCode.py - comsect1 Architecture Gate for OOP Languages (VB.NET / C#)

Checks all three architecture layers (ida_, prx_, poi_) for dependency direction
violations, forbidden imports, cross-feature reference violations, placement/path
rules, unit-qualified naming, module resource purity, service ownership, orphan
datastream detection, and dead shell detection.
Equivalent to Verify-Comsect1Code.py for C/C++ projects.

See: specs/A2_oop_adaptation.md (Appendix B)

Usage:
    python Verify-OOPCode.py -Root <comsect1_root> [-Extensions .vb,.cs] [-ReportPath <path>]

Exit codes:
    0 - Gate passed (no violations)
    2 - Gate failed (violations found)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

from comsect1_gate_helpers import (
    DOMAIN_CONDITIONAL_RE,
    add_finding,
    collect_source_files,
    count_code_lines as _count_code_lines,
    detect_unit_identity,
    requires_unit_qualification,
    stem_has_unit_suffix,
    validate_comsect1_root_boundary,
    verify_folder_structure,
    verify_layer_balance,
    verify_red_flags_common,
)

# ---------------------------------------------------------------------------
# Source file extensions to inspect
# ---------------------------------------------------------------------------
DEFAULT_EXTENSIONS = {".vb", ".cs"}

# OOP-specific code line counter: handle VB.NET single-quote comments
count_code_lines = partial(_count_code_lines, line_comment_prefixes=("//", "'"))

# ---------------------------------------------------------------------------
# Role detection: filename prefix -> architectural role (basic 3-layer)
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
# Extended role detection (§8.5 full prefix set)
# ---------------------------------------------------------------------------
_EXTENDED_ROLE_MAP: dict[str, tuple[str, bool]] = {
    # prefix -> (role_name, has_feature)
    "ida_": ("idea", True),
    "prx_": ("praxis", True),
    "poi_": ("poiesis", True),
    "cfg_": ("feature_cfg", True),
    "db_":  ("feature_db", True),
    "stm_": ("datastream", False),
    "svc_": ("service", False),
    "mdw_": ("middleware", False),
    "hal_": ("hal", False),
    "bsp_": ("bsp", False),
    "app_": ("app", False),
}

# Core variants
_CORE_NAMES_PREFIX = {
    "ida_core": "core_idea",
    "prx_core": "core_praxis",
    "poi_core": "core_poiesis",
}


def get_role_info_oop(
    file_name: str,
    unit_name: str | None = None,
) -> tuple[str, str | None]:
    """Extended role detection recognising all §8.5 prefixes.

    Returns (role, feature_or_none).  Invalid prefix ``inf_`` returns
    ``("invalid_prefix", None)``.
    """
    stem = Path(file_name).stem
    stem_lower = stem.lower()

    # Invalid prefix
    if stem_lower.startswith("inf_"):
        return "invalid_prefix", None

    # Core cfg
    core_cfg_names = {"cfg_core"}
    if unit_name:
        core_cfg_names.add(f"cfg_core_{unit_name}")
    if stem_lower in core_cfg_names:
        return "core_cfg", "core"

    # Core idea/prx/poi
    core_map: dict[str, str] = dict(_CORE_NAMES_PREFIX)
    if unit_name:
        core_map.update({
            f"ida_core_{unit_name}": "core_idea",
            f"poi_core_{unit_name}": "core_poiesis",
            f"prx_core_{unit_name}": "core_praxis",
        })
    if stem_lower in core_map:
        return core_map[stem_lower], "core"

    # Extended prefix scan
    for prefix, (role, has_feature) in _EXTENDED_ROLE_MAP.items():
        if stem_lower.startswith(prefix):
            feature = stem[len(prefix):] if has_feature else None
            return role, feature

    return "unknown", None


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
# OOP import/reference detection patterns
# ---------------------------------------------------------------------------

# C# using statements and VB.NET Imports — used to detect references to
# feature resource classes from module files.
_CS_USING_RE = re.compile(r"^\s*using\s+(?:static\s+)?(?P<ns>[A-Za-z_][\w.]*)\s*;")
_VB_IMPORTS_RE = re.compile(r"^\s*Imports\s+(?P<ns>[A-Za-z_][\w.]*)")

# OOP class/type reference pattern — word-boundary match on prefixed names
_OOP_TYPE_REF_RE = re.compile(r"\b(?:cfg_(?!core\b|Core\b)|db_|stm_)\w+")

# OOP method detection patterns for service ownership (C#/VB.NET)
_CS_METHOD_RE = re.compile(
    r"^\s*(?:public|internal|protected)\s+(?:static\s+)?(?:override\s+)?(?:async\s+)?"
    r"[\w<>\[\]?,\s]+\s+(?P<name>\w+)\s*\(",
    re.IGNORECASE,
)
_VB_METHOD_RE = re.compile(
    r"^\s*(?:Public|Friend|Protected)\s+(?:Shared\s+)?(?:Overrides\s+)?(?:Async\s+)?"
    r"(?:Sub|Function)\s+(?P<name>\w+)\s*\(",
    re.IGNORECASE,
)

# Detect thin delegation: method body is a single return/call line
_CS_SINGLE_DELEGATE_RE = re.compile(
    r"^\s*(?:return\s+)?(?P<callee>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*\([^;]*\)\s*;\s*$"
)
_VB_SINGLE_DELEGATE_RE = re.compile(
    r"^\s*(?:Return\s+)?(?P<callee>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*\([^)]*\)\s*$",
    re.IGNORECASE,
)

# Registry-like method names
_SVC_REGISTRY_NAME_RE = re.compile(r"\b(?:Register|RunTask|GetTask|GetUserPort|GetOps|SetOps)\b")


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


def extract_class_name(file_path: Path) -> str:
    """Extract the class/module name from filename by removing extension.
    e.g. ida_ColorConversion.vb -> ida_ColorConversion
    """
    return file_path.stem


def extract_feature_name(file_path: Path) -> str | None:
    """Extract the feature name for cross-feature reference checking.

    Three modes (bootstrap exemption first, then folder-based, then filename):
    0. Bootstrap exemption: files in /infra/bootstrap/ are core scope (§4.0),
       not features. Core files legitimately reference multiple features.
    1. Folder-based: if file is in .../features/<feature_name>/..., use folder name.
       Supports feature-scoped layouts where multiple layer files share a folder.
    2. Filename-based: extract from prefix (e.g. ida_Motor -> Motor).
       Fallback for flat layouts where each file IS a feature.

    Returns None if no recognized prefix or if it's a shared resource.
    """
    # Mode 0: Bootstrap core files are not features (§4.0 core scope)
    parts_lower = [p.lower() for p in file_path.parts]
    if "bootstrap" in parts_lower:
        return None

    # Mode 1: Folder-based feature identification (A2.5.7 feature-centric co-location)
    parts = file_path.parts
    for i, part in enumerate(parts):
        if part.lower() == "features" and i + 1 < len(parts):
            return parts[i + 1]

    # Mode 2: Filename-based (flat layout fallback)
    stem = file_path.stem.lower()
    for prefix in ROLE_PREFIXES:
        if stem.startswith(prefix):
            return file_path.stem[len(prefix):]
    return None


def is_shared_resource(file_path: Path) -> bool:
    """Return True if the file is a shared resource (cfg_, db_, stm_, svc_, etc.)."""
    name = file_path.name.lower()
    return any(name.startswith(prefix) for prefix in SHARED_RESOURCE_PREFIXES)


def _full_path(path_like: str | Path) -> str:
    return os.path.abspath(os.fspath(path_like))


def _test_is_under_path(path_like: str | Path, base_path: str | Path) -> bool:
    full = _full_path(path_like)
    base = _full_path(base_path)
    if not base.endswith(os.sep):
        base += os.sep
    return full.lower().startswith(base.lower())


def _test_contains_subpath(path_like: str | Path, subpath: str) -> bool:
    normalized_path = _full_path(path_like).replace("/", "\\")
    needle = subpath.replace("/", "\\")
    return needle.lower() in normalized_path.lower()


def _is_comment_line(stripped: str) -> bool:
    """Return True for obvious single-line comment starts (C# and VB.NET)."""
    return stripped.startswith("'") or stripped.startswith("//") or stripped.startswith("/*")


# ---------------------------------------------------------------------------
# Build reference maps for dependency direction checking
# ---------------------------------------------------------------------------

def build_class_map(files: list[Path]) -> dict[str, list[tuple[str, Path]]]:
    """Build mapping: role -> list of (class_name, file_path) for all recognized files."""
    role_map: dict[str, list[tuple[str, Path]]] = {"idea": [], "praxis": [], "poiesis": []}
    for f in files:
        role = get_role(f.name)
        if role and role in role_map:
            role_map[role].append((extract_class_name(f), f))
    return role_map


# ---------------------------------------------------------------------------
# Stage: Idea layer verification (forbidden imports/calls)
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
        for rule_id, regex in compiled_imports.items():
            if regex.search(line):
                _, msg = import_rules[rule_id]
                add_finding(findings, "error", file_path, line_no, rule_id,
                            f"Forbidden in ida_: {msg}")

        for rule_id, regex in compiled_calls.items():
            if regex.search(line):
                _, msg = IDA_FORBIDDEN_CALLS[rule_id]
                add_finding(findings, "error", file_path, line_no, rule_id,
                            f"Forbidden in ida_: {msg}")


# ---------------------------------------------------------------------------
# Stage: Reverse dependency checks (A2.3.2, A2.6.2, A2.6.3)
# ---------------------------------------------------------------------------

def verify_reverse_dependencies(file_path: Path, role: str, role_map: dict,
                                findings: list) -> None:
    """Check that prx_ does not reference ida_, and poi_ does not reference ida_/prx_."""
    if role not in ("praxis", "poiesis"):
        return

    if role == "praxis":
        forbidden_roles = ["idea"]
    else:  # poiesis
        forbidden_roles = ["idea", "praxis"]

    forbidden_names: list[tuple[str, str]] = []
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

    forbidden_patterns: list[tuple[re.Pattern, str, str]] = []
    for class_name, role_label in forbidden_names:
        own_name = extract_class_name(file_path)
        if class_name == own_name:
            continue
        pattern = re.compile(r"\b" + re.escape(class_name) + r"\b")
        forbidden_patterns.append((pattern, class_name, role_label))

    role_prefix = get_prefix(file_path.name)
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if _is_comment_line(stripped):
            continue

        for pattern, class_name, role_label in forbidden_patterns:
            if pattern.search(line):
                rule_id = f"{role_prefix}no-{role_label}-ref"
                add_finding(findings, "error", file_path, line_no, rule_id,
                            f"Reverse dependency: {role_prefix} references {class_name} ({role_label} layer)")


# ---------------------------------------------------------------------------
# Stage: Cross-feature layer reference check (A2.6.6)
# ---------------------------------------------------------------------------

def verify_cross_feature_references(file_path: Path, role: str, all_layer_files: list[Path],
                                    findings: list) -> None:
    """Check that feature layer files do not reference layer files from other features."""
    if is_shared_resource(file_path):
        return

    own_feature = extract_feature_name(file_path)
    if own_feature is None:
        return

    cross_feature_names: list[tuple[str, str]] = []
    for other_file in all_layer_files:
        if is_shared_resource(other_file):
            continue
        other_feature = extract_feature_name(other_file)
        if other_feature is None:
            continue
        if other_feature.lower() == own_feature.lower():
            continue
        other_role = get_role(other_file.name)
        if other_role:
            cross_feature_names.append((extract_class_name(other_file), other_feature))

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
        if _is_comment_line(stripped):
            continue

        for pattern, class_name, feature_name in cross_patterns:
            if pattern.search(line):
                add_finding(findings, "error", file_path, line_no, "cross-feature-layer-ref",
                            f"Cross-feature reference: references {class_name} from feature '{feature_name}' (use stm_ data plane)")


# ---------------------------------------------------------------------------
# Stage: Placement / path validation (A2.1 language-invariant)
# ---------------------------------------------------------------------------

def verify_placement(
    file_path: Path,
    role: str,
    feature: str | None,
    *,
    is_under_api: bool,
    is_under_any_bootstrap: bool,
    is_under_any_service: bool,
    is_under_any_project_features: bool,
    is_under_any_project_config: bool,
    is_under_any_project_datastreams: bool,
    is_under_deps_middleware: bool,
    is_under_deps_extern: bool,
    findings: list,
) -> None:
    """Per-file placement check (same canonical rules as C gate, A2.1 invariant)."""
    def err(rule: str, msg: str) -> None:
        add_finding(findings, "error", file_path, 1, rule, msg)

    if role == "core_idea" and not is_under_any_bootstrap:
        err("path.bootstrap", "ida_core must be located under /infra/bootstrap (root or nested architecture unit).")
    elif role == "core_poiesis" and not is_under_any_bootstrap:
        err("path.bootstrap", "poi_core must be located under /infra/bootstrap (root or nested architecture unit).")
    elif role == "core_praxis" and not is_under_any_bootstrap:
        err("path.bootstrap", "prx_core must be located under /infra/bootstrap (root or nested architecture unit).")
    elif role == "core_cfg" and not is_under_any_bootstrap:
        err("path.bootstrap", f"{file_path.name} must be located under /infra/bootstrap (root or nested architecture unit).")
    elif role == "service" and not is_under_any_service and not is_under_api:
        err("path.infra_service", "svc_* files must be located under /infra/service or /api.")
    elif role == "hal" and not is_under_api:
        err("path.infra_hal", "hal_* files must be located under /infra/platform/hal or /api.")
    elif role == "bsp" and not is_under_api:
        err("path.infra_bsp", "bsp_* files must be located under /infra/platform/bsp or /api.")
    elif role == "app" and not is_under_api:
        err("path.app", "app_* files must be located under /api.")
    elif role == "middleware" and not is_under_deps_middleware and not is_under_deps_extern and not is_under_api:
        err("path.deps_middleware", "mdw_* files must be located under /deps/middleware, /deps/extern, or /api.")
    elif role in ("idea", "praxis", "poiesis") and not is_under_any_project_features:
        err("path.project_feature", f"{file_path.stem.split('_')[0]}_ feature files must be located under /project/features (root or nested architecture unit).")
    elif role == "feature_cfg":
        if not is_under_any_project_features and not is_under_any_project_config:
            err("path.feature_resource", f"cfg_* feature files must be located under /project/features/ or /project/config/: {file_path.name}")
    elif role == "feature_db":
        if not is_under_any_project_features and not is_under_any_project_config:
            err("path.feature_resource", f"db_* feature files must be located under /project/features/ or /project/config/: {file_path.name}")
    elif role == "datastream" and not is_under_any_project_datastreams and not is_under_deps_middleware and not is_under_deps_extern:
        err("path.datastream", f"stm_* files must be located under /project/datastreams/, /deps/middleware/, or /deps/extern/: {file_path.name}")


# ---------------------------------------------------------------------------
# Stage: Unlisted prefix detection
# ---------------------------------------------------------------------------

def verify_unlisted_prefix(
    file_path: Path,
    role: str,
    *,
    is_architecture_managed: bool,
    findings: list,
) -> None:
    """Error on files with unknown prefix in architecture-managed paths."""
    if role == "unknown" and is_architecture_managed:
        add_finding(
            findings, "error", file_path, 1, "naming.prefix",
            f"Unknown architecture file role prefix: {file_path.name}",
        )


# ---------------------------------------------------------------------------
# Stage: Module resource purity
# ---------------------------------------------------------------------------

def verify_module_resource_purity(
    svc_files: list[Path],
    mdw_files: list[Path],
    findings: list,
) -> None:
    """svc_/mdw_ files must not import feature resources (cfg_<feature>, db_, stm_)."""
    for f in svc_files + mdw_files:
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        ext = f.suffix.lower()
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if _is_comment_line(stripped):
                continue
            # Check using/Imports statements
            if ext == ".cs":
                m = _CS_USING_RE.match(line)
            else:
                m = _VB_IMPORTS_RE.match(line)
            if m:
                ns = m.group("ns")
                # Check if namespace contains feature resource reference
                if _OOP_TYPE_REF_RE.search(ns):
                    add_finding(
                        findings, "error", f, line_no, "module.resource",
                        f"Module imports feature resource namespace '{ns}'. "
                        "svc_/mdw_ must not import feature cfg_/db_/stm_ resources.",
                    )
                    continue
            # Check class-name references in code
            if _OOP_TYPE_REF_RE.search(line):
                add_finding(
                    findings, "error", f, line_no, "module.resource",
                    "Module references a feature resource type (cfg_<feature>, db_, or stm_). "
                    "svc_/mdw_ must not access feature resources directly.",
                )
                break  # One error per file for class-name references


# ---------------------------------------------------------------------------
# Stage: Service ownership OOP
# ---------------------------------------------------------------------------

def verify_service_ownership_oop(
    svc_files: list[Path],
    findings: list,
) -> None:
    """OOP-specific service ownership checks (thin delegation, misclassified registry).

    NOT reusing C helper regex — OOP method syntax is fundamentally different.
    """
    for f in svc_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = text.splitlines()
        ext = f.suffix.lower()
        method_re = _CS_METHOD_RE if ext == ".cs" else _VB_METHOD_RE
        delegate_re = _CS_SINGLE_DELEGATE_RE if ext == ".cs" else _VB_SINGLE_DELEGATE_RE

        public_methods: list[tuple[str, int]] = []  # (name, line_no)
        thin_delegate_count = 0
        registry_count = 0

        # Scan for public/internal method declarations
        for line_no, line in enumerate(lines, start=1):
            m = method_re.match(line)
            if not m:
                continue
            name = m.group("name")
            public_methods.append((name, line_no))

            if _SVC_REGISTRY_NAME_RE.search(name):
                registry_count += 1

            # Look ahead for thin delegation (next non-blank, non-comment line)
            body_line = None
            for ahead in range(line_no, min(line_no + 5, len(lines))):
                ahead_stripped = lines[ahead].strip()
                if not ahead_stripped or _is_comment_line(ahead_stripped):
                    continue
                if ahead_stripped in ("{", "}", "End Sub", "End Function"):
                    continue
                body_line = ahead_stripped
                break

            if body_line and delegate_re.match(body_line):
                thin_delegate_count += 1
                add_finding(
                    findings, "error", f, line_no, "service.public-nonservice-delegate",
                    f"'{name}' is a thin service facade that delegates to a single call. "
                    "Public svc_ methods must own reusable computation or delegate only to service-private helpers.",
                )

        if public_methods and thin_delegate_count == len(public_methods):
            add_finding(
                findings, "error", f, 0, "service.file-facade",
                "All public methods in this svc_ file are thin pass-through delegates. "
                "This file is a facade membrane, not an owned service capability.",
            )

        if (
            len(public_methods) >= 2
            and registry_count >= max(2, (len(public_methods) + 1) // 2)
            and not DOMAIN_CONDITIONAL_RE.findall(text)
        ):
            add_finding(
                findings, "warning", f, 0, "service.misclassified-registry",
                "svc_ appears to be registry/dispatch code with little or no transform logic. "
                "Review whether this belongs in mdw_ or a core execution wrapper instead.",
            )


# ---------------------------------------------------------------------------
# Stage: Orphan datastream detection
# ---------------------------------------------------------------------------

def verify_orphan_datastreams(
    stm_files: list[Path],
    prx_files: list[Path],
    poi_files: list[Path],
    findings: list,
) -> None:
    """Advisory: warn when stm_ class is not referenced by any prx_/poi_ file."""
    if not stm_files:
        return

    # Collect all class-name references from prx_/poi_ files
    referenced_stems: set[str] = set()
    for pf in prx_files + poi_files:
        try:
            text = pf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Look for stm_ type references
        for m in re.finditer(r"\bstm_\w+", text, re.IGNORECASE):
            referenced_stems.add(m.group(0).lower())

    for stm_f in stm_files:
        stem_lower = stm_f.stem.lower()
        if stem_lower not in referenced_stems:
            add_finding(
                findings, "warning", stm_f, 1, "datastream.orphan",
                f"Datastream class '{stm_f.stem}' is not referenced by any prx_/poi_ source file. "
                "Verify it has active producers/consumers; remove if obsolete.",
            )


# ---------------------------------------------------------------------------
# Stage: Unit-qualified naming
# ---------------------------------------------------------------------------

def verify_unit_qualified_naming(
    file_path: Path,
    unit_name: str,
    *,
    is_under_any_bootstrap: bool,
    is_under_any_project_features: bool,
    is_under_any_project_config: bool,
    findings: list,
) -> None:
    """Enforce _<unit> suffix on files in /infra/bootstrap/, /project/features/, /project/config/."""
    if requires_unit_qualification(
        file_path.stem,
        is_under_any_bootstrap=is_under_any_bootstrap,
        is_under_any_project_features=is_under_any_project_features,
        is_under_any_project_config=is_under_any_project_config,
    ) and not stem_has_unit_suffix(file_path.stem, unit_name):
        add_finding(
            findings, "error", file_path, 1, "naming.unit_qualified",
            f"Internal /infra and /project files must use the unit-qualified suffix _{unit_name}: {file_path.name}",
        )


# ---------------------------------------------------------------------------
# Stage: Dead shell detection
# ---------------------------------------------------------------------------

def verify_dead_shells(
    svc_files: list[Path],
    findings: list,
) -> None:
    """Error on svc_ files with <3 code lines."""
    for f in svc_files:
        code_lines = count_code_lines(f)
        if code_lines < 3:
            add_finding(
                findings, "error", f, 1, "structure.dead_shell",
                f"Service file contains only {code_lines} code line(s). Remove empty shell files.",
            )


# ---------------------------------------------------------------------------
# Red Flag heuristics: OOP-specific (A2.8.2)
# ---------------------------------------------------------------------------

# Feature resource reference inside ida_ files (A2.6.4)
FEATURE_RESOURCE_RE = re.compile(
    r"\b(?:cfg_(?!core\b|Core\b)|db_|stm_)\w+",
)

# Mutable instance field: C# (A2.6.5)
CS_MUTABLE_FIELD_RE = re.compile(
    r"^\s*(?:private|public|protected|internal)(?:\s+(?!static\b|readonly\b|const\b)\w+)*\s+\w[\w<>\[\]?,\s]*\s+\w+\s*[;={]",
    re.IGNORECASE,
)

# Mutable instance field: VB.NET (A2.6.5)
VB_MUTABLE_FIELD_RE = re.compile(
    r"^\s*(?:Private|Public|Protected|Friend)(?:\s+(?!Shared\b|ReadOnly\b|Const\b)\w+)*\s+Dim\s+\w+",
    re.IGNORECASE,
)


def verify_red_flags_oop(ida_files: list[Path], findings: list) -> None:
    """OOP-specific Red Flag checks (A2.8.2): feature resource access and mutable fields."""
    for f in ida_files:
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if _is_comment_line(stripped):
                continue
            if FEATURE_RESOURCE_RE.search(line):
                add_finding(findings, "warning", f, line_no, "red-flag-ida-feature-resource",
                            "Possible self-containment violation: ida_ references a feature resource "
                            "(cfg_<feature>, db_, or stm_). Only cfg_core is allowed in ida_. "
                            "Move resource access to prx_ or poi_.")
                break

    for f in ida_files:
        ext = f.suffix.lower()
        mutable_re = CS_MUTABLE_FIELD_RE if ext == ".cs" else VB_MUTABLE_FIELD_RE
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if _is_comment_line(stripped):
                continue
            if mutable_re.search(line):
                add_finding(findings, "warning", f, line_no, "red-flag-ida-mutable-field",
                            "Possible purity violation: ida_ may declare a mutable instance field. "
                            "Idea must be immutable (A2.5.1). Use static methods or readonly/const fields.")
                break


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run(root: Path, extensions: set[str], report_path: Path | None) -> int:
    findings: list[dict] = []

    # --- Stage 1: Root boundary validation ---
    root_boundary_issue = validate_comsect1_root_boundary(root)
    if root_boundary_issue:
        add_finding(findings, "error", root, 1, "layout.root_boundary", root_boundary_issue)

    # --- Stage 2: Folder structure validation ---
    verify_folder_structure(root, findings)

    # --- Stage 3: Unit identity detection ---
    unit_identity = detect_unit_identity(root, header_extensions=extensions)
    unit_name = unit_identity.get("resolved_unit")
    if not isinstance(unit_name, str):
        unit_name = None

    # --- Stage 4: File collection + extended role detection ---
    files = collect_source_files(root, extensions)
    _deps_dir = root / "deps"
    if _deps_dir.exists():
        files = [f for f in files if not f.is_relative_to(_deps_dir)]
    role_map = build_class_map(files)

    all_layer_files = [f for f in files if get_role(f.name) is not None]

    ida_files = [f for _, fl in role_map.items() for _, f in fl if get_role(f.name) == "idea"]
    prx_files = [f for _, fl in role_map.items() for _, f in fl if get_role(f.name) == "praxis"]
    poi_files = [f for _, fl in role_map.items() for _, f in fl if get_role(f.name) == "poiesis"]

    # Extended file groups
    svc_files = [f for f in files if f.stem.lower().startswith("svc_")]
    mdw_files = [f for f in files if f.stem.lower().startswith("mdw_")]
    stm_files = [f for f in files if f.stem.lower().startswith("stm_")]

    total_checked = len(ida_files) + len(prx_files) + len(poi_files)

    # Canonical directory references
    api_dir = root / "api"
    infra_bootstrap_dir = root / "infra" / "bootstrap"
    infra_service_dir = root / "infra" / "service"
    project_features_dir = root / "project" / "features"
    project_config_dir = root / "project" / "config"
    project_datastreams_dir = root / "project" / "datastreams"
    deps_middleware_dir = root / "deps" / "middleware"
    deps_extern_dir = root / "deps" / "extern"

    # --- Stage 5: Per-file placement + unlisted prefix + unit-qualified naming ---
    for file in files:
        full_file_path = _full_path(file)
        is_under_api = _test_is_under_path(full_file_path, api_dir)
        is_under_bootstrap = _test_is_under_path(full_file_path, infra_bootstrap_dir)
        is_under_service = _test_is_under_path(full_file_path, infra_service_dir)
        is_under_project_features = _test_is_under_path(full_file_path, project_features_dir)
        is_under_project_config = _test_is_under_path(full_file_path, project_config_dir)
        is_under_project_datastreams = _test_is_under_path(full_file_path, project_datastreams_dir)
        is_under_deps_middleware = _test_is_under_path(full_file_path, deps_middleware_dir)
        is_under_deps_extern = _test_is_under_path(full_file_path, deps_extern_dir)

        is_nested_deps_unit = is_under_deps_extern or is_under_deps_middleware
        has_infra_bootstrap_segment = _test_contains_subpath(full_file_path, "\\infra\\bootstrap\\")
        has_infra_service_segment = _test_contains_subpath(full_file_path, "\\infra\\service\\")
        has_project_features_segment = _test_contains_subpath(full_file_path, "\\project\\features\\")
        has_project_config_segment = _test_contains_subpath(full_file_path, "\\project\\config\\")
        has_project_datastreams_segment = _test_contains_subpath(full_file_path, "\\project\\datastreams\\")

        is_under_any_bootstrap = is_under_bootstrap or (is_nested_deps_unit and has_infra_bootstrap_segment)
        is_under_any_service = is_under_service or (is_nested_deps_unit and has_infra_service_segment)
        is_under_any_project_features = is_under_project_features or (
            is_nested_deps_unit and has_project_features_segment
        )
        is_under_any_project_config = is_under_project_config or (
            is_nested_deps_unit and has_project_config_segment
        )
        is_under_any_project_datastreams = is_under_project_datastreams or (
            is_nested_deps_unit and has_project_datastreams_segment
        )

        role, feature = get_role_info_oop(file.name, unit_name)

        # Invalid prefix
        if role == "invalid_prefix":
            add_finding(
                findings, "error", file, 1, "naming.prefix",
                "Invalid role prefix 'inf_'. Keep role prefixes (ida_/prx_/poi_/mdw_/svc_/hal_/bsp_/stm_/cfg_/db_).",
            )
            continue

        # Unit-qualified naming
        if unit_name:
            verify_unit_qualified_naming(
                file, unit_name,
                is_under_any_bootstrap=is_under_any_bootstrap,
                is_under_any_project_features=is_under_any_project_features,
                is_under_any_project_config=is_under_any_project_config,
                findings=findings,
            )

        # Unlisted prefix
        is_architecture_managed = (
            is_under_project_features or is_under_project_config or is_under_project_datastreams
            or is_under_bootstrap or is_under_service or is_under_api
        )
        verify_unlisted_prefix(file, role, is_architecture_managed=is_architecture_managed, findings=findings)
        if role == "unknown":
            continue

        # Placement
        verify_placement(
            file, role, feature,
            is_under_api=is_under_api,
            is_under_any_bootstrap=is_under_any_bootstrap,
            is_under_any_service=is_under_any_service,
            is_under_any_project_features=is_under_any_project_features,
            is_under_any_project_config=is_under_any_project_config,
            is_under_any_project_datastreams=is_under_any_project_datastreams,
            is_under_deps_middleware=is_under_deps_middleware,
            is_under_deps_extern=is_under_deps_extern,
            findings=findings,
        )

    if total_checked == 0:
        if findings:
            errors = [f for f in findings if f["severity"] == "error"]
            print(f"\n{'='*60}")
            print(f"  comsect1 OOP Gate - FAILED  ({len(errors)} error(s), 0 warning(s))")
            print(f"{'='*60}")
            for f in findings:
                sev = "FAIL" if f["severity"] == "error" else "WARN"
                try:
                    rel = Path(f["file"]).relative_to(root)
                except ValueError:
                    rel = Path(f["file"]).name
                print(f"  [{sev}] {rel}:{f['line']}  [{f['rule']}]  {f['message']}")
            print()
            print(f"Gate FAILED -- {len(errors)} error(s) must be resolved.")
            return 2
        print(f"[INFO] No ida_/prx_/poi_ files found under {root}")
        return 0

    # --- Stage 6: Idea forbidden imports/calls ---
    for f in ida_files:
        verify_idea_file(f, findings)

    # --- Stage 7: Reverse dependency checks ---
    for f in prx_files:
        verify_reverse_dependencies(f, "praxis", role_map, findings)
    for f in poi_files:
        verify_reverse_dependencies(f, "poiesis", role_map, findings)

    # --- Stage 8: Cross-feature layer references ---
    for f in all_layer_files:
        role = get_role(f.name)
        if role:
            verify_cross_feature_references(f, role, all_layer_files, findings)

    # --- Stage 9: Module resource purity ---
    verify_module_resource_purity(svc_files, mdw_files, findings)

    # --- Stage 10: Service ownership OOP ---
    verify_service_ownership_oop(svc_files, findings)

    # --- Stage 11: Orphan datastream detection ---
    verify_orphan_datastreams(stm_files, prx_files, poi_files, findings)

    # --- Stage 12: Dead shell detection ---
    verify_dead_shells(svc_files, findings)

    # --- Stage 13: Layer Balance Invariant ---
    verify_layer_balance(
        ida_files, poi_files, findings,
        extract_feature=extract_feature_name, count_lines=count_code_lines,
    )

    # --- Stage 14: Red Flag heuristics ---
    verify_red_flags_common(
        ida_files, prx_files, poi_files, findings,
        count_lines=count_code_lines,
        extract_feature=extract_feature_name,
    )
    verify_red_flags_oop(ida_files, findings)

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

    warnings = [f for f in findings if f["severity"] == "warning"]
    if errors:
        print(f"Gate FAILED -- {len(errors)} error(s) must be resolved.")
    elif warnings:
        print(f"Gate passed -- {len(warnings)} advisory warning(s) for review.")
    else:
        print("Gate passed -- no issues found.")

    # JSON report
    if report_path:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "root": str(root),
            "ida_files_checked": len(ida_files),
            "prx_files_checked": len(prx_files),
            "poi_files_checked": len(poi_files),
            "svc_files_checked": len(svc_files),
            "stm_files_checked": len(stm_files),
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
    parser.add_argument("-Root", required=True, help="Dedicated comsect1 root directory to scan")
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
