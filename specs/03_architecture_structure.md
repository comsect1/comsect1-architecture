# 3. Architecture Structure

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.
> - **Domain**: Project, Infra Capability, Dependency Repository
> - **Architecture Layer**: Idea, Praxis, Poiesis
> - **Layout**: physical folder conventions

---

## 3.1 Physical Structure (Layout)

comsect1 uses an **infra-integrated, feature-centric** folder structure for cohesion:

```
/comsect1
  /project/
    /config/
      cfg_project.h       <- Project target config (Praxis/Poiesis include)
    /datastreams/
      stm_<name>.h        <- Project-specific STM definitions
    /features/
      /<feature>/         <- ida_, prx_, poi_, cfg_, db_ together
  /infra/
    /bootstrap/           <- ida_core, poi_core, cfg_core (and optional prx_core)
    /service/             <- svc_*
    /platform/
      /hal/               <- hal_*
      /bsp/               <- bsp_*
  /deps/
    /extern/              <- git submodules / external dependencies
    /middleware/          <- vendor middleware sources
```

**Note:** `IDA -> {PRX, POI}` is an allowed dependency set. A feature may include only PRX, only POI, or both (Section 2.3).

### 3.1.1 Legacy Layout Migration

Legacy folder layouts (`/modules/`, `/platform/`, `/core/config/`) are not part of the normative specification.
For migration guidance, see `guides/02_Execution_Guides/EG_02_Refactoring_Legacy.md`.

---

## 3.2 Conceptual Model (Domain Boundaries)

Domain dependency direction:

```
Project feature policies -> Infra capability
Infra capability -> { Platform subdomain, Dependency repository integrations }
```

Architecture layers exist *within* project features and bootstrap core scope.
The full dependency diagram, allowed sets, and execution plane model are
defined in **Section 5** (§5.1–§5.4).

---

## 3.3 Where Each Rule Lives

This document describes structure and conceptual mapping.
For normative constraints:

| If you need... | Read... |
|---------------|---------|
| Layer roles and constraints | Section 4 |
| `#include` direction and dependency rules | Section 5 |
| Error handling rules | Section 6 (+ Appendix A) |
| Folder layout conventions | Section 7 |
| Naming scheme | Section 8 |
| Anti-patterns | Section 10 |
| Verification checklist | Section 11 |
| Version and transition notes | Section 12 |

---

## 3.4 Layer Relationship Inside a Feature

Layer roles and constraints are defined in **Section 4**. Illustrative
example (ida_ → poi_ direct, no prx_ needed):

```c
/* ida_sensor.c — Idea owns mode decision and duty computation */
void Ida_Sensor_Run(void)
{
    uint8_t duty;
    if (target_mode == SENSOR_MODE_ECO) {
        duty = 30U;   /* policy: eco brightness */
    } else {
        duty = 80U;   /* policy: normal brightness */
    }
    Poi_Sensor_ApplyDuty(duty);
}

/* poi_sensor.c — Poiesis: mechanical HAL wrapper */
Result_t Poi_Sensor_ApplyDuty(uint8_t duty)
{
    return Hal_Pwm_SetDuty(SENSOR_PWM_CHANNEL, duty);
}
```

For a full IDA → PRX → POI example with Praxis translation, see §9.1.
For the substantive Idea pattern (state machine + policy + orchestration),
see §9.6.

---

## 3.5 Shared Runtime Component Hierarchy

Runtime-facing components are split across orthogonal planes:

- **Capability plane** (`/infra/*`): middleware/service/platform execution contracts
- **Data plane** (`stm_` under `/project/datastreams` or `/deps/*`): cross-feature runtime state/event flow

| Component | Plane | Behavior | State | Complexity |
|--------|-------|----------|-------|------------|
| **Middleware** | Capability | Protocol/timing orchestration | Yes | High |
| **Service** | Capability | Computation/transform | Minimal | Medium |
| **Datastream** | Data | Shared runtime state/event flow | Runtime values | Low |

---

## 3.6 Core Contract Header (Shared Interface)

The Core Contract header (`/infra/bootstrap/cfg_core.h`) contains shared types and interfaces that all layers can access.

```c
typedef enum {
    RESULT_OK,
    RESULT_FAIL,
    RESULT_BUSY,
    RESULT_UNSUPPORTED,
    RESULT_UNDEFINED
} Result_t;
```

It is shared contract vocabulary, not a feature resource.

The canonical definition of `Result_t` and result check macros is
provided by the standard package `cfg_core_std.h` (Section 14.2).
Projects that adopt comsect1-std include these types transitively by
having `cfg_core.h` include `cfg_core_std.h`. Projects may also define
these types directly in `cfg_core.h` without adopting comsect1-std.

### 3.6.1 Contract Vocabulary vs Target Configuration

`cfg_core.h` holds contract vocabulary (`Result_t`, `Ida_Interface_t`, `Ida_Id_t`).

`cfg_project.h` holds target configuration (MCU, pins, clocks, build mode).

Rule:
- If a type is required to construct/consume `Ida_Interface_t`, it belongs in `cfg_core.h`.
- If a definition configures target behavior, it belongs in `cfg_project.h`.

---

## 3.7 Resource Categories

For canonical definitions, see **Section 2.7.4**.

| Prefix | Meaning | Typical mutability | Who accesses |
|--------|---------|--------------------|--------------|
| `cfg_` | compile-time configuration | immutable | Praxis/Poiesis |
| `db_`  | compile-time static data tables | immutable | Praxis/Poiesis |
| `stm_` | runtime datastream | mutable | Praxis/Poiesis |

Idea can use contract types via `cfg_core.h`, but never accesses feature resources directly.

---

## 3.8 Feature-Centric Structure and AIAD

Feature-centric layout supports AI-assisted development by:

1. **Intent visibility**: `ida_`, `prx_`, `poi_`, resources are co-located
2. **Bounded context**: feature folders are clear working units
3. **Explicit dependency cues**: prefixes expose architectural roles directly

AI assists implementation and analysis, but humans remain responsible for intent and architecture decisions.

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
