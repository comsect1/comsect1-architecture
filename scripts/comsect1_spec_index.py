#!/usr/bin/env python3
"""Generate .comsect1-spec-index.json mapping gate rules to SSOT spec sections.

This index enables AI agents to look up the exact spec section for any gate
rule without reading entire spec files, reducing token consumption.

Usage:
    python scripts/comsect1_spec_index.py [--repo-root <path>]

Output:
    <repo-root>/.comsect1-spec-index.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from comsect1_gate_helpers import resolve_repo_root

# ---------------------------------------------------------------------------
# Static mapping: gate rule ID -> SSOT spec section(s)
#
# Each entry maps a gate rule (or rule family prefix) to:
#   - "spec": relative path to the SSOT spec file
#   - "sections": list of section numbers within that file
#   - "summary": one-line description of what the rule checks
# ---------------------------------------------------------------------------

GATE_RULE_INDEX: list[dict[str, object]] = [
    # -- CAT-1: Layout --
    {"rule": "layout.root_boundary", "spec": "specs/07_folder_structure.md", "sections": ["7.2"], "summary": "comsect1 root folder convention"},
    {"rule": "layout.required", "spec": "specs/07_folder_structure.md", "sections": ["7.3", "7.5"], "summary": "Required directories and files"},
    {"rule": "layout.examples_misplaced", "spec": "specs/07_folder_structure.md", "sections": ["7.10"], "summary": "examples/ must be outside /comsect1"},
    {"rule": "layout.api-misplaced", "spec": "specs/07_folder_structure.md", "sections": ["7.3", "7.10"], "summary": "Standalone middleware API placement"},
    {"rule": "layout.legacy", "spec": "specs/07_folder_structure.md", "sections": ["7.9"], "summary": "Legacy folder detection"},

    # -- CAT-2: Naming --
    {"rule": "naming.prefix", "spec": "specs/08_naming_conventions.md", "sections": ["8.5"], "summary": "Valid role prefix enforcement"},
    {"rule": "naming.unit_qualified", "spec": "specs/08_naming_conventions.md", "sections": ["8.6"], "summary": "Unit-qualified file naming"},
    {"rule": "naming.api_anchor", "spec": "specs/08_naming_conventions.md", "sections": ["8.6.1"], "summary": "API identity anchor"},
    {"rule": "naming.unit_conflict", "spec": "specs/08_naming_conventions.md", "sections": ["8.6.2"], "summary": "Multiple unit identifiers"},
    {"rule": "naming.anchor_mismatch", "spec": "specs/08_naming_conventions.md", "sections": ["8.6.2"], "summary": "API/config anchor mismatch"},
    {"rule": "naming.missing_unit_anchor", "spec": "specs/08_naming_conventions.md", "sections": ["8.6.1"], "summary": "cfg_project.h without unit name"},
    {"rule": "naming.service_export", "spec": "specs/08_naming_conventions.md", "sections": ["8.5"], "summary": "svc_ export prefix enforcement"},
    {"rule": "naming.service_header_export", "spec": "specs/08_naming_conventions.md", "sections": ["8.5"], "summary": "svc_ header declaration prefix"},

    # -- CAT-3: Path Placement --
    {"rule": "path.bootstrap", "spec": "specs/07_folder_structure.md", "sections": ["7.5"], "summary": "Core files in /infra/bootstrap"},
    {"rule": "path.infra_service", "spec": "specs/07_folder_structure.md", "sections": ["7.5"], "summary": "svc_* in /infra/service"},
    {"rule": "path.infra_hal", "spec": "specs/07_folder_structure.md", "sections": ["7.5"], "summary": "hal_* in /infra/platform/hal"},
    {"rule": "path.infra_bsp", "spec": "specs/07_folder_structure.md", "sections": ["7.5"], "summary": "bsp_* in /infra/platform/bsp"},
    {"rule": "path.app", "spec": "specs/07_folder_structure.md", "sections": ["7.7"], "summary": "app_* in /api"},
    {"rule": "path.deps_middleware", "spec": "specs/07_folder_structure.md", "sections": ["7.5"], "summary": "mdw_* in /deps"},
    {"rule": "path.project_feature", "spec": "specs/07_folder_structure.md", "sections": ["7.5"], "summary": "ida_/prx_/poi_ in /project/features"},
    {"rule": "path.project_config", "spec": "specs/07_folder_structure.md", "sections": ["7.6"], "summary": "cfg_project/db_project in /project/config"},
    {"rule": "path.feature_resource", "spec": "specs/07_folder_structure.md", "sections": ["7.6"], "summary": "cfg_/db_ in /project/features or /project/config"},
    {"rule": "path.datastream", "spec": "specs/07_folder_structure.md", "sections": ["7.6"], "summary": "stm_* in /project/datastreams"},

    # -- CAT-4: Include/Dependency (C/embedded) --
    {"rule": "ida_core.include", "spec": "specs/04_layer_roles.md", "sections": ["4.0.2"], "summary": "ida_core include prohibitions"},
    {"rule": "ida.include", "spec": "specs/05_dependency_rules.md", "sections": ["5.2.1", "5.4"], "summary": "Feature ida_ include rules"},
    {"rule": "poi_core.include", "spec": "specs/04_layer_roles.md", "sections": ["4.0.3"], "summary": "poi_core include prohibitions"},
    {"rule": "prx_core.include", "spec": "specs/04_layer_roles.md", "sections": ["4.0.4"], "summary": "prx_core include prohibitions"},
    {"rule": "prx.include", "spec": "specs/05_dependency_rules.md", "sections": ["5.2.1", "5.4"], "summary": "Feature prx_ include rules"},
    {"rule": "poi.include", "spec": "specs/05_dependency_rules.md", "sections": ["5.2.1", "5.4"], "summary": "Feature poi_ include rules"},
    {"rule": "include.deps_path", "spec": "specs/05_dependency_rules.md", "sections": ["5.2.1"], "summary": "No direct deps/ path from core/project layers"},
    {"rule": "resource.include", "spec": "specs/05_dependency_rules.md", "sections": ["5.4"], "summary": "Resources must not include upper layers"},
    {"rule": "module.include", "spec": "specs/05_dependency_rules.md", "sections": ["5.4"], "summary": "Modules must not include upper layers"},
    {"rule": "module.resource", "spec": "specs/04_layer_roles.md", "sections": ["4.2.2"], "summary": "Modules must not include feature resources"},
    {"rule": "platform.include", "spec": "specs/05_dependency_rules.md", "sections": ["5.4"], "summary": "Platform must not include upper layers"},
    {"rule": "platform.direction", "spec": "specs/04_layer_roles.md", "sections": ["4.3.2"], "summary": "BSP must not include HAL"},

    # -- CAT-5: Include/Dependency (OOP) --
    {"rule": "ida-no-winforms", "spec": "specs/A2_oop_adaptation.md", "sections": ["A2.5.1", "A2.6.1"], "summary": "ida_ WinForms import forbidden"},
    {"rule": "ida-no-drawing", "spec": "specs/A2_oop_adaptation.md", "sections": ["A2.5.1", "A2.6.1"], "summary": "ida_ System.Drawing import forbidden"},
    {"rule": "ida-no-interop", "spec": "specs/A2_oop_adaptation.md", "sections": ["A2.5.1", "A2.6.1"], "summary": "ida_ COM Interop import forbidden"},
    {"rule": "ida-no-serialport", "spec": "specs/A2_oop_adaptation.md", "sections": ["A2.5.1", "A2.6.1"], "summary": "ida_ System.IO.Ports import forbidden"},
    {"rule": "ida-no-fileio", "spec": "specs/A2_oop_adaptation.md", "sections": ["A2.5.1", "A2.6.1"], "summary": "ida_ System.IO import forbidden"},
    {"rule": "ida-no-messagebox", "spec": "specs/A2_oop_adaptation.md", "sections": ["A2.5.1", "A2.6.1"], "summary": "ida_ MessageBox.Show forbidden"},
    {"rule": "ida-no-invoke", "spec": "specs/A2_oop_adaptation.md", "sections": ["A2.5.1", "A2.6.1"], "summary": "ida_ Invoke/BeginInvoke forbidden"},
    {"rule": "ida-no-threadsleep", "spec": "specs/A2_oop_adaptation.md", "sections": ["A2.5.1", "A2.6.1"], "summary": "ida_ Thread.Sleep forbidden"},
    {"rule": "ida-no-processstart", "spec": "specs/A2_oop_adaptation.md", "sections": ["A2.5.1", "A2.6.1"], "summary": "ida_ Process.Start forbidden"},
    {"rule": "cross-feature-layer-ref", "spec": "specs/05_dependency_rules.md", "sections": ["5.2.2"], "summary": "Cross-feature layer reference"},

    # -- CAT-6: Platform Boundary --
    {"rule": "platform.misplaced", "spec": "specs/05_dependency_rules.md", "sections": ["5.2.5"], "summary": "Platform coupling outside /infra/platform"},
    {"rule": "platform.misplaced.build", "spec": "specs/05_dependency_rules.md", "sections": ["5.2.5"], "summary": "Legacy platform path in build files"},

    # -- CAT-7: Service Ownership --
    {"rule": "service.public-backend-bounce", "spec": "specs/04_layer_roles.md", "sections": ["4.2.3"], "summary": "svc_ public API wraps backend symbol"},
    {"rule": "service.public-nonservice-delegate", "spec": "specs/04_layer_roles.md", "sections": ["4.2.3"], "summary": "svc_ delegates to non-service owner"},
    {"rule": "service.file-facade", "spec": "specs/04_layer_roles.md", "sections": ["4.2.3"], "summary": "svc_ file is pure facade"},
    {"rule": "service.misclassified-registry", "spec": "specs/04_layer_roles.md", "sections": ["4.2.3"], "summary": "svc_ may be registry/dispatch code"},
    {"rule": "service.infra-orphan", "spec": "specs/04_layer_roles.md", "sections": ["4.2.3"], "summary": "svc_ without infrastructure mechanism"},
    {"rule": "service.internal-public-bounce", "spec": "specs/04_layer_roles.md", "sections": ["4.2.3"], "summary": "Internal code calls public LIN API"},
    {"rule": "structure.dead_shell", "spec": "specs/07_folder_structure.md", "sections": ["7.5"], "summary": "Service file with < 3 code lines"},

    # -- CAT-8: Layer Balance --
    {"rule": "layer-balance", "spec": "specs/04_layer_roles.md", "sections": ["4.1.2"], "summary": "Layer Balance Invariant: empty ida_ + fat poi_"},

    # -- CAT-9: Red Flag Heuristics --
    {"rule": "red-flag-empty-idea", "spec": "specs/10_anti_patterns.md", "sections": ["10.5"], "summary": "ida_ < 10 code lines"},
    {"rule": "red-flag-fat-poiesis", "spec": "specs/04_layer_roles.md", "sections": ["4.1.3"], "summary": "poi_ contains domain conditionals"},
    {"rule": "red-flag-fat-praxis", "spec": "specs/04_layer_roles.md", "sections": ["4.1.3"], "summary": "prx_ has code but no domain conditionals"},
    {"rule": "red-flag-poi-wrapper", "spec": "specs/04_layer_roles.md", "sections": ["4.1.3"], "summary": "poi_ pure pass-through to prx_"},
    {"rule": "red-flag-praxis-overflow", "spec": "specs/10_anti_patterns.md", "sections": ["10.6"], "summary": "prx_ code lines exceed ida_ for same feature"},
    {"rule": "red-flag-hal-bsp-mixed", "spec": "specs/04_layer_roles.md", "sections": ["4.3.3"], "summary": "HAL/BSP mixed responsibility"},
    {"rule": "red-flag-ida-feature-resource", "spec": "specs/A2_oop_adaptation.md", "sections": ["A2.8.2"], "summary": "OOP ida_ references feature resource"},
    {"rule": "red-flag-ida-mutable-field", "spec": "specs/A2_oop_adaptation.md", "sections": ["A2.8.2"], "summary": "OOP ida_ mutable instance field"},
]


def generate_index(repo_root: Path) -> dict[str, object]:
    """Build the spec index payload."""
    by_rule: dict[str, dict[str, object]] = {}
    for entry in GATE_RULE_INDEX:
        by_rule[str(entry["rule"])] = {
            "spec": entry["spec"],
            "sections": entry["sections"],
            "summary": entry["summary"],
        }

    return {
        "_comment": "Auto-generated by comsect1_spec_index.py. Do not edit manually.",
        "rules": by_rule,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate comsect1 spec index.")
    parser.add_argument("--repo-root", dest="repo_root", default=None)
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = resolve_repo_root(script_path, args.repo_root)

    index = generate_index(repo_root)
    out_path = repo_root / ".comsect1-spec-index.json"
    out_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Spec index generated: {out_path}")
    print(f"  Rules indexed: {len(index['rules'])}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
