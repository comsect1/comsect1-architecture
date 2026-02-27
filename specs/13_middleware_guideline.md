# 13. Middleware Integration Guideline

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.

---

## 13.0 Overview

This document defines how Middleware (`mdw_`) is integrated into comsect1 with consistent dependency direction.

Primary goal:
- formalize the contract between Middleware and consumers (`prx_` / `poi_`)
- keep Middleware reusable and architecture-compliant

---

## 13.1 Definition and Role

Middleware is a reusable module that encapsulates complex integration logic:

- protocol stacks
- scheduler/OS wrappers
- stateful coordination logic

Examples:
- `mdw_os`, `mdw_scheduler`
- `mdw_serial`, `mdw_comm`
- `mdw_storage`

---

## 13.2 Interaction Rules (Dependencies)

Middleware must **never** be called directly from Idea.

Correct pattern:

**`Idea` -> `{Praxis, Poiesis}` -> `Middleware`**

1. Idea defines WHAT/WHEN.
2. Praxis handles externally-coupled interpretation when needed.
3. Poiesis handles mechanical execution.
4. Praxis/Poiesis call Middleware/Service/HAL as needed.

```c
/* Anti-pattern */
#include "mdw_serial.h"   /* in ida_main.c: forbidden */

/* Correct */
#include "prx_main.h"   /* or poi_main.h */
```

### Resource Access

Middleware must not directly include feature resources (`cfg_`, `db_`, `stm_`).
Configuration is injected by `prx_`/`poi_` at init/runtime.

---

## 13.3 API Design Principles

- Provide one stable public API header (`mdw_<name>.h`).
- Hide internal state machines and private structures.
- Keep API cohesive around one responsibility.
- Prefix public symbols with `Mdw_<ModuleName>_`.

---

## 13.4 Internal Structure (Fractal Pattern)

A complex Middleware may internally use the same architectural shape as the main project.
The structure looks different depending on the viewing context.

### 13.4.1 Consumer Project View (Installed Middleware)

When a middleware unit is **embedded as a dependency** inside a consumer project,
the consumer's comsect1 tree looks like:

```
/comsect1                          (consumer project root)
  /deps/middleware/comm
    /api
      mdw_comm.h                   ← access point for prx_/poi_ in the consumer
    /infra/bootstrap
      ida_core_comm.c/h             ← middleware-qualified (§8.6)
      poi_core_comm.c/h
      cfg_core_comm.h
    /project/features/
      /schedule
        ida_schedule_comm.c/h
        prx_schedule_comm.c/h
        poi_schedule_comm.c/h
```

This is the **consumer's view** — `api/` appears under `deps/middleware/<name>/` because that is
where the middleware unit is installed.

### 13.4.2 Standalone Middleware Repository View

When the same middleware module is developed **as its own repository**, its `/comsect1` root follows
the standard top-level structure (Section 7.3, Section 7.10):

```
/comsect1                          (middleware repo root)
  /api
    mdw_comm.h                     ← public API at root, NOT under deps/
  /infra/bootstrap
    ida_core_comm.c/h              ← middleware-qualified (§8.6)
    poi_core_comm.c/h
    cfg_core_comm.h
  /project/features/
    /schedule
      ida_schedule_comm.c/h
      prx_schedule_comm.c/h
      poi_schedule_comm.c/h
```

The `/api` folder is at the middleware unit root in both contexts. The difference is only the
path from the outer project perspective (where in the outer tree the middleware unit is located).

Notes:
- When embedded, middleware reuses the consumer project's shared `/infra` capability components where possible.
- Middleware must not duplicate HAL/BSP stacks.
- `/api` is the only external membrane in both views.

---

## 13.5 New Middleware Development Checklist

Packaging context:
- [ ] If developed as a standalone repository, the middleware unit root is `/comsect1`
- [ ] If embedded into a consumer project, the middleware unit appears under `/deps/middleware/<name>/`
- [ ] In both contexts, the middleware unit exposes `/api` at its own root

Architecture and API:
- [ ] Internal core/project layout exists if the middleware is complex
- [ ] Public naming uses `Mdw_<ModuleName>_`
- [ ] Internal state and implementation details are hidden
- [ ] Used only by `prx_`/`poi_`, never by `ida_`
- [ ] No direct include of feature resources (`cfg_`, `db_`, `stm_`)
- [ ] Reuses shared `/infra/platform` and `/infra/service` where the consumer project provides them

---

## 13.6 Internal Naming (Collision Prevention)

All internal files of a middleware comsect1 unit MUST follow the unit-qualified
naming rule (§8.6): `<prefix>_<name>_<unit>`.

This prevents file name collisions when the middleware is compiled alongside the
consumer project or other middleware units. The `/api/mdw_<name>.h` filename determines `<unit>` for middleware.

The §13.4 examples above already reflect this rule.

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
