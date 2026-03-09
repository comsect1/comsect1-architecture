# 8. Naming Conventions

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.

---

## 8.1 Philosophy: Names as Intent Declarations

Every filename is an architectural declaration:

```
ida_sensor.c   -> Idea file for sensor feature
prx_sensor.c   -> Praxis file for sensor feature
poi_sensor.c   -> Poiesis file for sensor feature
cfg_sensor.h   -> Feature configuration
```

A newcomer should infer role, allowed dependencies, and expected responsibility from prefix alone.

---

## 8.2 Complete Naming Scheme

| Category | Folder Path | Prefix | Note |
|----------|-------------|--------|------|
| **Core Idea** | `/infra/bootstrap/` | `ida_core_<unit>` | required |
| **Core Poiesis** | `/infra/bootstrap/` | `poi_core_<unit>` | required |
| **Core Praxis (optional)** | `/infra/bootstrap/` | `prx_core_<unit>` | only if core has externally-coupled interpretation |
| **Core Contract header** | `/infra/bootstrap/` | `cfg_core_<unit>` | required |
| **Project Config** | `/project/config/` | `cfg_` | required |
| **Project Database** | `/project/config/` | `db_` | optional |
| **Feature Idea** | `/project/features/<feature>/` | `ida_` | required |
| **Feature Praxis** | `/project/features/<feature>/` | `prx_` | optional by discriminator |
| **Feature Poiesis** | `/project/features/<feature>/` | `poi_` | optional by discriminator |
| **Feature Config** | `/project/features/<feature>/` | `cfg_` | optional |
| **Feature Database** | `/project/features/<feature>/` | `db_` | optional |
| **Middleware** | `/deps/middleware/` or `/deps/extern/*` | `mdw_` | recommended |
| **Service** | `/infra/service/` | `svc_` | recommended |
| **Datastream** | `/project/datastreams/` (or dependency-provided) | `stm_` | required |
| **HAL** | `/infra/platform/hal/` | `hal_` | recommended |
| **BSP** | `/infra/platform/bsp/` | `bsp_` | recommended |
| **External modules** | `/deps/extern/` | *(external)* | optional |
| **Application API** | `/api/` | `app_` | required for main projects |

Reserved project header:
- `/project/config/cfg_project_<unit>.h` for target configuration (Praxis/Poiesis include only)
  (This file also serves as the identity anchor for main projects — see §8.6)

---

## 8.3 Application Scope

| Role | Enforcement |
|------|-------------|
| `app_`, `ida_`, `prx_`, `poi_`, `cfg_`, `db_`, `stm_` in project-owned code | Required |
| `mdw_`, `svc_`, `hal_`, `bsp_` for reusable/external code | Recommended |

Primary enforcement remains human code review. Optional scripts may assist, but architecture meaning is human-owned.

---

## 8.4 Naming Principles

- Prefix must match architectural role.
- Feature name must be consistent across folder and filenames.
- Preferred file set in one feature folder:
  - `ida_<feature>.c/h`
  - `prx_<feature>.c/h` (if needed)
  - `poi_<feature>.c/h` (if needed)
  - `cfg_<feature>.h`, `db_<feature>.h` (if needed)
- Decomposed large feature patterns:
  - `prx_<feature>_<aspect>.c/h`
  - `poi_<feature>_<aspect>.c/h`
  - Variant form: `prx_<feature>_<aspect>_<variant>.c`

---

## 8.5 Prefix Selection Rationale

This table is exhaustive. Only prefixes listed here are valid architectural
role prefixes. Any prefix not in this table is a naming violation.

### Feature Layers

| Prefix | Role |
|--------|------|
| `ida_` | intent and domain decision |
| `prx_` | externally-coupled domain interpretation |
| `poi_` | mechanical production/bridging |

### Resources

| Prefix | Role |
|--------|------|
| `cfg_` | configuration |
| `db_`  | static data tables |
| `stm_` | datastream |

### External API

| Prefix | Role |
|--------|------|
| `app_` | main project public interface |
| `mdw_` | middleware |
| `svc_` | service |
| `hal_` | hardware abstraction layer |
| `bsp_` | board support package |

---

## 8.6 Unit-Qualified Naming

Every comsect1 unit that exposes a public API (identified by the presence of `api/`
at the comsect1 root) is a **sub-unit** and MUST qualify all internal file names with
its unit identifier to prevent name collisions in consumer build include paths.

Pattern: `<prefix>_<name>_<unit>`

The `<unit>` identifier is derived from the primary API header in `api/`:

| API header          | Unit identifier | Example internal file    |
|---------------------|-----------------|--------------------------|
| `api/mdw_comm.h`    | `comm`          | `ida_core_comm.c/h`      |
| `api/mdw_storage.h` | `storage`       | `ida_core_storage.c/h`   |
| `api/hal_uart.h`    | `uart`          | `ida_core_uart.c/h`      |
| `api/mylib.h`       | `mylib`         | `ida_core_mylib.c/h`     |

Extraction rule: if the API header stem contains `_`, strip the first segment (role prefix)
and use the remainder. If no `_`, use the full stem.

Scope:
- Applies to: `ida_`, `prx_`, `poi_`, `cfg_`, `db_` files in `/infra/` and `/project/`
- Exempt: `api/<header>.h` (already named with the unit identity)
- Exempt: `svc_`, `hal_`, `bsp_` files (shared infrastructure, intentionally reused)

API headers in `/api/` use the role prefix that matches the unit's architectural
role. Sub-units use their existing role prefix (`mdw_`, `hal_`, etc.). Main
projects use `app_` because no other single role prefix applies.

**Unit identity declaration**:

Every comsect1 unit must declare its identity through an anchor file from which
`<unit>` is derived:

| Unit type      | Anchor file                               | Unit extracted |
|----------------|-------------------------------------------|----------------|
| Sub-unit       | `api/<role>_<unit>.h` (e.g. `mdw_comm.h`) | `<unit>`       |
| Main project   | `project/config/cfg_project_<unit>.h`    | `<unit>`       |

For main projects, this means renaming `cfg_project.h` to `cfg_project_<projectname>.h`
(e.g. `cfg_project_demo.h`). This is the only file that changes — the containing folder
(`project/config/`) remains unchanged.

**Important — folder structure is not affected**:
This rule applies to **file names only**. Folder paths are defined by §7 and remain
unchanged. The comsect1 folder skeleton (`/infra/bootstrap/`, `/project/features/<feature>/`,
etc.) is identical for all comsect1 units.

Example — legacy vs. qualified naming (unit = `demo`):

| Location (unchanged)          | Legacy form (unqualified) | Qualified form              |
|-------------------------------|---------------------------|-----------------------------|
| `infra/bootstrap/`            | `cfg_core.h`              | `cfg_core_demo.h`           |
| `infra/bootstrap/`            | `ida_core.c/h`            | `ida_core_demo.c/h`         |
| `infra/bootstrap/`            | `poi_core.c/h`            | `poi_core_demo.c/h`         |
| `project/features/schedule/`  | `ida_schedule.c/h`        | `ida_schedule_demo.c/h`     |
| `project/features/schedule/`  | `prx_schedule.c/h`        | `prx_schedule_demo.c/h`     |

Rationale: In C embedded builds, include paths are flat. Multiple comsect1 units compiled
together each contribute files with identical base names — the compiler cannot distinguish
them. Qualifying with the unit identifier makes each file's identity globally unique.

See also: §13.6 (middleware instance); §13.4 (updated examples).

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
