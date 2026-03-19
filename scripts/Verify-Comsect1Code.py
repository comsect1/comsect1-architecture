#!/usr/bin/env python3
"""Verify comsect1 code layout and dependency rules."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from functools import partial
from pathlib import Path

from comsect1_gate_helpers import (
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
    verify_service_ownership_common,
)

SOURCE_EXTENSIONS = {".c", ".h", ".cpp", ".hpp"}
INCLUDE_REGEX = re.compile(r'^\s*#\s*include\s*[<"](?P<path>[^">]+)[">]')
SYSTEM_INCLUDE_REGEX = re.compile(r"^\s*#\s*include\s*<")
PLATFORM_PATH_SEGMENT_RE = re.compile(r"(^|[\\/])(?:cmsis|vendor|device|board|boards?|bsp|port|ports)([\\/]|$)", re.IGNORECASE)
PLATFORM_PORT_SEGMENT_RE = re.compile(r"(^|[\\/])ports?([\\/]|$)", re.IGNORECASE)
BOARD_INCLUDE_LEAF_RE = re.compile(r"^(?:bsp_|board_)", re.IGNORECASE)
LEGACY_PLATFORM_BUILD_PATH_RE = re.compile(r"(^|[\\/])(?:platform|ports?)([\\/]|$)", re.IGNORECASE)
BUILD_FILE_PATTERNS = ("CMakeLists.txt", "*.cmake", "Makefile", "makefile", "*.mk")
BUILD_SKIP_DIRS = {".git", ".hg", ".svn", ".cmakebuild", "build", "out", "dist", "node_modules", ".venv", "venv", "__pycache__"}
BUILD_EVIDENCE_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "macro-branch",
        re.compile(r"\b(?:if|elseif)\s*\(.*(?:mcu|bsp|board|device|cmsis|vendor)[A-Za-z0-9_/-]*", re.IGNORECASE),
        "MCU/BSP conditional branch",
    ),
    (
        "compile-def",
        re.compile(r"\b(?:add_definitions|add_compile_definitions|target_compile_definitions)\b.*(?:mcu|bsp|board|device|cmsis|vendor)[A-Za-z0-9_/-]*", re.IGNORECASE),
        "MCU/BSP compile definition",
    ),
    (
        "target-link",
        re.compile(r"\btarget_link_libraries\b.*(?:bsp|board|cmsis|vendor|device|hal)[A-Za-z0-9_./\\-]*", re.IGNORECASE),
        "BSP/platform target link",
    ),
    (
        "include-path",
        re.compile(r"\b(?:include_directories|target_include_directories|include)\b.*(?:bsp|board|cmsis|vendor|device|platform[\\/](?:hal|bsp)|[\\/]ports?[\\/])", re.IGNORECASE),
        "BSP/platform include path",
    ),
    (
        "dummy-fallback",
        re.compile(r"\b(?:dummy|fallback)\b", re.IGNORECASE),
        "dummy or fallback platform wiring",
    ),
)
PLATFORM_SYMBOL_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("peripheral", re.compile(r"\bNVIC_[A-Za-z0-9_]+\b"), "NVIC interrupt primitive"),
    ("peripheral", re.compile(r"\bPORT_REGS\b"), "PORT_REGS device register"),
    ("peripheral", re.compile(r"\bSERCOM_[A-Za-z0-9_]*\b"), "SERCOM peripheral symbol"),
    ("peripheral", re.compile(r"\b__WFI\b"), "__WFI power primitive"),
    ("board", re.compile(r"\bBOARD_[A-Za-z0-9_]+\b"), "board macro or constant"),
    ("board", re.compile(r"\bBsp_[A-Za-z0-9_]+\b"), "BSP API"),
    (
        "board",
        re.compile(r"\bBoard_(?:Timer|Clock|Pin|Gpio|GPIO|Init|Boot|Uart|UART|Spi|SPI|I2c|I2C|Sercom|SERCOM)[A-Za-z0-9_]*\b"),
        "board-owned hardware API",
    ),
)

# C-specific code line counter: skip preprocessor directives
count_code_lines = partial(_count_code_lines, line_comment_prefixes=("//",), skip_preprocessor=True)

# Function-level naming checks for service layer
SVC_EXPORT_FUNC_RE = re.compile(r"^(?!static\b)\w[\w\s\*]*?\b(\w+)\s*\(")
SVC_HEADER_FUNC_DECL_RE = re.compile(r"^(?!static\b)\w[\w\s\*]*?\b(\w+)\s*\(.*\)\s*;")


def full_path(path_like: str | Path) -> str:
    return os.path.abspath(os.fspath(path_like))


def get_role_info(file_name: str, unit_name: str | None = None) -> tuple[str, str | None]:
    stem = Path(file_name).stem

    if re.match(r"^inf_", stem):
        return "invalid_prefix", None

    core_cfg_names = {"cfg_core"}
    core_map: dict[str, str] = {
        "ida_core": "core_idea",
        "poi_core": "core_poiesis",
        "prx_core": "core_praxis",
    }

    if unit_name:
        core_cfg_names.add(f"cfg_core_{unit_name}")
        core_map.update(
            {
                f"ida_core_{unit_name}": "core_idea",
                f"poi_core_{unit_name}": "core_poiesis",
                f"prx_core_{unit_name}": "core_praxis",
            }
        )

    if stem in core_cfg_names:
        return "core_cfg", "core"
    if stem in core_map:
        return core_map[stem], "core"

    m = re.match(r"^(?P<p>ida|prx|poi|cfg|db)_(?P<f>.+)$", stem)
    if m:
        role_map = {
            "ida": "idea",
            "prx": "praxis",
            "poi": "poiesis",
            "cfg": "feature_cfg",
            "db": "feature_db",
        }
        return role_map[m.group("p")], m.group("f")

    if re.match(r"^svc_", stem):
        return "service", None
    if re.match(r"^mdw_", stem):
        return "middleware", None
    if re.match(r"^hal_", stem):
        return "hal", None
    if re.match(r"^bsp_", stem):
        return "bsp", None
    if re.match(r"^stm_", stem):
        return "datastream", None
    if re.match(r"^app_", stem):
        return "app", None

    return "unknown", None


def get_includes(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    return get_includes_from_text(text)


def get_includes_from_text(text: str) -> list[dict[str, object]]:
    includes: list[dict[str, object]] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        line = line.lstrip("\ufeff")
        m = INCLUDE_REGEX.match(line)
        if not m:
            continue
        include_path = m.group("path")
        includes.append(
            {
                "Line": idx,
                "IncludePath": include_path,
                "Leaf": os.path.basename(include_path),
                "Raw": line.rstrip("\n"),
            }
        )
    return includes


def test_is_under_path(path_like: str | Path, base_path: str | Path) -> bool:
    full = full_path(path_like)
    base = full_path(base_path)
    if not base.endswith(os.sep):
        base += os.sep
    return full.lower().startswith(base.lower())


def test_contains_subpath(path_like: str | Path, subpath: str) -> bool:
    normalized_path = full_path(path_like).replace("/", "\\")
    needle = subpath.replace("/", "\\")
    return needle.lower() in normalized_path.lower()


def get_feature_from_path(path_like: str | Path) -> str | None:
    normalized = full_path(path_like).replace("/", "\\")
    m = re.search(r"[\\/]project[\\/]features[\\/](?P<feature>[^\\/]+)", normalized)
    return m.group("feature") if m else None


def test_is_same_feature_header(leaf: str, prefix: str, feature: str | None) -> bool:
    if not feature:
        return False
    stem = Path(leaf).stem.lower()
    base = f"{prefix}_{feature}".lower()
    return stem == base or stem.startswith(base + "_")


def test_is_same_feature_include(
    leaf: str,
    prefix: str,
    feature: str | None,
    header_feature_owners: dict[str, set[str]],
) -> bool:
    if not feature:
        return False
    if leaf in header_feature_owners:
        return feature in header_feature_owners[leaf]
    return test_is_same_feature_header(leaf=leaf, prefix=prefix, feature=feature)


_VALID_API_ROLE_PREFIXES = {"app", "mdw", "hal", "svc", "bsp"}


def extract_api_unit(header_name: str) -> str | None:
    stem = Path(header_name).stem
    if "_" in stem:
        prefix, remainder = stem.split("_", 1)
        if prefix.lower() in _VALID_API_ROLE_PREFIXES and remainder:
            return remainder.lower()
        return None
    return stem.lower() if stem else None


# detect_unit_identity is imported from comsect1_gate_helpers








def write_json_no_bom(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# stem_has_unit_suffix and requires_unit_qualification are imported from comsect1_gate_helpers


def discover_repo_root(root_path: Path, repo_root_arg: str | None) -> Path:
    if repo_root_arg:
        return Path(repo_root_arg).resolve()

    for candidate in [root_path, *root_path.parents]:
        if any((candidate / name).is_file() for name in ("CMakeLists.txt", "Makefile", "makefile")):
            return candidate
    return root_path


def collect_build_evidence(repo_root: Path) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    seen_files: set[Path] = set()

    for pattern in BUILD_FILE_PATTERNS:
        for path in repo_root.rglob(pattern):
            if not path.is_file():
                continue
            if path in seen_files:
                continue
            if any(part.lower() in BUILD_SKIP_DIRS for part in path.parts):
                continue
            seen_files.add(path)
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue

            for line_no, line in enumerate(lines, start=1):
                for kind, regex, message in BUILD_EVIDENCE_RULES:
                    if regex.search(line):
                        evidence.append(
                            {
                                "file": path,
                                "line": line_no,
                                "kind": kind,
                                "message": message,
                                "text": line.strip().lstrip("\ufeff"),
                            }
                        )
    return evidence


def detect_platform_include_evidence(include_path: str, leaf: str) -> tuple[str, str] | None:
    normalized = include_path.replace("\\", "/")
    lower_path = normalized.lower()
    lower_leaf = leaf.lower()

    if lower_leaf.startswith("bsp_") or BOARD_INCLUDE_LEAF_RE.search(lower_leaf):
        return ("board", f"direct board/BSP include: {include_path}")
    if PLATFORM_PATH_SEGMENT_RE.search(normalized):
        category = (
            "board"
            if re.search(r"(^|/)(?:board|boards?|bsp|port|ports)(/|$)", lower_path)
            else "peripheral"
        )
        return (category, f"raw platform include path: {include_path}")
    return None


def collect_platform_evidence(
    includes: list[dict[str, object]],
    text: str,
) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []

    for inc in includes:
        include_path = str(inc["IncludePath"])
        leaf = str(inc["Leaf"])
        detected = detect_platform_include_evidence(include_path, leaf)
        if not detected:
            continue
        category, message = detected
        evidence.append(
            {
                "line": int(inc["Line"]),
                "category": category,
                "message": message,
            }
        )

    for category, regex, message in PLATFORM_SYMBOL_RULES:
        for match in regex.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            evidence.append(
                {
                    "line": line_no,
                    "category": category,
                    "message": message,
                }
            )

    return evidence


def is_platform_declared_role(role: str) -> bool:
    return role in {"hal", "bsp"}


def has_legacy_platform_build_path(text: str) -> bool:
    normalized = text.replace("\\", "/")
    return bool(
        re.search(r"(^|[\s\"'(<:=])(?:platform|ports?)/", normalized, re.IGNORECASE)
        or re.search(r"/(?:platform|ports?)(/|$)", normalized, re.IGNORECASE)
        or PLATFORM_PORT_SEGMENT_RE.search(normalized)
        or LEGACY_PLATFORM_BUILD_PATH_RE.search(normalized)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify comsect1 code architecture rules.")
    parser.add_argument("-Root", dest="root", required=True, help="Dedicated comsect1 root directory to scan")
    parser.add_argument("-RepoRoot", dest="repo_root", default=None, help="Repository/project root for build evidence scanning")
    parser.add_argument("-JsonOut", dest="json_out", default=None)
    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    if not root_path.is_dir():
        raise RuntimeError(f"Root folder not found: {root_path}")

    repo_root = discover_repo_root(root_path, args.repo_root)
    unit_identity = detect_unit_identity(root_path)
    unit_name = unit_identity.get("resolved_unit")
    if not isinstance(unit_name, str):
        unit_name = None

    findings: list[dict[str, object]] = []

    def err(file_path: str | Path, line: int, rule: str, message: str) -> None:
        add_finding(findings, "error", file_path, line, rule, message)

    def warn(file_path: str | Path, line: int, rule: str, message: str) -> None:
        add_finding(findings, "warning", file_path, line, rule, message)

    root_boundary_issue = validate_comsect1_root_boundary(root_path)
    if root_boundary_issue:
        err(str(root_path), 1, "layout.root_boundary", root_boundary_issue)

    api_dir = root_path / "api"
    infra_bootstrap_dir = root_path / "infra" / "bootstrap"
    infra_service_dir = root_path / "infra" / "service"
    infra_hal_dir = root_path / "infra" / "platform" / "hal"
    infra_bsp_dir = root_path / "infra" / "platform" / "bsp"
    deps_root_dir = root_path / "deps"
    deps_extern_dir = root_path / "deps" / "extern"
    deps_middleware_dir = root_path / "deps" / "middleware"
    project_features_dir = root_path / "project" / "features"
    project_config_dir = root_path / "project" / "config"
    project_datastreams_dir = root_path / "project" / "datastreams"

    if not infra_bootstrap_dir.is_dir():
        err(str(root_path), 1, "layout.required", f"Missing required infra bootstrap path: {infra_bootstrap_dir}")
    if not deps_root_dir.is_dir():
        err(str(root_path), 1, "layout.required", f"Missing required dependency repository path: {deps_root_dir}")

    api_units = unit_identity["api_units"]
    project_units = unit_identity["project_units"]
    api_headers = unit_identity["api_headers"]
    if api_dir.is_dir() and not api_headers:
        err(api_dir, 1, "naming.api_anchor", "Missing valid API identity anchor under /api. Use app_<unit>.h or <role>_<unit>.h.")
    if len(api_units) > 1:
        err(api_dir, 1, "naming.unit_conflict", f"Multiple API unit identifiers detected under /api: {sorted(api_units)}")
    if len(project_units) > 1:
        err(project_config_dir, 1, "naming.unit_conflict", f"Multiple cfg_project_<unit>.h anchors detected: {sorted(project_units)}")
    if api_units and project_units and api_units != project_units:
        err(project_config_dir, 1, "naming.anchor_mismatch", f"API anchor unit(s) {sorted(api_units)} do not match cfg_project anchor unit(s) {sorted(project_units)}")

    # Unit-aware core file name sets — strictly one mode: qualified when unit known, legacy when not
    if unit_name:
        cfg_core_names: set[str] = {f"cfg_core_{unit_name}.h"}
        ida_core_names: set[str] = {f"ida_core_{unit_name}.h"}
        poi_core_names: set[str] = {f"poi_core_{unit_name}.h"}
        prx_core_names: set[str] = {f"prx_core_{unit_name}.h"}
    else:
        cfg_core_names: set[str] = {"cfg_core.h"}
        ida_core_names: set[str] = {"ida_core.h"}
        poi_core_names: set[str] = {"poi_core.h"}
        prx_core_names: set[str] = {"prx_core.h"}
    core_config_names = cfg_core_names

    expected_core_cfg = f"cfg_core_{unit_name}.h" if unit_name else "cfg_core.h"
    top_level_core_contract_header = infra_bootstrap_dir / expected_core_cfg
    if not top_level_core_contract_header.is_file():
        err(str(root_path), 1, "layout.required", f"Missing required Core Contract header: {top_level_core_contract_header}")

    core_config_dir = root_path / "core" / "config"
    if core_config_dir.is_dir():
        err(str(root_path), 1, "layout.legacy", f"Legacy core config folder detected. Migrate to /infra/bootstrap/{expected_core_cfg}: {core_config_dir}")

    project_config_names: set[str] = set()
    if project_config_dir.is_dir():
        for header in project_config_dir.glob("*.h"):
            if header.is_file():
                project_config_names.add(header.name)
        expected_project_cfg = f"cfg_project_{unit_name}.h" if unit_name else "cfg_project.h"
        if expected_project_cfg not in project_config_names:
            err(str(project_config_dir), 1, "layout.required",
                f"Missing required project target interface header: {project_config_dir / expected_project_cfg}")
        # §8.6: Main project must establish unit identity via cfg_project_<unit>.h
        # When unit_name is None and api/ is absent, this is a main project without an anchor —
        # cfg_project.h alone is insufficient; the gate cannot infer the unit name.
        if unit_name is None and "cfg_project.h" in project_config_names:
            err(str(project_config_dir), 1, "naming.missing_unit_anchor",
                "Main project identity anchor missing (§8.6). "
                "Rename cfg_project.h to cfg_project_<unit>.h "
                "(e.g. cfg_project_demo.h) to enable unit-qualified naming.")
    else:
        err(str(root_path), 1, "layout.required", f"Missing required project config folder: {project_config_dir}")

    legacy_features_dir = root_path / "features"
    if legacy_features_dir.is_dir():
        err(str(root_path), 1, "layout.legacy", f"Legacy features folder detected. Migrate to /project/features/: {legacy_features_dir}")

    legacy_modules_dir = root_path / "modules"
    if legacy_modules_dir.is_dir():
        err(str(root_path), 1, "layout.legacy", f"Legacy modules folder detected. Migrate to /infra/ and /deps/: {legacy_modules_dir}")

    legacy_platform_dir = root_path / "platform"
    if legacy_platform_dir.is_dir():
        err(str(root_path), 1, "layout.legacy", f"Legacy platform folder detected. Migrate to /infra/platform/: {legacy_platform_dir}")

    # --- Comprehensive folder tree checks (Section 7.3, 7.5, 7.10) ---
    verify_folder_structure(root_path, findings)

    source_files = collect_source_files(root_path, SOURCE_EXTENSIONS)
    # Exclude deps/ — external dependency code is verified by its own gate.
    # The consumer project gate checks only project-owned code (project/ and infra/).
    # deps/ is a Dependency Repository (§7.3), not project-owned code.
    source_files = [
        f for f in source_files
        if not test_is_under_path(f, deps_root_dir)
    ]
    if not source_files:
        err(str(root_path), 1, "layout.required", f"No source files found under: {root_path}")

    build_evidence = collect_build_evidence(repo_root)

    header_feature_owners: dict[str, set[str]] = {}
    for candidate in source_files:
        if candidate.suffix.lower() not in {".h", ".hpp"}:
            continue
        owner_feature = get_feature_from_path(candidate)
        if not owner_feature:
            continue
        header_feature_owners.setdefault(candidate.name, set()).add(owner_feature)

    project_resource_header_names: set[str] = set()
    for candidate in source_files:
        if candidate.suffix.lower() not in {".h", ".hpp"}:
            continue
        candidate_role, _ = get_role_info(candidate.name, unit_name)
        if candidate_role not in {"feature_cfg", "feature_db", "datastream"}:
            continue

        candidate_path = full_path(candidate)
        candidate_is_under_project_features = test_is_under_path(candidate_path, project_features_dir)
        candidate_is_under_project_config = test_is_under_path(candidate_path, project_config_dir)
        candidate_is_under_project_datastreams = test_is_under_path(candidate_path, project_datastreams_dir)
        candidate_is_under_deps_extern = test_is_under_path(candidate_path, deps_extern_dir)
        candidate_is_under_deps_middleware = test_is_under_path(candidate_path, deps_middleware_dir)
        candidate_is_nested_deps_unit = candidate_is_under_deps_extern or candidate_is_under_deps_middleware

        candidate_has_project_features_segment = test_contains_subpath(candidate_path, "\\\\project\\\\features\\\\")
        candidate_has_project_config_segment = test_contains_subpath(candidate_path, "\\\\project\\\\config\\\\")
        candidate_has_project_datastreams_segment = test_contains_subpath(candidate_path, "\\\\project\\\\datastreams\\\\")

        candidate_is_under_any_project_features = candidate_is_under_project_features or (
            candidate_is_nested_deps_unit and candidate_has_project_features_segment
        )
        candidate_is_under_any_project_config = candidate_is_under_project_config or (
            candidate_is_nested_deps_unit and candidate_has_project_config_segment
        )
        candidate_is_under_any_project_datastreams = candidate_is_under_project_datastreams or (
            candidate_is_nested_deps_unit and candidate_has_project_datastreams_segment
        )

        if (
            candidate_is_under_any_project_features
            or candidate_is_under_any_project_config
            or candidate_is_under_any_project_datastreams
        ):
            project_resource_header_names.add(candidate.name)

    for file in source_files:
        full_file_path = full_path(file)
        is_under_api = test_is_under_path(full_file_path, api_dir)

        is_under_bootstrap = test_is_under_path(full_file_path, infra_bootstrap_dir)
        is_under_service = test_is_under_path(full_file_path, infra_service_dir)
        is_under_hal = test_is_under_path(full_file_path, infra_hal_dir)
        is_under_bsp = test_is_under_path(full_file_path, infra_bsp_dir)
        is_under_deps_extern = test_is_under_path(full_file_path, deps_extern_dir)
        is_under_deps_middleware = test_is_under_path(full_file_path, deps_middleware_dir)
        is_under_project_features = test_is_under_path(full_file_path, project_features_dir)
        is_under_project_config = test_is_under_path(full_file_path, project_config_dir)
        is_under_project_datastreams = test_is_under_path(full_file_path, project_datastreams_dir)

        is_nested_deps_unit = is_under_deps_extern or is_under_deps_middleware
        has_project_features_segment = test_contains_subpath(full_file_path, "\\\\project\\\\features\\\\")
        has_project_config_segment = test_contains_subpath(full_file_path, "\\\\project\\\\config\\\\")
        has_project_datastreams_segment = test_contains_subpath(full_file_path, "\\\\project\\\\datastreams\\\\")
        has_infra_bootstrap_segment = test_contains_subpath(full_file_path, "\\\\infra\\\\bootstrap\\\\")
        has_infra_service_segment = test_contains_subpath(full_file_path, "\\\\infra\\\\service\\\\")
        has_infra_hal_segment = test_contains_subpath(full_file_path, "\\\\infra\\\\platform\\\\hal\\\\")
        has_infra_bsp_segment = test_contains_subpath(full_file_path, "\\\\infra\\\\platform\\\\bsp\\\\")

        is_under_any_bootstrap = is_under_bootstrap or (is_nested_deps_unit and has_infra_bootstrap_segment)
        is_under_any_service = is_under_service or (is_nested_deps_unit and has_infra_service_segment)
        is_under_any_hal = is_under_hal or (is_nested_deps_unit and has_infra_hal_segment)
        is_under_any_bsp = is_under_bsp or (is_nested_deps_unit and has_infra_bsp_segment)
        is_under_any_project_features = is_under_project_features or (
            is_nested_deps_unit and has_project_features_segment
        )
        is_under_any_project_config = is_under_project_config or (
            is_nested_deps_unit and has_project_config_segment
        )
        is_under_any_project_datastreams = is_under_project_datastreams or (
            is_nested_deps_unit and has_project_datastreams_segment
        )

        role, feature = get_role_info(file.name, unit_name)
        feature_from_path = get_feature_from_path(full_file_path)
        if feature_from_path:
            feature = feature_from_path

        if role == "invalid_prefix":
            err(str(file), 1, "naming.prefix", "Invalid role prefix 'inf_'. Keep role prefixes (ida_/prx_/poi_/mdw_/svc_/hal_/bsp_/stm_/cfg_/db_).")
            continue

        if unit_name and requires_unit_qualification(
            file.stem,
            is_under_any_bootstrap=is_under_any_bootstrap,
            is_under_any_project_features=is_under_any_project_features,
            is_under_any_project_config=is_under_any_project_config,
        ) and not stem_has_unit_suffix(file.stem, unit_name):
            err(
                str(file),
                1,
                "naming.unit_qualified",
                f"Internal /infra and /project files must use the unit-qualified suffix _{unit_name}: {file.name}",
            )

        if role == "unknown":
            is_top_level_architecture_managed_path = (
                is_under_project_features or is_under_project_config or is_under_project_datastreams or is_under_bootstrap
                or is_under_service or is_under_hal or is_under_bsp or is_under_api
            )
            if is_top_level_architecture_managed_path:
                err(str(file), 1, "naming.prefix", f"Unknown architecture file role prefix: {file.name}")
            continue

        if file.name.lower() in cfg_core_names and not is_under_any_bootstrap:
            err(str(file), 1, "path.bootstrap", f"{file.name} must be located under /infra/bootstrap (root or nested architecture unit).")

        if role == "core_idea" and not is_under_any_bootstrap:
            err(str(file), 1, "path.bootstrap", "ida_core must be located under /infra/bootstrap (root or nested architecture unit).")
        elif role == "core_poiesis" and not is_under_any_bootstrap:
            err(str(file), 1, "path.bootstrap", "poi_core must be located under /infra/bootstrap (root or nested architecture unit).")
        elif role == "core_praxis" and not is_under_any_bootstrap:
            err(str(file), 1, "path.bootstrap", "prx_core must be located under /infra/bootstrap (root or nested architecture unit).")
        elif role == "service" and not is_under_any_service and not is_under_api:
            err(str(file), 1, "path.infra_service", "svc_* files must be located under /infra/service or /api.")
        elif role == "hal" and not is_under_any_hal and not is_under_api:
            err(str(file), 1, "path.infra_hal", "hal_* files must be located under /infra/platform/hal or /api.")
        elif role == "bsp" and not is_under_any_bsp and not is_under_api:
            err(str(file), 1, "path.infra_bsp", "bsp_* files must be located under /infra/platform/bsp or /api.")
        elif role == "app" and not is_under_api:
            err(str(file), 1, "path.app", "app_* files must be located under /api.")
        elif role == "middleware" and not is_under_deps_middleware and not is_under_deps_extern and not is_under_api:
            err(str(file), 1, "path.deps_middleware", "mdw_* files must be located under /deps/middleware, /deps/extern, or /api.")
        elif role == "idea" and not is_under_any_project_features:
            err(str(file), 1, "path.project_feature", "ida_* feature files must be located under /project/features (root or nested architecture unit).")
        elif role == "praxis" and not is_under_any_project_features:
            err(str(file), 1, "path.project_feature", "prx_* feature files must be located under /project/features (root or nested architecture unit).")
        elif role == "poiesis" and not is_under_any_project_features:
            err(str(file), 1, "path.project_feature", "poi_* feature files must be located under /project/features (root or nested architecture unit).")
        elif role == "feature_cfg":
            is_external_non_fractal_cfg = is_nested_deps_unit and not has_project_features_segment and not has_project_config_segment
            if not is_external_non_fractal_cfg and file.name.lower() not in cfg_core_names:
                is_project_anchor_cfg = file.name.lower() == "cfg_project.h" or (
                    unit_name and file.name.lower() == f"cfg_project_{unit_name}.h"
                )
                if is_project_anchor_cfg:
                    if not is_under_any_project_config:
                        err(str(file), 1, "path.project_config", f"{file.name} must be located under /project/config (root or nested architecture unit).")
                elif not is_under_any_project_features and not is_under_any_project_config:
                    err(str(file), 1, "path.feature_resource", f"cfg_* feature files must be located under /project/features/ or /project/config/ (root or nested architecture unit): {file.name}")
        elif role == "feature_db":
            is_external_non_fractal_db = is_nested_deps_unit and not has_project_features_segment and not has_project_config_segment
            if not is_external_non_fractal_db:
                if file.name.lower() == "db_project.h":
                    if not is_under_any_project_config:
                        err(str(file), 1, "path.project_config", "db_project.h must be located under /project/config (root or nested architecture unit).")
                elif not is_under_any_project_features and not is_under_any_project_config:
                    err(str(file), 1, "path.feature_resource", f"db_* feature files must be located under /project/features/ or /project/config/ (root or nested architecture unit): {file.name}")
        elif role == "datastream" and not is_under_any_project_datastreams and not is_under_deps_middleware and not is_under_deps_extern:
            err(str(file), 1, "path.datastream", f"stm_* files must be located under /project/datastreams/, /deps/middleware/, or /deps/extern/: {file.name}")

        try:
            text = file.read_text(encoding="utf-8")
        except Exception as exc:
            err(str(file), 1, "read", f"Failed to read file: {exc}")
            continue

        includes = get_includes_from_text(text)
        platform_evidence = collect_platform_evidence(includes, text)
        platform_categories = {str(item["category"]) for item in platform_evidence}
        if "board" in platform_categories and "peripheral" in platform_categories:
            mixed_line = min(int(item["line"]) for item in platform_evidence)
            warn(
                str(file),
                mixed_line,
                "red-flag-hal-bsp-mixed",
                "File mixes peripheral abstraction and board wiring. Split HAL and BSP responsibilities.",
            )

        if platform_evidence and not is_platform_declared_role(role):
            seen_platform_findings: set[tuple[int, str]] = set()
            for item in sorted(platform_evidence, key=lambda entry: (int(entry["line"]), str(entry["message"]))):
                key = (int(item["line"]), str(item["message"]))
                if key in seen_platform_findings:
                    continue
                seen_platform_findings.add(key)
                err(
                    str(file),
                    int(item["line"]),
                    "platform.misplaced",
                    f"Non-platform file owns raw platform coupling ({item['message']}). Extract this responsibility to /infra/platform/hal or /infra/platform/bsp.",
                )

        for inc in includes:
            line_no = int(inc["Line"])
            include_path = str(inc["IncludePath"])
            leaf = str(inc["Leaf"])
            raw = str(inc["Raw"])

            if SYSTEM_INCLUDE_REGEX.match(raw):
                continue

            if role in {"core_idea", "core_poiesis", "core_praxis", "idea", "praxis", "poiesis"}:
                if re.search(r"(^|[\\/])deps([\\/]|$)", include_path):
                    err(str(file), line_no, "include.deps_path", f"Do not include dependency repository paths directly from core/project layers: {include_path}")

            is_core_cfg = leaf in core_config_names
            is_project_cfg = leaf in project_config_names
            if role == "core_idea":
                if re.match(r"^prx_", leaf) and leaf not in prx_core_names:
                    err(str(file), line_no, "ida_core.include", f"ida_core must not include feature praxis: {include_path}")
                if re.match(r"^poi_", leaf) and leaf not in poi_core_names:
                    err(str(file), line_no, "ida_core.include", f"ida_core must not include feature poiesis: {include_path}")
                if re.match(r"^cfg_", leaf) and not is_core_cfg:
                    err(str(file), line_no, "ida_core.include", f"ida_core may include only core contract headers: {include_path}")
                if re.match(r"^(db_|stm_|mdw_|svc_|hal_|bsp_)", leaf):
                    err(str(file), line_no, "ida_core.include", f"ida_core must not include lower layer/resource headers directly: {include_path}")

            elif role == "idea":
                if re.match(r"^prx_", leaf) and not test_is_same_feature_include(leaf, "prx", feature, header_feature_owners):
                    err(str(file), line_no, "ida.include", f"Idea must include only its own feature Praxis headers: {include_path}")
                if re.match(r"^poi_", leaf) and not test_is_same_feature_include(leaf, "poi", feature, header_feature_owners):
                    err(str(file), line_no, "ida.include", f"Idea must include only its own feature Poiesis headers: {include_path}")
                if re.match(r"^ida_", leaf) and not test_is_same_feature_include(leaf, "ida", feature, header_feature_owners):
                    err(str(file), line_no, "ida.include", f"Idea must not include other features' Idea headers: {include_path}")
                if re.match(r"^cfg_", leaf) and not is_core_cfg:
                    err(str(file), line_no, "ida.include", f"Idea must not include cfg_ directly (except core contract): {include_path}")
                if re.match(r"^(db_|stm_|mdw_|svc_|hal_|bsp_)", leaf):
                    err(str(file), line_no, "ida.include", f"Idea must not include lower layer/resource headers directly: {include_path}")

            elif role == "core_poiesis":
                if re.match(r"^ida_", leaf) and leaf not in ida_core_names:
                    err(str(file), line_no, "poi_core.include", f"poi_core must not include feature ideas: {include_path}")
                if re.match(r"^(prx_|poi_)", leaf) and leaf not in poi_core_names:
                    err(str(file), line_no, "poi_core.include", f"poi_core must not include feature PRX/POI headers: {include_path}")
                if re.match(r"^(hal_|bsp_)", leaf):
                    err(str(file), line_no, "poi_core.include", f"poi_core must not include platform headers directly: {include_path}")
                if re.match(r"^cfg_", leaf) and not is_core_cfg:
                    err(str(file), line_no, "poi_core.include", f"poi_core may include only core contract headers: {include_path}")

            elif role == "core_praxis":
                if re.match(r"^ida_", leaf) and leaf not in ida_core_names:
                    err(str(file), line_no, "prx_core.include", f"prx_core must not include feature ideas: {include_path}")
                if re.match(r"^(prx_|poi_)", leaf) and leaf not in (prx_core_names | poi_core_names):
                    err(str(file), line_no, "prx_core.include", f"prx_core must not include feature PRX/POI headers: {include_path}")
                if re.match(r"^(hal_|bsp_)", leaf):
                    err(str(file), line_no, "prx_core.include", f"prx_core must not include platform headers directly: {include_path}")
                if re.match(r"^cfg_", leaf) and not is_core_cfg:
                    err(str(file), line_no, "prx_core.include", f"prx_core may include only core contract headers: {include_path}")

            elif role == "praxis":
                if re.match(r"^ida_", leaf):
                    err(str(file), line_no, "prx.include", f"Praxis must not include Idea headers: {include_path}")
                if re.match(r"^prx_", leaf) and not test_is_same_feature_include(leaf, "prx", feature, header_feature_owners):
                    err(str(file), line_no, "prx.include", f"Praxis must not include other features' Praxis: {include_path}")
                if re.match(r"^poi_", leaf) and not test_is_same_feature_include(leaf, "poi", feature, header_feature_owners):
                    err(str(file), line_no, "prx.include", f"Praxis must not include other features' Poiesis: {include_path}")
                if re.match(r"^cfg_", leaf) and not is_core_cfg and not is_project_cfg and not test_is_same_feature_include(leaf, "cfg", feature, header_feature_owners):
                    err(str(file), line_no, "prx.include", f"Praxis must not include other features' config: {include_path}")
                if re.match(r"^db_", leaf) and not is_project_cfg and not test_is_same_feature_include(leaf, "db", feature, header_feature_owners):
                    err(str(file), line_no, "prx.include", f"Praxis must not include other features' database headers: {include_path}")

            elif role == "poiesis":
                if re.match(r"^ida_", leaf):
                    err(str(file), line_no, "poi.include", f"Poiesis must not include Idea headers: {include_path}")
                if re.match(r"^prx_", leaf):
                    err(str(file), line_no, "poi.include", f"Poiesis must not include Praxis headers (no reverse dependency): {include_path}")
                if re.match(r"^poi_", leaf) and not test_is_same_feature_include(leaf, "poi", feature, header_feature_owners):
                    err(str(file), line_no, "poi.include", f"Poiesis must not include other features' Poiesis: {include_path}")
                if re.match(r"^cfg_", leaf) and not is_core_cfg and not is_project_cfg and not test_is_same_feature_include(leaf, "cfg", feature, header_feature_owners):
                    err(str(file), line_no, "poi.include", f"Poiesis must not include other features' config: {include_path}")
                if re.match(r"^db_", leaf) and not is_project_cfg and not test_is_same_feature_include(leaf, "db", feature, header_feature_owners):
                    err(str(file), line_no, "poi.include", f"Poiesis must not include other features' database headers: {include_path}")

            if role in {"feature_cfg", "feature_db", "datastream"}:
                if re.match(r"^(ida_|prx_|poi_)", leaf):
                    err(str(file), line_no, "resource.include", f"Resources must not include upper-layer headers: {include_path}")

            if role in {"service", "middleware"}:
                if re.match(r"^(ida_|prx_|poi_)", leaf):
                    is_api_entry_bootstrap = is_under_api and re.match(r"^ida_core_", leaf)
                    if not is_api_entry_bootstrap:
                        err(str(file), line_no, "module.include", f"Modules must not include upper-layer headers: {include_path}")
                if leaf in project_resource_header_names and not is_core_cfg:
                    err(str(file), line_no, "module.resource", f"Modules must not include resources (cfg_/db_/stm_) directly: {include_path}")

            if role in {"hal", "bsp"}:
                if role == "bsp" and re.match(r"^hal_", leaf):
                    err(str(file), line_no, "platform.direction", f"BSP must not include HAL headers (direction is HAL -> BSP): {include_path}")
                is_forbidden_platform_include = bool(
                    re.match(r"^(ida_|prx_|poi_|mdw_|svc_)", leaf)
                    or (leaf in project_resource_header_names and not is_core_cfg)
                )
                if is_forbidden_platform_include:
                    err(str(file), line_no, "platform.include", f"Platform must not include upper-layer/resource/module headers: {include_path}")

        # --- Rule: naming.service_export ---
        # Non-static function definitions in svc_ .c files must use Svc_ prefix
        if role == "service" and file.suffix.lower() == ".c":
            for line_idx, raw_line in enumerate(text.splitlines(), start=1):
                if raw_line[:1].isspace() or not raw_line.strip():
                    continue
                if raw_line.lstrip().startswith(("#", "/", "*", "typedef")):
                    continue
                m = SVC_EXPORT_FUNC_RE.match(raw_line)
                if not m:
                    continue
                func_name = m.group(1)
                if func_name.startswith("Svc_"):
                    continue
                err(str(file), line_idx, "naming.service_export",
                    f"Non-standard export '{func_name}'. Service-layer exports must use Svc_<Module>_ prefix.")

        # --- Rule: naming.service_header_export (advisory) ---
        # Function declarations in svc_ .h files should use Svc_ prefix
        if role == "service" and file.suffix.lower() == ".h":
            for line_idx, raw_line in enumerate(text.splitlines(), start=1):
                if raw_line[:1].isspace() or not raw_line.strip():
                    continue
                if raw_line.lstrip().startswith(("#", "/", "*", "typedef")):
                    continue
                m = SVC_HEADER_FUNC_DECL_RE.match(raw_line)
                if not m:
                    continue
                func_name = m.group(1)
                if func_name.startswith("Svc_"):
                    continue
                warn(str(file), line_idx, "naming.service_header_export",
                    f"Non-standard declaration '{func_name}'. Service header exports should use Svc_<Module>_ prefix.")

        # --- Rule: structure.dead_shell ---
        # Service .c files with fewer than 3 code lines are dead shells
        if is_under_any_service and file.suffix.lower() == ".c":
            code_lines = count_code_lines(file)
            if code_lines < 3:
                err(str(file), 1, "structure.dead_shell",
                    f"Service file contains only {code_lines} code line(s). Remove empty shell files.")

    has_platform_implementation = any(
        test_is_under_path(full_path(candidate), infra_hal_dir)
        or test_is_under_path(full_path(candidate), infra_bsp_dir)
        for candidate in source_files
    )

    for item in build_evidence:
        build_file = Path(str(item["file"]))
        line_no = int(item["line"])
        message = str(item["message"])
        text = str(item["text"])

        if has_legacy_platform_build_path(text):
            err(
                build_file,
                line_no,
                "platform.misplaced.build",
                f"Legacy platform/port build reference detected ({text}). Align build wiring to /infra/platform/hal or /infra/platform/bsp.",
            )
            continue

        if not has_platform_implementation:
            err(
                build_file,
                line_no,
                "platform.misplaced.build",
                f"Repo-root build wiring shows platform responsibility ({message}) but no /infra/platform/hal or /infra/platform/bsp implementation was found under {root_path}.",
            )

    # Pre-group .c files by architectural role for shared helpers
    c_files = [f for f in source_files if f.suffix.lower() == ".c"]
    ida_files = [f for f in c_files if get_role_info(f.name, unit_name)[0] == "idea"]
    prx_files = [f for f in c_files if get_role_info(f.name, unit_name)[0] == "praxis"]
    poi_files = [f for f in c_files if get_role_info(f.name, unit_name)[0] == "poiesis"]
    service_files = [f for f in c_files if get_role_info(f.name, unit_name)[0] == "service"]
    internal_impl_files = [
        f for f in c_files
        if test_is_under_path(full_path(f), infra_bootstrap_dir)
        or test_is_under_path(full_path(f), infra_service_dir)
        or test_is_under_path(full_path(f), project_features_dir)
    ]

    # Stage: Orphan Datastream detection (advisory)
    stm_headers = [
        f for f in source_files
        if f.suffix.lower() == ".h" and get_role_info(f.name, unit_name)[0] == "datastream"
    ]
    if stm_headers:
        # Collect all includes from prx_/poi_ .c files to find stm_ consumers/producers
        prx_poi_includes: set[str] = set()
        for pf in prx_files + poi_files:
            try:
                text = pf.read_text(encoding="utf-8", errors="replace")
                for inc in get_includes_from_text(text):
                    prx_poi_includes.add(str(inc["Leaf"]).lower())
            except OSError:
                pass
        for stm_h in stm_headers:
            if stm_h.name.lower() not in prx_poi_includes:
                warn(
                    str(stm_h), 1, "datastream.orphan",
                    f"Datastream header '{stm_h.name}' is not included by any prx_/poi_ source file. "
                    "Verify it has active producers/consumers; remove if obsolete.",
                )

    # Stage: Layer Balance Invariant (v1.0.1, error severity)
    verify_layer_balance(
        ida_files, poi_files, findings,
        extract_feature=get_feature_from_path, count_lines=count_code_lines,
    )

    # Stage: Red Flag heuristics (advisory only)
    verify_red_flags_common(
        ida_files, prx_files, poi_files, findings,
        count_lines=count_code_lines,
        extract_feature=get_feature_from_path,
    )
    verify_service_ownership_common(
        service_files, internal_impl_files, findings,
        count_lines=count_code_lines,
    )

    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]

    print(f"comsect1 code verification complete: {root_path}")
    print(f"Errors: {len(errors)}")
    if warnings:
        print(f"Warnings (advisory): {len(warnings)}")
    for e in sorted(errors, key=lambda item: (str(item["file"]), int(item["line"]), str(item["rule"]))):
        print(f"- {e['file']}:{e['line']} [{e['rule']}] {e['message']}")
    for w in sorted(warnings, key=lambda item: (str(item["file"]), int(item["line"]), str(item["rule"]))):
        print(f"  (advisory) {w['file']}:{w['line']} [{w['rule']}] {w['message']}")

    if errors:
        print(f"\nGate FAILED -- {len(errors)} error(s) must be resolved.")
    elif warnings:
        print(f"\nGate passed -- {len(warnings)} advisory warning(s) for review.")
    else:
        print("\nGate passed -- no issues found.")

    if args.json_out:
        report = {
            "generatedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "repoRoot": str(repo_root),
            "rootPath": str(root_path),
            "errorsCount": len(errors),
            "warningsCount": len(warnings),
            "findings": findings,
        }
        write_json_no_bom(Path(args.json_out), report)
        print(f"JSON report: {args.json_out}")

    return 2 if errors else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
