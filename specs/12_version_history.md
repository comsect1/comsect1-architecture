# 12. Version History

> **Note:** This section is a non-normative record of architectural evolution.

---

## v1.0.2

### Normative additions

- **Official unit identity setup**: Section 8.6 now explicitly defines the
  project naming procedure around two anchors: `/api/<role>_<unit>.h` and
  `/project/config/cfg_project_<unit>.h`.
- **Semantic platform misplaced classification**: raw platform evidence outside
  `/infra/platform/` is now defined as misplaced responsibility, not a harmless
  folder mismatch.
- **Contextual absence rule**: missing `hal_`/`bsp_` is no longer treated as
  true absence when platform-coupled code already exists elsewhere in the tree.
- **HAL/BSP mixed responsibility advisory**: files mixing peripheral
  abstraction and board wiring are now explicitly reviewable as a separate
  advisory concern.

### Guides and tooling

- Analysis, review, setup, migration, and verification guides now reference
  the unit identity anchors and semantic platform misplaced rules.
- The C code gate and AIAD runner are expected to scan repo-root build files
  for platform evidence and to report `platform.misplaced` /
  `platform.misplaced.build` findings.

---

## v1.0.0

### Architecture

- **3-Layer Feature Model**:
  - Idea (`ida_`): business intent and domain decisions
  - Praxis (`prx_`): externally-coupled interpretation with domain meaning
  - Poiesis (`poi_`): mechanical production, wrapping, and bridging
- **Feature-Centric Folder Structure**:
  - `/project/config/`: project-scoped `cfg_`/`db_`
  - `/project/features/`: feature-local `ida_`, `prx_`, `poi_`, `cfg_`, `db_`
  - `/project/datastreams/`: project-specific `stm_` (optional)
  - `/infra/bootstrap/`: `ida_core`, `poi_core`, `cfg_core` (and optional `prx_core`)
  - `/infra/service/`, `/infra/platform/`
  - `/deps/extern/`, `/deps/middleware/`
  - `/infra/platform/`: HAL/BSP
- **Dependency Rules**:
  - `IDA -> { own PRX, own POI }`
  - `PRX -> { own POI, mdw_, svc_, hal_, cfg_, db_, stm_ }`
  - `POI -> { mdw_, svc_, hal_, cfg_, db_, stm_ }`
  - Inter-feature communication via `stm_` only
- **Infra concept clarification**:
  - `infra` defined as shared capability fabric (orthogonal to `ida_`/`prx_`/`poi_`)
  - data plane (`stm_`) and capability plane (`mdw_`/`svc_`/`hal_`/`bsp_`/core execution) explicitly separated
  - `IDA -> { own PRX, own POI }` interpreted as allowed dependency set, not mandatory dual call
  - only listed role prefixes are valid; visibility is achieved by folder grouping and verification

### Why PRX/POI split was restored before first release

Audit findings showed one legacy `prx_` bucket was mixing two heterogeneous responsibilities:

1. External-type-coupled domain interpretation (true Praxis)
2. Mechanical wrapping/bridge code (Poiesis)

This weakened role clarity and caused classification drift. The architecture restores explicit separation by intent.

Philosophical alignment note:
- The author's upstream philosophical work describes practical propagation as `Idea -> Praxis -> implementation`.
- The split keeps that alignment by treating `Poiesis` as an explicit decomposition of the former implementation zone, not as an additional philosophical pole.

---

## v1.0.1

### Normative additions

- **Pre-Generation Discriminator**: 3-Question Discriminator must be explicitly answered and documented before writing `ida_`/`prx_`/`poi_` code (not silent application)
- **Layer Balance Invariant**: `ida_` must contain domain decisions; empty forwarding-only `ida_` is a structural violation equal in severity to dependency direction errors
- **Migration Invariants** (Section 7.9.1): canonical folder skeleton must precede file placement; non-conformant remnants must be removed after migration
- **Migration Cleanup Verification** (Section 11.10): checklist for verifying boundary cleanup after legacy migration

### Guides

- **EG_02 Refactoring Legacy**: Execution Phase restructured to spatial-first 4-step flow (scaffold → place → verify/refactor → cleanup)
- **V_01 Post-Task Checklist**: Section A.6 Layer Balance check added; Section J Migration Cleanup added

### Normative additions (continued)

- **Standalone Middleware Repository Layout** (Section 7.10): canonical folder structure for
  middleware published as its own repository — `/api` at the comsect1 root; `examples/` and
  `docs/` outside the `/comsect1` boundary. Distinguishes standalone repo view (§7.10) from
  consumer project view (§13.4.1). Follows from the fractal comsect1 unit principle (Ch.3
  Structure). Does not require upstream consultation.
- **§13.4 split into consumer view (§13.4.1) and standalone view (§13.4.2)**: clarifies the
  two-context nature of middleware API placement without changing the underlying rule.

### Guides

