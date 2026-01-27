# 4. Role of Each Layer

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.
> - **Domain:** Project, Infra Capability, Dependency Repository
> - **Architecture Layer:** Idea (`ida_`), Praxis (`prx_`), Poiesis (`poi_`)
> - **Execution Plane:** Data plane (`stm_`) vs Capability plane (`mdw_`/`svc_`/`hal_`/`bsp_`)

This section is normative for layer responsibilities.

---

## 4.0 Core Scope (inside Infra Bootstrap)

### 4.0.1 Overview

Core is the supervisor domain above all features.

Core default architecture:
- `ida_core`: registration policy and orchestration intent
- `poi_core`: OS/scheduler execution and mechanical registration

Optional:
- `prx_core`: only when core has externally-coupled interpretation that cannot be reduced to pure execution

| Core layer | Prefix | Location | Primary role |
|------------|--------|----------|--------------|
| Core Idea | `ida_core` | `/infra/bootstrap/` | which features, what order, when to start |
| Core Poiesis | `poi_core` | `/infra/bootstrap/` | scheduler/OS wrapping and task registration execution |
| Core Praxis (optional) | `prx_core` | `/infra/bootstrap/` | externally-coupled interpretation in core context |

### 4.0.2 CORE IDEA (`ida_core`)

Allowed:
- include feature `ida_*.h` for interface collection
- define feature participation and order
- call feature `init()` in policy order
- call core execution API (`poi_core`)
- include `cfg_core.h`

Prohibited:
- include `mdw_*.h`, `svc_*.h`, `hal_*.h`, `bsp_*.h`
- include feature `prx_*.h` or `poi_*.h`
- include feature resources (`cfg_<feature>.h`, `db_<feature>.h`, `stm_*.h`)

### 4.0.3 CORE POIESIS (`poi_core`)

Allowed:
- include scheduler/OS middleware (`mdw_*.h`)
- consume `Ida_Interface_t` objects passed from `ida_core`
- execute task creation / registration / scheduler start
- include `cfg_core.h`

Prohibited:
- include feature `ida_*.h` (policy belongs to `ida_core`)
- include HAL/BSP directly
- make policy decisions (which features, what order)

### 4.0.4 CORE PRAXIS (`prx_core`, optional)

Use `prx_core` only when core must interpret external-type-coupled semantics.
If core logic is pure execution wrapping, use only `poi_core`.

### 4.0.5 OS Positioning

OS stays in dependency middleware scope (`mdw_os`, `mdw_scheduler`).
Core uses OS; core is not OS.

Callback usage is not reverse dependency when:
- OS does not include `ida_*.h`
- callbacks are registered through interface objects

### 4.0.6 Dependency Symmetry

```
ida_core -> feature ida_*     (policy)
feature ida_* -> own prx_/poi_ (feature-local dependency)
poi_core -> mdw_scheduler      (execution)
```

Only `ida_core` includes feature `ida_*.h`.

### 4.0.7 Independence Guarantees

- Idea-to-Idea direct calls are prohibited.
- Feature-to-feature communication is datastream-only (`stm_`).
- Features remain self-contained; core orchestrates them.

### 4.0.8 Execution Models

`ida_core` interface remains stable across execution models.
Only `poi_core` implementation varies:

| Model | `poi_core` behavior |
|-------|----------------------|
| Super loop | sequentially dispatch each idea main entry |
| Cooperative scheduler | register tasks and start scheduler |
| RTOS | create tasks and start OS scheduler |

### 4.0.9 Self-Contained Initialization

Each feature initializes what it owns through its own `prx_`/`poi_`.

Shared init APIs must be idempotent (or explicit init-once semantics).
If strict global ordering is unavoidable, it must be explicit in `ida_core` policy + `poi_core` execution.

### 4.0.10 Platform Initialization Pattern

Platform initialization that requires application data must remain feature-owned.

Forbidden pattern:

```c
/* /infra/platform/bsp/system_init.c */
#include "prx_storage.h"   /* forbidden: platform -> feature reverse include */
```

Allowed patterns:

1. Dedicated HW init feature
- storage feature publishes boot params to `stm_`
- hw-init feature consumes `stm_` and calls HAL/BSP through own `prx_`/`poi_`

2. Feature-owned hardware init
- feature init performs its own required hardware setup

Invariants:
- core does not include HAL/BSP directly
- platform does not include feature headers
- cross-feature data uses `stm_`

