# 8. Naming Conventions

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.

---

## 8.1 Philosophy: Names as Intent Declarations

Every filename is an architectural declaration:

```
ida_motor.c   -> Idea file for motor feature
prx_motor.c   -> Praxis file for motor feature
poi_motor.c   -> Poiesis file for motor feature
cfg_motor.h   -> Feature configuration
```

A newcomer should infer role, allowed dependencies, and expected responsibility from prefix alone.

---

## 8.2 Complete Naming Scheme

| Category | Folder Path | Prefix | Note |
|----------|-------------|--------|------|
| **Core Idea** | `/infra/bootstrap/` | `ida_core` | required |
| **Core Poiesis** | `/infra/bootstrap/` | `poi_core` | required |
| **Core Praxis (optional)** | `/infra/bootstrap/` | `prx_core` | only if core has externally-coupled interpretation |
| **Core Contract header** | `/infra/bootstrap/` | `cfg_core` | required |
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

Reserved project header:
- `/project/config/cfg_project.h` for target configuration (Praxis/Poiesis include only)

### 8.2.1 No `inf_` role prefix policy

`infra` is a layout visibility concept, not a role prefix.

- Correct: `svc_storage.c` under `/infra/service/`
- Incorrect: `inf_storage.c`

Role meaning must remain encoded by existing prefixes (`svc_`, `mdw_`, `hal_`, ...).

---

## 8.3 Application Scope

| Role | Enforcement |
|------|-------------|
| `ida_`, `prx_`, `poi_`, `cfg_`, `db_`, `stm_` in project-owned code | Required |
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

| Prefix | Role |
|--------|------|
| `ida_` | intent and domain decision |
| `prx_` | externally-coupled domain interpretation |
| `poi_` | mechanical production/bridging |
| `mdw_` | middleware |
| `svc_` | service |
| `stm_` | datastream |
| `cfg_` | configuration |
| `db_`  | static data tables |
| `hal_` | hardware abstraction layer |
| `bsp_` | board support package |

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
