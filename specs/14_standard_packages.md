# 14. Standard Packages

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.

---

## 14.0 Purpose

The three biggest obstacles when starting an embedded project with a
structured architecture are: defining a common type vocabulary, building
a task scheduler, and implementing persistent storage. Standard packages
address these first-day barriers by providing working, architecture-
compliant examples for each.

A **Standard Package** is a published, reusable package maintained by the
comsect1 architecture project. These three packages represent the
complete scope of what comsect1 provides beyond the specification itself.
Any additional middleware (communication stacks, sensor drivers, UI
frameworks, etc.) is the adopter's responsibility, built by applying the
same architectural principles defined in Sections 1-13.

Using a standard package is not required for comsect1 compliance.
Projects may define their own implementations for any responsibility
covered by a standard package. The packages exist as reference material
and reusable building blocks, not as mandatory dependencies.

---

## 14.1 Role and Status

Standard packages demonstrate comsect1 principles in working code:

- **Vocabulary example** (comsect1-std): shows how to structure
  `cfg_core.h` contract types for cross-unit consistency.
- **Middleware example** (comsect1-mdw-os, comsect1-mdw-storage_manager):
  shows how to build capability-plane middleware that integrates with the
  3-layer feature model and follows dependency direction rules.

### 14.1.1 Non-Compliance Clarification

Not using a standard package does not constitute architecture
non-compliance. A project that defines its own `Result_t` in `cfg_core.h`
without including `cfg_core_std.h`, or that uses FreeRTOS instead of
comsect1-mdw-os, is fully compliant as long as it follows the
architectural rules defined in Sections 1-13.

### 14.1.2 When to Use

Standard packages are recommended when:
- starting a new comsect1 project and wanting a proven baseline
- the standard package covers the exact responsibility needed
- cross-project type consistency is desired (comsect1-std)

---

## 14.2 comsect1-std (Vocabulary Example)

### 14.2.1 Purpose

Provides a canonical definition of architecture-level contract vocabulary
types. Projects that adopt it gain type-level consistency across multiple
comsect1 units.

### 14.2.2 Contents

| Symbol | Kind | Description |
|--------|------|-------------|
| `Result_t` | enum | `RESULT_OK`, `RESULT_FAIL`, `RESULT_BUSY`, `RESULT_UNSUPPORTED`, `RESULT_UNDEFINED` |
| `RESULT_IS_OK(r)` | macro | `((r) == RESULT_OK)` |
| `RESULT_IS_ERROR(r)` | macro | `((r) != RESULT_OK)` |

The header also re-exports `<stdint.h>`, `<stdbool.h>`, and `<stddef.h>`.

### 14.2.3 Include Chain (When Adopted)

When a project adopts comsect1-std, the recommended integration is for
`cfg_core.h` to include `cfg_core_std.h` as its first project-local
include, then extend with project-specific contract types.

```c
/* cfg_core.h -- project's Core Contract header */
#include "cfg_core_std.h"        /* canonical vocabulary from comsect1-std */

/* Project-specific contract vocabulary below this line */
typedef struct {
    /* ... project-specific fields ... */
} Ida_Interface_t;
```

Guidelines:
- `cfg_core.h` should not redefine types already defined in
  `cfg_core_std.h`.
- `cfg_core_std.h` must not include any project-specific header.

### 14.2.4 Placement (When Adopted)

`/deps/extern/comsect1-std/` as a git submodule.

---

## 14.3 comsect1-mdw-os (Middleware Example)

### 14.3.1 Purpose

Demonstrates how to build a cooperative task scheduler and delta-queue
software timer as comsect1-compliant middleware for bare-metal
environments.

### 14.3.2 API Surface

| Function Group | Purpose |
|----------------|---------|
| `Mdw_OS_Task_Init`, `Mdw_OS_Task_Create`, `Mdw_OS_Task_Post`, `Mdw_OS_Task_RunOnce` | Task lifecycle |
| `Mdw_OS_Timer_Start`, `Mdw_OS_Timer_Stop`, `Mdw_OS_Timer_Handler` | Software timer |
| `Mdw_OS_Port_InitSystemTimer`, `Mdw_OS_Port_StartScheduler` | Platform port |

### 14.3.3 Self-Containment

comsect1-mdw-os defines its own result type (`mdw_os_Result_t`) and does
not depend on `cfg_core_std.h` or any project-specific header. This
demonstrates the middleware self-containment principle: middleware is
compilable without any project context.

### 14.3.4 Integration Pattern

When adopted, projects wrap comsect1-mdw-os through a service or `poi_`
adapter. `ida_` must not include `mdw_os` headers directly (Section 5,
Section 13).

Canonical integration:

```
/infra/service/os/svc_os.c     <- wraps Mdw_OS_Task_* / Mdw_OS_Port_*
/infra/bootstrap/poi_core.c    <- calls Svc_OS_* for scheduler start
```

### 14.3.5 Placement (When Adopted)

`/deps/extern/comsect1-mdw-os/` as a git submodule.

---

## 14.4 comsect1-mdw-storage_manager (Middleware Example)

### 14.4.1 Purpose

Demonstrates how to build flash storage middleware with Ping-Pong
dual-area architecture, CRC32 integrity verification, and runtime
configuration injection as a comsect1-compliant middleware unit.

### 14.4.2 API Surface

| Function Group | Purpose |
|----------------|---------|
| `Mdw_Storage_Setup`, `Mdw_Storage_Init` | Configuration and initialization |
| `Mdw_Storage_RegisterData`, `Mdw_Storage_RegisterKey` | Data registration |
| `Mdw_Storage_GetData`, `Mdw_Storage_GetDataPtr` | Data access |
| `Mdw_Storage_BeginEdit`, `Mdw_Storage_EndEdit`, `Mdw_Storage_CancelEdit` | Edit mode |
| `Mdw_Storage_MarkDirty`, `Mdw_Storage_Commit`, `Mdw_Storage_Format` | Persistence |

### 14.4.3 Internal Structure

comsect1-mdw-storage_manager follows the comsect1 fractal pattern
internally (Section 7, Section 13):

```
/comsect1/api/mdw_storage.h
/comsect1/infra/bootstrap/cfg_core_storage.h
/comsect1/project/features/manager/ida_manager_storage.c
/comsect1/project/features/manager/poi_manager_storage.c
```

It defines its own domain-specific error type (`Storage_Error_t`) in
`cfg_core_storage.h`. This type is not part of `cfg_core_std.h` because
it is domain-specific to storage.

### 14.4.4 Integration Pattern

When adopted, projects wrap comsect1-mdw-storage_manager through a
service or `poi_` adapter. Configuration is injected at runtime via
`Mdw_Storage_Setup()` -- the middleware has no compile-time dependency on
project config headers.

Canonical integration:

```
/infra/service/storage/svc_storage.c    <- wraps Mdw_Storage_* API
/project/features/storage/              <- project-specific storage feature
```

### 14.4.5 Placement (When Adopted)

`/deps/extern/comsect1-mdw-storage_manager/` as a git submodule.

---

## 14.5 General Rules

### 14.5.1 Gate Verification Scope

Standard packages under `/deps/extern/` are excluded from the consumer
project's gate verification. Each package is verified by its own gate.

### 14.5.2 Versioning

Standard packages follow semantic versioning.

### 14.5.3 Scope Boundary

The three packages listed in this section (comsect1-std, comsect1-mdw-os,
comsect1-mdw-storage_manager) define the complete scope of standard
packages provided by the comsect1 architecture project. The architecture
specification itself may evolve, but no additional submodules are planned
under the comsect1 name. Further middleware and libraries are the
adopter's domain.

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
