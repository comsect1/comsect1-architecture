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

Domain dependency remains:

```
Project feature policies -> Infra capability
Infra capability -> { Platform subdomain, Dependency repository integrations }
```

Architecture layers exist *within* project features and bootstrap core scope.

```
Bootstrap core: ida_core -> poi_core
Feature: ida_ -> { prx_, poi_ }
prx_ -> { poi_, mdw_, svc_, hal_, cfg_, db_, stm_ }
poi_ -> { mdw_, svc_, hal_, cfg_, db_, stm_ }
```

Inter-feature communication remains datastream-only (`stm_`).

Execution boundaries are orthogonal:
- **Data plane**: `stm_` for feature-to-feature runtime state/event
- **Capability plane**: `mdw_`/`svc_`/`hal_`/`bsp_` and core execution wrappers

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

### Idea (`ida_`)

- Expresses business intent and decisions (WHAT/WHEN)
- Calls only its own `prx_` and/or `poi_` interfaces
- Does not include `cfg_`, `db_`, `stm_`, `mdw_`, `svc_`, `hal_`, or `bsp_` directly

### Praxis (`prx_`)

- Interprets external types/protocols when that interpretation has domain meaning
- May call own `poi_`
- May access `mdw_`, `svc_`, `hal_`, `cfg_`, `db_`, `stm_`

### Poiesis (`poi_`)

- Performs mechanical wrapping/bridging/forwarding
- May access `mdw_`, `svc_`, `hal_`, `cfg_`, `db_`, `stm_`
- Must not perform domain decision-making

Illustrative example:

```c
/* ida_motor.c */
void Ida_Motor_Run(void)
{
    if (target_mode == MOTOR_MODE_ECO) {
        Prx_Motor_InterpretAndApply(target_mode);
    } else {
        Poi_Motor_ApplyDuty(target_duty);
    }
}

/* prx_motor.c */
Result_t Prx_Motor_InterpretAndApply(MotorMode_t mode)
{
    uint8_t duty = (mode == MOTOR_MODE_ECO) ? db_motor_eco_duty : db_motor_normal_duty;
    return Poi_Motor_ApplyDuty(duty);
}

/* poi_motor.c */
Result_t Poi_Motor_ApplyDuty(uint8_t duty)
{
    return Hal_Pwm_SetDuty(MOTOR_PWM_CHANNEL, duty);
}
```

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
    RESULT_UNSUPPORTED,
    RESULT_UNDEFINED
} Result_t;
```

It is shared contract vocabulary, not a feature resource.

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
