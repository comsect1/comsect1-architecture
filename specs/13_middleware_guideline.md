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
- `mdw_can`, `mdw_lin`
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
#include "mdw_can.h"   /* in ida_main.c: forbidden */

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

A complex Middleware may internally use the same architectural shape:

```
/deps/middleware/lin/
  /api
    mdw_lin.h
  /infra/bootstrap
    ida_core.c/h
    poi_core.c/h
    cfg_core.h
  /project/features/
    /schedule
      ida_schedule.c/h
      prx_schedule.c/h
      poi_schedule.c/h
```

Notes:
- Middleware reuses main project's `/infra` capability components.
- Middleware must not duplicate HAL/BSP stacks.
- `/api` is the only external membrane.

---

## 13.5 New Middleware Development Checklist

- [ ] Located under `/deps/middleware/<name>/`
- [ ] `/api` folder exists with public header
- [ ] Internal core/project layout exists if module is complex
- [ ] Public naming uses `Mdw_<ModuleName>_`
- [ ] Internal state and implementation details are hidden
- [ ] Used only by `prx_`/`poi_`, never by `ida_`
- [ ] No direct include of feature resources (`cfg_`, `db_`, `stm_`)
- [ ] Reuses shared `/infra/platform` and `/infra/service` where possible

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
