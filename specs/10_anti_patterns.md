# 10. Anti-patterns

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.

---

## 10.0 Why Anti-patterns Matter

Anti-patterns show what breaks when layer boundaries are violated.

---

## 10.1 Idea Directly Accessing Modules

**Violation:** Idea self-containment.

```c
/* ida_display.c */
#include "mdw_serial.h"   /* forbidden */
```

Impact:
- requirement logic becomes coupled to implementation detail
- module changes force Idea changes

---

## 10.2 Idea Accessing Feature Resources Directly

**Violation:** resource encapsulation.

```c
#include "cfg_sensor.h"  /* forbidden in ida_ */
#include "db_sensor.h"   /* forbidden in ida_ */
```

Impact:
- Idea leaks implementation assumptions
- feature portability drops

---

## 10.3 Praxis or Poiesis Calling Idea (Reverse Dependency)

**Violation:** dependency direction.

```c
/* prx_button.c */
#include "ida_ui.h"     /* forbidden */
```

Impact:
- circular coupling (`ida_ -> prx_/poi_ -> ida_`)
- poor testability and maintainability

---

## 10.4 PRX/POI Role Collapse

**Violation:** layer role clarity.

Patterns:
- `prx_` file contains mostly mechanical wrappers (must be `poi_`)
- `poi_` file contains protocol/domain interpretation (must be `prx_` or `ida_` split)

Use the 3-question discriminator (Section 2.3).

---

## 10.5 Anemic Idea (Idea as Thin Wrapper)

**Violation:** Idea is the contract subject (Section 1.6.1).

**Symptom:** `ida_` file consists primarily of:
- one-line forwarding calls to `prx_`/`poi_`
- a `GetInterface()` function with minimal or no domain logic
- init/main functions that immediately delegate without decision

Meanwhile, `prx_` or `poi_` files contain state machines, threshold
evaluations, policy decisions, or orchestration sequences.

```c
/* ida_feature.c -- WRONG: Anemic Idea */
void Ida_Feature_Main(void)
{
    Prx_Feature_DoEverything();  /* all logic pushed to prx_ */
}
```

**Root cause:** Misreading "WHAT/WHEN" as "which features exist and when
to boot them," or interpreting "pure intent" as "minimal code."

**Impact:**
- requirement changes modify `prx_`/`poi_` instead of `ida_`
- domain decisions become invisible, buried in implementation layers
- the feature loses its architectural contract surface

**Fix:** Apply the 3-Question Discriminator. Any logic that answers Q1
with "No" (no external dependency required) must move to `ida_`. This
includes state machines, policy evaluations, guard conditions, domain
computations, and orchestration sequences.

**Diagnostic:** If `ida_` is smaller than the corresponding `prx_` or
`poi_`, investigate. In a well-structured feature, `ida_` is typically
the largest layer.

---

## 10.6 Cross-feature Direct Include

**Violation:** feature isolation.

```c
#include "features/sensor/prx_sensor.h"  /* forbidden */
#include "features/sensor/poi_sensor.h"  /* forbidden */
```

Correct pattern:

```c
#include "stm_sensor_data.h"             /* allowed */
```

---

## 10.7 Resource Files Including Layer Headers

**Violation:** reverse dependency from data to logic.

```c
/* db_xxx.h */
#include "ida_xxx.h"   /* forbidden */
```

Resources must remain pure data.

---

## 10.8 Core Execution Layer Including HAL/BSP

**Violation:** core purity.

Core execution (`poi_core` by default) must not include HAL/BSP directly when platform init belongs to feature-owned initialization.

---

## 10.9 Platform Evidence Outside Platform

**Violation:** semantic placement.

Non-platform files directly include vendor/device/BSP/CMSIS headers or use raw
platform primitives.

Examples:
- `poi_sensor.c` including `sam.h` or `cmsis_device.h`
- `svc_crc.c` using `NVIC_` or `PORT_REGS`
- `cfg_board.h` owning board timer and clock wiring logic

Correct direction: extract peripheral abstraction into `hal_` and board wiring
into `bsp_`.

---

## 10.10 HAL/BSP Mixed Responsibility

**Violation:** platform role collapse.

One file simultaneously owns peripheral abstraction and board-specific wiring.

Examples:
- direct MCU register access in the same file as board clock, board pin, or
  board timer setup
- one file both wraps SERCOM/UART access and decides which board routing is used

Correct direction:
- `hal_`: peripheral-facing abstraction
- `bsp_`: board-facing composition and wiring

---

## 10.11 OOP-Specific Anti-patterns

The following anti-patterns apply when comsect1 is used with object-oriented languages. For the full treatment, see **Appendix B (A2)**.

### 10.11.1 Reverse Dependency via Inheritance

**Violation:** dependency direction (Section 2.7.3).

Praxis or Poiesis class inherits from Idea class, creating an implicit upward dependency.

Correct: use composition. Idea calls Praxis/Poiesis; it does not extend them.

### 10.11.2 Idea Holding Mutable State

**Violation:** Idea purity.

Idea class declares mutable instance fields. Stateful Idea introduces temporal coupling.

Correct: Idea methods are static/shared. State belongs in `cfg_`/`db_`/`stm_` or Praxis/Poiesis.

### 10.11.3 God-Class (Layer Collapse)

**Violation:** layer role clarity (Section 10.4).

A single class mixes UI handling, domain logic, external API calls, and state management.

Correct: apply the 3-Question Discriminator (Section 2.3) to decompose into `ida_`/`prx_`/`poi_`.

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
