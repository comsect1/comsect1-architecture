# 12. Version History

> **Note:** This section is a non-normative record of architectural evolution.

---

## Unreleased

### Normative additions

- **Standard Packages** (Section 14): introduces canonical example
  packages (comsect1-std, comsect1-mdw-os, comsect1-mdw-storage_manager).
  Usage is not required for architecture compliance.
- **SSOT terminology** (Section 2.7.10): adds Standard Package definition.
- **Anemic Idea** (Section 10.5): new anti-pattern for thin-wrapper Idea.
- **WHAT/WHEN/WHICH**: Idea layer question shorthand expanded across all
  spec files.
- **Idea Responsibility Catalog** (Section 4.1.2): normative table of
  responsibility categories that belong in `ida_`.
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
- **Pre-Generation Discriminator**: 3-Question Discriminator must be explicitly
  answered and documented before writing `ida_`/`prx_`/`poi_` code
- **Layer Balance Invariant**: `ida_` must contain domain decisions; empty
  forwarding-only `ida_` is a structural violation
- **Migration Invariants** (Section 7.9.1): canonical folder skeleton must
  precede file placement
- **Standalone Middleware Repository Layout** (Section 7.10): canonical folder
  structure for middleware published as its own repository
- **Unit-Qualified Naming** (Section 8.6): all comsect1 units must qualify
  internal file names as `<prefix>_<name>_<unit>`
- **`app_` prefix** (Section 8.2, 8.5): new role prefix for main project
  public interface

### Guides and tooling

- Analysis, review, setup, migration, and verification guides updated.
- Gate scripts: deps/ exclusion, app_ recognition, unit-qualified naming
  enforcement, folder structure verification, layer balance check.
- Codex AI tooling package added.

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