- **EG_06 Analysis Report Format**: display policy — write full report to `.comsect1-analysis.md`;
  show only Verdict Block (§A) and Closing Summary (§C) in conversation. Reduces output token
  consumption without information loss.
- **EG_07 Analysis Procedure**: Phase Gate model — two-phase analysis with gate as binary
  go/no-go decision point. Phase 1: gate execution (always). Phase 2: full qualitative analysis
  (only when gate passes). Lazy spec loading: read only spec sections relevant to gate violation
  rule prefixes.
- **EG_08 Review Procedure — Check 0**: folder structure check added as the first review check.
  `specs/07_folder_structure.md` was in the canonical sources list but had no corresponding
  check item; Check 0 closes this gap.

### Tooling

- Reference-based deployment: installed files reference canonical spec via path (`{{COMSECT1_ROOT}}`), not embedded copies
- Install scripts: `tooling/claude-code/install.sh` (bash), `install.ps1` (PowerShell)
- Layer Balance Check added to reviewer agent as BLOCKING severity
- **Language-agnostic folder enforcement**: `verify_folder_structure()` extracted to
  `comsect1_gate_helpers.py` (svc_ analog); both `Verify-Comsect1Code.py` and
  `Verify-OOPCode.py` now call it. A2 invariant ("folder structure rules not relaxed for OOP")
  is now mechanically enforced.
- **Codex AI tooling package**: `tooling/codex/` with `comsect1-analyze` and `comsect1-review`
  skills, install and bootstrap scripts. Consistency verified by `Verify-ToolingConsistency.py`
  alongside the existing claude-code package.
- **Gate: deps/ exclusion**: `Verify-Comsect1Code.py` and `Verify-OOPCode.py` now exclude
  `deps/` from all per-file checks (path, include, layer-balance, red-flag). External
  dependency code is verified by its own gate — the consumer project gate checks only
  project-owned code (`project/` and `infra/`). Follows from `deps/` being a Dependency
  Repository (§7.3), not project-owned code. Folder-structure root checks (§7.10) are
  unaffected as they operate at the root level, not per-file.
- **Unit-Qualified Naming** (§8.6, §8.2, §13.6): All comsect1 units (main project and
  sub-units alike) must qualify internal file names as `<prefix>_<name>_<unit>`. Main
  project exception removed. `<unit>` is derived from the API header for sub-units
  (e.g., `api/mdw_comm.h` → `comm`) or from `project/config/cfg_project_<unit>.h` for
  main projects (renaming `cfg_project.h`). Gate `detect_unit_name()` covers both
  anchor types. Gate enforces migration: main projects with `cfg_project.h` but no
  `cfg_project_<unit>.h` fail with `naming.missing_unit_anchor`. `cfg_core.h` legacy
  fallback retained for bootstrap files only. §8.2 bootstrap row names updated to
  `<prefix>_core_<unit>`. §13.4.1/§13.4.2 examples reflect qualified naming.

---

## v1.0.1-beta

### Normative additions

- **`app_` prefix introduced** (§8.2, §8.5): new role prefix for main project public
  interface. The application API header (`app_<project>.h`) in `/api/` serves as the
  external entry point from `main.c` into the comsect1 architecture.
- **§8.5 restructured**: prefix table reorganized into three categories — Feature Layers
  (`ida_`/`prx_`/`poi_`), Resources (`cfg_`/`db_`/`stm_`), and External API
  (`app_`/`mdw_`/`svc_`/`hal_`/`bsp_`). The table is now exhaustive: unlisted prefixes
  are naming violations.
- **§8.2.1 removed**: the specific prohibition naming a non-existent prefix is replaced
  by the exhaustive prefix list in §8.5. Category labels use plain English words, not
  prefix format, to avoid confusion between prefixes and categorization.
- **§8.6 clarification**: API headers in `/api/` use the role prefix matching the unit's
  architectural role. Sub-units use their existing role prefix (`mdw_`, `hal_`, etc.).
  Main projects use `app_`.
- **§7.5**: `api_<project>.h` renamed to `app_<project>.h`.
- **§8.3**: `app_` added to the Required enforcement row.

### Tooling

- **Gate: `app_` recognition**: `Verify-Comsect1Code.py` recognizes `app_` as a valid
  role prefix and validates that `app_*` files are located under `/api/`.

---

## Superseded Draft

An earlier draft used a strict 2-layer feature model (`ida_`/`prx_`).
That draft is superseded by the current 3-layer model.

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.0**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

You are free to:
- **Share** - copy and redistribute the material in any medium or format for non-commercial purposes only.

Under the following terms:
- **Attribution** - You must give appropriate credit to the author (Kim Hyeongjeong), provide a reference to the license, and indicate if changes were made.
- **NonCommercial** - You may not use the material for commercial purposes.
- **NoDerivatives** - If you remix, transform, or build upon the material, you may not distribute the modified material.

No additional restrictions - You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
