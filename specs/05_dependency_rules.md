# 5. Dependency Rules

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.
> - **Architecture Layer**: Idea / Praxis / Poiesis
> - **Domain**: Project / Infra Capability / Dependency Repository

---

## 5.0 Philosophy: Dependencies as Alignment

Dependency rules are the mechanism that keeps alignment toward The Order.

Every include/import is a trust statement:

```
When A depends on B:
  A trusts B's stability
  A changes when B changes
```

The architectural goal is one-way dependency direction toward intent purity.

### The Selective Extraction Principle

Dependency rules implement what the author's upstream philosophy calls the **Selective Extraction Principle**: a well-formed structure makes intended actions easy to perform and unintended actions structurally difficult.

In comsect1 terms:
- `ida_` can reach only its own `prx_`/`poi_` — the intended path of least resistance.
- `ida_` is blocked from `cfg_`/`db_`/`stm_`/`mdw_`/`svc_`/`hal_`/`bsp_` — unintended paths are made structurally impossible.
- Feature-to-feature communication uses `stm_` only — the data plane is the selective membrane.

This creates **directionality** (intent flows one way through the system) and **constancy** (the system resists arbitrary coupling drift).

---

## 5.1 Header Include Direction (Allowed)

```c
/* /infra/bootstrap/ */
ida_core.c
  +-- #include "cfg_core.h"
  +-- #include "poi_core.h"        /* core execution */
  +-- #include "ida_<feature>.h"   /* registration policy */
  +-- (NO mdw_*.h, svc_*.h, hal_*.h, bsp_*.h)

/* /infra/bootstrap/ */
poi_core.c
  +-- #include "poi_core.h"
  +-- #include "cfg_core.h"
  +-- #include "mdw_scheduler.h"
  +-- (NO ida_<feature>.h)
  +-- (NO hal_*.h, bsp_*.h)

/* /project/features/motor/ */
ida_motor.c
  +-- #include "cfg_core.h"
  +-- #include "prx_motor.h"       /* optional */
  +-- #include "poi_motor.h"       /* optional */
  +-- (NO cfg_motor.h, db_motor.h, stm_*.h)
  +-- (NO mdw_*.h, svc_*.h, hal_*.h, bsp_*.h)

/* /project/features/motor/ */
prx_motor.c
  +-- #include "prx_motor.h"
  +-- #include "poi_motor.h"       /* same feature */
  +-- #include "cfg_motor.h"
  +-- #include "db_motor.h"
  +-- #include "stm_sensor.h"
  +-- #include "mdw_can.h"
  +-- #include "svc_math.h"
  +-- #include "hal_pwm.h"

/* /project/features/motor/ */
poi_motor.c
  +-- #include "poi_motor.h"
  +-- #include "cfg_motor.h"
  +-- #include "db_motor.h"
  +-- #include "stm_sensor.h"
  +-- #include "mdw_can.h"
  +-- #include "svc_math.h"
  +-- #include "hal_pwm.h"

/* /deps/middleware/can/ */
mdw_can.c
  +-- #include "mdw_can.h"
  +-- #include "hal_can.h"
  +-- (NO ida_*.h, prx_*.h, poi_*.h)
```

---

## 5.2 Dependency Principles

### 5.2.1 Within a Feature

```
+------------------------------------------------+
| /project/features/motor/                       |
|                                                |
| ida_motor -> { prx_motor, poi_motor }          |
| prx_motor -> poi_motor                         |
| prx_motor/poi_motor -> cfg_/db_/stm_/mdw_/svc_|
| prx_motor/poi_motor -> hal_                    |
+------------------------------------------------+
```

Rules:

- Idea -> own Praxis/Poiesis only (locked as allowed set `IDA -> { own PRX, own POI }`)
- IDA may call PRX only, POI only, or both, depending on discriminator output.
- Praxis -> own Poiesis, infra/resources/platform
- Poiesis -> infra/resources/platform
- No reverse includes (`prx_`/`poi_` -> `ida_`)

### 5.2.2 Between Features

Inter-feature communication uses datastream only.

Prohibited:

```c
#include "project/features/sensor/ida_sensor.h"  /* NEVER */
#include "project/features/sensor/prx_sensor.h"  /* NEVER */
#include "project/features/sensor/poi_sensor.h"  /* NEVER */
```

Allowed:

```c
#include "stm_sensor_data.h"
uint16_t temp = *Stm_SensorData_Stream(NULL);
```

### 5.2.3 Core Contract and Target Resource Access

| Category | Location | Who Can Access |
|----------|----------|----------------|
| **Core Contract header** | `/infra/bootstrap/cfg_core.h` | ALL layers |
| **Project Config/DB** | `/project/config/` | Praxis/Poiesis only |
| **Feature Config/DB** | `/project/features/<f>/` | Praxis/Poiesis only |
| **Datastream (`stm_`)** | `/project/datastreams/` or dependency-provided headers | Praxis/Poiesis only |

`cfg_core.h` contains contract vocabulary.
`cfg_project.h` and feature resources contain implementation details.

### 5.2.4 Orthogonal execution planes

Dependency direction is governed by two orthogonal runtime planes:

- **Data plane (`stm_`)**: cross-feature runtime state/event flow
- **Capability plane (`mdw_`, `svc_`, `hal_`, `bsp_`, core execution wrappers)**: execution and resource control

Rules:
- Feature-to-feature runtime interaction uses data plane (`stm_`) only.
- Praxis/Poiesis may call capability plane APIs.
- Capability plane components must not include feature-layer headers (`ida_`/`prx_`/`poi_`).
- Do not create `inf_` role prefixes; folder grouping does not change prefix semantics.

---

## 5.3 Dependency Direction Diagram

```
Core: ida_core -> poi_core
Feature: ida_ -> { prx_, poi_ }
prx_ -> poi_
prx_/poi_ -> { mdw_, svc_, hal_, cfg_, db_, stm_ }
Infra capability -> Platform
Platform: HAL -> BSP
```

Plane interpretation:
- `stm_` edges represent data plane boundaries.
- `mdw_`/`svc_`/`hal_`/`bsp_` edges represent capability plane boundaries.

---

## 5.4 Prohibited Actions

- Idea directly including `mdw_`/`svc_`
- Idea directly including feature resources (`cfg_`, `db_`, `stm_`)
- Idea including another feature's files
- Praxis including another feature's `ida_`/`prx_`/`poi_`
- Poiesis including another feature's `ida_`/`prx_`/`poi_`
- Reverse dependencies (`prx_`/`poi_` -> `ida_`)
- Platform (HAL/BSP) including feature headers
- Core execution layer including HAL/BSP (platform init is feature responsibility; see Section 4.0.10)
- Resources including any upper layer header

Explicit exception:
- Any layer may include `cfg_core.h`.

---

## 5.5 The Cost of Violation

When dependency direction breaks, costs are deferred and compound:

- Requirement changes leak into wrong layers
- Platform changes ripple into Idea
- Feature boundaries collapse into transitive coupling
- Testability and reasoning cost increase non-linearly

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
