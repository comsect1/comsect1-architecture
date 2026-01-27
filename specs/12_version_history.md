# 12. Version History

> **Note:** This section is a non-normative record of architectural evolution.

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
  - no `inf_` role prefix; visibility is achieved by folder grouping and verification

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