### 4.0.11 Core Code Sketch

```c
/* ida_core.c */
#include "cfg_core.h"
#include "poi_core.h"
#include "ida_feature_a.h"
#include "ida_feature_b.h"

void Ida_Core_Entry(void)
{
    Poi_Core_Init();
    Poi_Core_Register(Ida_FeatureA_GetInterface());
    Poi_Core_Register(Ida_FeatureB_GetInterface());
    Poi_Core_Start();
}
```

---

## 4.1 Feature Domain

### 4.1.1 Overview

Feature layers answer different questions:

- `ida_`: WHAT/WHEN
- `prx_`: externally-coupled interpretation with domain meaning
- `poi_`: mechanical execution

### 4.1.2 IDEA (`ida_`)

Allowed:
- business decisions, policy, flow
- include `cfg_core.h`
- include own `prx_`/`poi_` headers

Prohibited:
- include `mdw_`, `svc_`, `hal_`, `bsp_`
- include feature resources directly (`cfg_`, `db_`, `stm_`)
- include other feature files

### 4.1.3 PRAXIS (`prx_`) and POIESIS (`poi_`)

PRX (`prx_`) allowed:
- external-type/protocol interpretation tied to domain meaning
- call own `poi_`
- include/use `mdw_`, `svc_`, `hal_`, `cfg_`, `db_`, `stm_`

PRX prohibited:
- include other feature's `ida_`/`prx_`/`poi_`
- upward call into Idea

POI (`poi_`) allowed:
- wrapping/bridging/forwarding of OS/HAL/module/resource interactions
- include/use `mdw_`, `svc_`, `hal_`, `cfg_`, `db_`, `stm_`

POI prohibited:
- business decisions
- external-type-coupled domain interpretation
- include other feature's `ida_`/`prx_`/`poi_`

### 4.1.4 Large Feature Praxis/Poiesis Decomposition

Large features may decompose PRX/POI into sub-modules.

Naming patterns:
- `prx_<feature>_<aspect>.c/h`
- `poi_<feature>_<aspect>.c/h`
- variant form: `prx_<feature>_<aspect>_<variant>.c`

Rules:
- decomposition stays within same feature folder/subfolder
- Idea includes only its own feature PRX/POI headers
- cross-feature includes remain prohibited

---

## 4.2 Infra Capability Domain and Data Plane Boundary

### 4.2.1 Overview

Shared **capability** components are consumed by PRX/POI and live under `/infra/*`.

Capability types:
- Middleware (`mdw_`)
- Service (`svc_`)
- Platform (`hal_`, `bsp_`)

Capability components must not depend on upper layers.
Role prefixes and dependency constraints remain unchanged.

Orthogonal note:
- Datastream (`stm_`) is the **data plane**, not an infra capability component.
- `stm_` placement is `/project/datastreams` (project scope) or `/deps/*` (reusable scope).

### 4.2.2 MIDDLEWARE

Middleware contains reusable integration/stateful logic.

Rules:
- consumed by `prx_`/`poi_`, not `ida_`
- public API only (`mdw_<name>.h`)
- no direct include of feature resources (`cfg_`, `db_`, `stm_`)

### 4.2.3 SERVICE

Service provides reusable computation/transform logic.

Rules:
- no upper-layer include
- no feature coupling
- keep deterministic and side-effect-minimal where possible

### 4.2.4 DATASTREAM (`stm_`, Data Plane)

Datastream is neutral cross-feature runtime state.

Rules:
- inter-feature communication channel
- accessed via PRX/POI only
- no ownership by any single feature

Datastream is the **data plane**, orthogonal to infra capability APIs.

---

## 4.3 Platform Subdomain (inside Infra)

Platform includes HAL and BSP.

Rules:
- Platform must not include feature headers.
- Platform is consumed by PRX/POI, not Idea.
- HAL abstracts peripherals; BSP handles board/boot specifics.

Platform is part of the execution **capability plane**.
It provides mechanisms, not feature policy.

---

## 4.4 Quick Role Table

| Role | Prefix | Core responsibility | Must not do |
|------|--------|---------------------|-------------|
| Idea | `ida_` | business intent/decision | include infra/deps/resources/platform directly |
| Praxis | `prx_` | externally-coupled interpretation | mechanical-only wrapper accumulation, cross-feature include |
| Poiesis | `poi_` | mechanical production/execution | business/protocol meaning decisions |

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
