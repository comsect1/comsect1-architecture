# 7. Folder Structure

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.
> - **Layout**: Physical folder conventions (what this section defines)
> - **Domain**: Responsibility boundaries (Project/Infra Capability/Dependency Repository)
>
> Layout reflects Domain structure but optimizes for developer workflow.

---

## 7.1 Philosophy: Structure for Cohesion and Intent

The folder structure is designed to maximize **feature cohesion** while making shared execution capability explicit.

```text
When you open the project:
  /comsect1
  /api            "Public API exposed to external consumers."
  /project        "Target-owned code and resources."
    /config       "Project-scoped cfg_/db_."
    /features     "Feature folders with ida_/prx_/poi_/cfg_/db_."
    /datastreams  "Project-specific stm_ (optional)."
  /infra          "Shared execution capability fabric."
    /bootstrap    "ida_core, poi_core, cfg_core (+ optional prx_core)."
    /service      "svc_*"
    /platform     "hal_*/bsp_*"
  /deps           "dependency repository."
    /extern       "git submodules."
    /middleware   "vendor middleware sources."
```

---

## 7.2 Root Folder Convention

All comsect1 architecture source files reside under a dedicated root folder named `comsect1`.

```text
/MyProject
  /codes
    /comsect1
    main.c
  /build
  /docs
  CMakeLists.txt
```

---

## 7.3 Top-Level Grouping

| Top-Level Folder | Type | Description |
|------------------|------|-------------|
| **/api** | Interface | Public API exposed to external consumers. |
| **/project** | Layout group | Target-owned code/resources (`/project/config`, `/project/features`, optional `/project/datastreams`). |
| **/infra** | Domain (Capability) | Shared execution capability (`bootstrap`, `service`, `platform`). |
| **/deps** | Domain (Dependency Repository) | External dependency sources (`/deps/extern`, `/deps/middleware`). |

> **Note:** The Domain axis and Layout axis are distinct (Section 2.7.1).
> Feature logic still lives under `/project/features/` and is organized by Idea-Praxis-Poiesis prefixes.

---

## 7.4 Naming Cues Inside Feature Folders

The folder layout optimizes cohesion; role meaning is expressed by file prefixes.

- `ida_`: intent and decision
- `prx_`: external-type-coupled interpretation
- `poi_`: mechanical execution
- `cfg_`/`db_`: feature resources

See **Section 8** for full naming rules.

---

## 7.5 Complete Folder Structure (Reference)

```text
/Project
  /codes
    /comsect1
      /api
        app_<project>.h
      /project
        /config
          cfg_project.h
          db_project.h        (optional)
        /datastreams          (optional)
          stm_<project>.h
        /features
          /sensor
            ida_sensor.c/h
            prx_sensor.c/h     (optional by discriminator)
            poi_sensor.c/h
            cfg_sensor.h
            db_sensor.h
          /comm_stack
            ida_comm_stack.c/h
            /business
              prx_comm_protocol_*.c
              poi_comm_runtime.c/h
      /infra
        /bootstrap
          ida_core.c/h
          poi_core.c/h
          cfg_core.h
          prx_core.c/h        (optional by discriminator)
        /service
          svc_*.c/h
        /platform
          /hal
            hal_*.c/h
          /bsp
            bsp_*.c/h
      /deps
        /extern
          <vendor-lib>/
        /middleware
          <vendor-mdw-src>/
    main.c
  /build
  /docs
  CMakeLists.txt
```

> **Note:** File names above are shown in base form. When unit-qualified naming applies (§8.6),
> append `_<unit>` to each `ida_`/`prx_`/`poi_`/`cfg_`/`db_` file name.

---

## 7.6 Resource Placement and Access

Resources like `cfg_` and `db_` are co-located with their owning feature.

- `cfg_<feature>.h`, `db_<feature>.h` live in `/project/features/<feature>/`.
- Project-wide target configuration lives in `/project/config/cfg_project.h`.
- Core contract vocabulary lives in `/infra/bootstrap/cfg_core.h`.

**Datastream (`stm_`) placement** depends on scope:

| Location | Scope |
|----------|-------|
| `/deps/middleware/` or dependency-provided headers | Reusable datastream/capability definitions |
| `/project/datastreams/` | Project-specific inter-feature state |

Access invariants:
- Idea does not access `cfg_`/`db_`/`stm_` directly.
- Praxis/Poiesis may access own feature resources and `stm_`.
- Feature-to-feature runtime interaction is datastream-only.

---

## 7.7 API and Fractal Structure

The `/api` folder is the public membrane of a comsect1 unit.

```text
Main Application (Core 0)      Middleware Unit (example)
/comsect1                      /comsect1/deps/middleware/comm
  /api                           /api
  /infra/bootstrap               /infra/bootstrap
  /project                       /project
  /infra                         (reuses shared infra policies)
```

`/api` allows intended integration while reducing accidental coupling to internals.

---

## 7.8 Self-Describing Codebase

| What You See | What You Understand |
|--------------|---------------------|
| `/project/features/sensor/` | "Sensor feature logic is here." |
| `ida_sensor.c` | "Intent and decision for sensor." |
| `prx_sensor.c` | "External-type interpretation for sensor." |
| `poi_sensor.c` | "Mechanical execution for sensor." |
| `/infra/service/` | "Shared service capability." |

This supports low entry barrier and high comprehension.

---

## 7.9 Legacy Layout Migration

Legacy folder layouts (`/modules/`, `/platform/`) are not conformant with this specification.
The verification script enforces normative layout only.

### 7.9.1 Migration Invariants

1. The canonical folder skeleton (Section 7.5) MUST be created before file placement begins.
2. Files MUST be placed into their canonical locations before semantic refactoring (layer role and balance corrections).
3. After migration, non-conformant folders and orphaned files MUST be removed or moved outside the `/comsect1` boundary.

For the step-by-step procedural guide, see `guides/02_Execution_Guides/EG_02_Refactoring_Legacy.md`.

---

## 7.10 Standalone Middleware Repository Layout

A middleware module published as its own repository (not yet embedded into a consumer project)
follows the same top-level structure as any comsect1 unit.

```text
/comsect1                       ← comsect1 root of the middleware repo
  /api
    mdw_<name>.h                ← public API header (the single external membrane)
  /infra
    /bootstrap
      ida_core_<name>.c/h       ← unit-qualified (§8.6)
      poi_core_<name>.c/h
      cfg_core_<name>.h
  /project
    /config
      cfg_project_<name>.h
    /features
      /<feature>
        ida_<feature>_<name>.c/h
        poi_<feature>_<name>.c/h
        cfg_<feature>_<name>.h
  /deps                         ← own external dependencies (if any)
    /extern
    /middleware
/examples                       ← outside /comsect1 — consumer integration examples
/docs
CMakeLists.txt
```

Key rules:
- `/api` at the comsect1 root is the middleware's own public API (same rule as any comsect1 unit).
- `/examples` and `/docs` are consumer-facing artifacts and must reside **outside** the `/comsect1`
  boundary.
- When this repo is later embedded as a dependency in a consumer project, the consumer places the
  repo under their own `/deps/middleware/<name>/` and gains access through `<name>/api/` — this is
  the consumer-side view documented in §7.7 and §13.4.1.

**Common mistake**: placing `mdw_<name>.h` under `/deps/middleware/<name>/api/` inside the standalone
repo itself. This confuses the consumer project view with the standalone repo view.

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
