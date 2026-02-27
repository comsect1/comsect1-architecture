#!/usr/bin/env python3
"""Verify comsect1 code layout and dependency rules."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

SOURCE_EXTENSIONS = {".c", ".h", ".cpp", ".hpp"}
INCLUDE_REGEX = re.compile(r'^\s*#\s*include\s*[<"](?P<path>[^">]+)[">]')
SYSTEM_INCLUDE_REGEX = re.compile(r"^\s*#\s*include\s*<")


def full_path(path_like: str | Path) -> str:
    return os.path.abspath(os.fspath(path_like))


def add_finding(
    findings: list[dict[str, object]],
    severity: str,
    file_path: str,
    line: int,
    rule: str,
    message: str,
) -> None:
    findings.append(
        {
            "Severity": severity,
            "File": file_path,
            "Line": line,
            "Rule": rule,
            "Message": message,
        }
    )


def get_role_info(file_name: str) -> tuple[str, str | None]:
    stem = Path(file_name).stem

    if re.match(r"^inf_", stem):
        return "invalid_prefix", None

    core_map = {
        "ida_core": "core_idea",
        "poi_core": "core_poiesis",
        "prx_core": "core_praxis",
    }
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

    return "unknown", None


def get_includes(path: Path) -> list[dict[str, object]]:
    includes: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
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


MIN_IDA_LINES = 10
DOMAIN_CONDITIONAL_RE = re.compile(
    r"\b(?:if|switch|case)\b.*\b(?:mode|state|status|level|type|flag|enable|disable|active|threshold)\b",
    re.IGNORECASE,
)

COMMENT_LINE_RE = re.compile(r"^\s*(?://|/\*|\*|\*/)")
BLANK_LINE_RE = re.compile(r"^\s*$")


def count_code_lines(path: Path) -> int:
    """Count non-blank, non-comment lines in a C source file."""
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
                if stripped.startswith("/*") and "*/" not in stripped[2:]:
                    in_block_comment = True
                    continue
                if BLANK_LINE_RE.match(stripped) or COMMENT_LINE_RE.match(stripped):
                    continue
                if stripped.startswith("#"):  # preprocessor directives don't count as logic
                    continue
                count += 1
    except OSError:
        pass
    return count


def verify_red_flags(
    source_files: list[Path],
    findings: list[dict[str, object]],
) -> None:
    """Advisory-level Red Flag heuristic checks (§11.8)."""
    for file in source_files:
        if file.suffix.lower() != ".c":
            continue
        role, _ = get_role_info(file.name)

        # Red Flag: Empty Idea
        if role == "idea":
            code_lines = count_code_lines(file)
            if code_lines < MIN_IDA_LINES:
                add_finding(
                    findings,
                    "warning",
                    str(file),
                    0,
                    "red-flag-empty-idea",
                    f"ida_ source has only {code_lines} code lines (threshold: {MIN_IDA_LINES}). "
                    "Verify that domain judgment is present, not just pass-through calls.",
                )

        # Red Flag: Fat Poiesis
        if role == "poiesis":
            try:
                text = file.read_text(encoding="utf-8", errors="replace")
                domain_hits = DOMAIN_CONDITIONAL_RE.findall(text)
                if domain_hits:
                    add_finding(
                        findings,
                        "warning",
                        str(file),
                        0,
                        "red-flag-fat-poiesis",
                        f"poi_ source contains {len(domain_hits)} domain-meaningful conditional(s). "
                        "Consider moving domain logic to ida_ or prx_.",
                    )
            except OSError:
                pass


def collect_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SOURCE_EXTENSIONS:
            files.append(p)
    return files


def write_json_no_bom(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify comsect1 code architecture rules.")
    parser.add_argument("-Root", dest="root", required=True)
    parser.add_argument("-JsonOut", dest="json_out", default=None)
    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    if not root_path.is_dir():
        raise RuntimeError(f"Root folder not found: {root_path}")

    findings: list[dict[str, object]] = []

    def err(file_path: str, line: int, rule: str, message: str) -> None:
        add_finding(findings, "error", file_path, line, rule, message)

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

    core_config_names = {"cfg_core.h"}
    top_level_core_contract_header = infra_bootstrap_dir / "cfg_core.h"
    if not top_level_core_contract_header.is_file():
        err(str(root_path), 1, "layout.required", f"Missing required Core Contract header: {top_level_core_contract_header}")

    core_config_dir = root_path / "core" / "config"
    if core_config_dir.is_dir():
        err(str(root_path), 1, "layout.legacy", f"Legacy core config folder detected. Migrate to /infra/bootstrap/cfg_core.h: {core_config_dir}")

    project_config_names: set[str] = set()
    if project_config_dir.is_dir():
        for header in project_config_dir.glob("*.h"):
            if header.is_file():
                project_config_names.add(header.name)
        if "cfg_project.h" not in project_config_names:
            err(str(project_config_dir), 1, "layout.required", f"Missing required project target interface header: {project_config_dir / 'cfg_project.h'}")
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

    source_files = collect_source_files(root_path)
    if not source_files:
        err(str(root_path), 1, "layout.required", f"No source files found under: {root_path}")

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
        candidate_role, _ = get_role_info(candidate.name)
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

        role, feature = get_role_info(file.name)
        feature_from_path = get_feature_from_path(full_file_path)
        if feature_from_path:
            feature = feature_from_path

        if role == "invalid_prefix":
            err(str(file), 1, "naming.prefix", "Invalid role prefix 'inf_'. Keep role prefixes (ida_/prx_/poi_/mdw_/svc_/hal_/bsp_/stm_/cfg_/db_).")
            continue

        if role == "unknown":
            is_top_level_architecture_managed_path = (
                is_under_project_features or is_under_project_config or is_under_project_datastreams or is_under_bootstrap
            )
            if is_top_level_architecture_managed_path:
                err(str(file), 1, "naming.prefix", f"Unknown architecture file role prefix: {file.name}")
            continue

        if file.name.lower() == "cfg_core.h" and not is_under_any_bootstrap:
            err(str(file), 1, "path.bootstrap", "cfg_core.h must be located under /infra/bootstrap (root or nested architecture unit).")

        if role == "core_idea" and not is_under_any_bootstrap:
            err(str(file), 1, "path.bootstrap", "ida_core must be located under /infra/bootstrap (root or nested architecture unit).")
        elif role == "core_poiesis" and not is_under_any_bootstrap:
            err(str(file), 1, "path.bootstrap", "poi_core must be located under /infra/bootstrap (root or nested architecture unit).")
        elif role == "core_praxis" and not is_under_any_bootstrap:
            err(str(file), 1, "path.bootstrap", "prx_core must be located under /infra/bootstrap (root or nested architecture unit).")
        elif role == "service" and not is_under_any_service:
            err(str(file), 1, "path.infra_service", "svc_* files must be located under /infra/service (root or nested architecture unit).")
        elif role == "hal" and not is_under_any_hal:
            err(str(file), 1, "path.infra_hal", "hal_* files must be located under /infra/platform/hal (root or nested architecture unit).")
        elif role == "bsp" and not is_under_any_bsp:
            err(str(file), 1, "path.infra_bsp", "bsp_* files must be located under /infra/platform/bsp (root or nested architecture unit).")
        elif role == "middleware" and not is_under_deps_middleware and not is_under_deps_extern:
            err(str(file), 1, "path.deps_middleware", "mdw_* files must be located under /deps/middleware or /deps/extern.")
        elif role == "idea" and not is_under_any_project_features:
            err(str(file), 1, "path.project_feature", "ida_* feature files must be located under /project/features (root or nested architecture unit).")
        elif role == "praxis" and not is_under_any_project_features:
            err(str(file), 1, "path.project_feature", "prx_* feature files must be located under /project/features (root or nested architecture unit).")
        elif role == "poiesis" and not is_under_any_project_features:
            err(str(file), 1, "path.project_feature", "poi_* feature files must be located under /project/features (root or nested architecture unit).")
        elif role == "feature_cfg":
            is_external_non_fractal_cfg = is_nested_deps_unit and not has_project_features_segment and not has_project_config_segment
            if not is_external_non_fractal_cfg and file.name.lower() != "cfg_core.h":
                if file.name.lower() == "cfg_project.h":
                    if not is_under_any_project_config:
                        err(str(file), 1, "path.project_config", "cfg_project.h must be located under /project/config (root or nested architecture unit).")
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
            includes = get_includes(file)
        except Exception as exc:
            err(str(file), 1, "read", f"Failed to read file: {exc}")
            continue

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
                if re.match(r"^prx_", leaf) and leaf != "prx_core.h":
                    err(str(file), line_no, "ida_core.include", f"ida_core must not include feature praxis: {include_path}")
                if re.match(r"^poi_", leaf) and leaf != "poi_core.h":
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
                if re.match(r"^ida_", leaf) and leaf != "ida_core.h":
                    err(str(file), line_no, "poi_core.include", f"poi_core must not include feature ideas: {include_path}")
                if re.match(r"^(prx_|poi_)", leaf) and leaf != "poi_core.h":
                    err(str(file), line_no, "poi_core.include", f"poi_core must not include feature PRX/POI headers: {include_path}")
                if re.match(r"^(hal_|bsp_)", leaf):
                    err(str(file), line_no, "poi_core.include", f"poi_core must not include platform headers directly: {include_path}")
                if re.match(r"^cfg_", leaf) and not is_core_cfg:
                    err(str(file), line_no, "poi_core.include", f"poi_core may include only core contract headers: {include_path}")

            elif role == "core_praxis":
                if re.match(r"^ida_", leaf) and leaf != "ida_core.h":
                    err(str(file), line_no, "prx_core.include", f"prx_core must not include feature ideas: {include_path}")
                if re.match(r"^(prx_|poi_)", leaf) and leaf not in {"prx_core.h", "poi_core.h"}:
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

    # Stage: Red Flag heuristics (advisory only)
    verify_red_flags(source_files, findings)

    errors = [f for f in findings if f["Severity"] == "error"]
    warnings = [f for f in findings if f["Severity"] == "warning"]

    print(f"comsect1 code verification complete: {root_path}")
    print(f"Errors: {len(errors)}")
    if warnings:
        print(f"Warnings (advisory): {len(warnings)}")
    for e in sorted(errors, key=lambda item: (str(item["File"]), int(item["Line"]), str(item["Rule"]))):
        print(f"- {e['File']}:{e['Line']} [{e['Rule']}] {e['Message']}")
    for w in sorted(warnings, key=lambda item: (str(item["File"]), int(item["Line"]), str(item["Rule"]))):
        print(f"  (advisory) {w['File']}:{w['Line']} [{w['Rule']}] {w['Message']}")

    if args.json_out:
        report = {
            "generatedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "rootPath": str(root_path),
            "errorsCount": len(errors),
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
