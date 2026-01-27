# comsect1 Legacy Code Refactoring Guide

> **Note:** The verification script no longer provides `Core` or `Legacy`
> conformance profiles. All rules are enforced as errors.
> This guide describes the migration path from legacy layouts to the normative structure.

Step-by-step guide for migrating legacy code to 3-layer architecture (`ida_`/`prx_`/`poi_`).

---

## 1. Assessment Phase

### 1.1 Current State Audit

Collect:
- file map
- dependency map (`#include` graph)
- hardware-touching call sites
- business decision hotspots

### 1.2 Smell Checklist

| Symptom | Severity | Direction |
|--------|----------|-----------|
| business logic mixed with HAL calls | high | split ida/poi |
| protocol parsing buried in wrappers | high | isolate prx |
| cross-feature direct include | high | replace with `stm_` |
| idea directly reading cfg/db/stm | high | route through prx/poi |
| giant prx with mixed concerns | high | split prx+poi |

### 1.3 Baseline Metrics

Track before/after:
- count of forbidden includes
- count of mixed-role files
- build status (debug/release)

---

## 2. Planning Phase

### 2.1 Classification Plan

Use 3-question discriminator for each legacy function:

1. external dependency needed?
2. separable domain judgment?
3. inseparable external-type-coupled judgment?

Map result:
- Idea (`ida_`)
- Praxis (`prx_`)
- Poiesis (`poi_`)

### 2.2 Migration Order (Recommended)

1. core execution (`prx_core` -> `poi_core` semantics in docs/code where possible)
2. platform-adjacent wrappers (`prx_*` wrappers -> `poi_*`)
3. protocol interpretation files (remain/convert to `prx_*`)
4. cross-feature dependency cleanup (`stm_` only)
5. guide/checklist/doc sync

### 2.3 Risk Control

- keep each phase buildable
- avoid large unverified batch moves
- run dependency grep after each phase

---

## 3. Execution Phase

### 3.1 Build Safety Net

Before edits:

```powershell
cmake -S cmake -B .cmakeBuild -G Ninja -DCMAKE_BUILD_TYPE=Debug
ninja -C .cmakeBuild
```

### 3.2 Mechanical Extraction

Typical extraction pattern:

1. move raw HAL/OS wrappers from legacy file to `poi_<feature>.c`
2. keep external-type interpretation in `prx_<feature>.c`
3. move decisions to `ida_<feature>.c`

### 3.3 Include Direction Cleanup

Required outcomes:
- `ida_` includes only own `prx_`/`poi_` + `cfg_core.h`
- `prx_`/`poi_` include no other feature headers
- feature-to-feature communication only via `stm_`

### 3.4 Cross-feature Refactor Pattern

Forbidden legacy pattern:

```c
#include "features/sensor/prx_sensor.h"
```

Target pattern:

```c
#include "stm_sensor_data.h"
```

### 3.5 Core Pattern Update

- `ida_core` remains policy owner
- `poi_core` performs scheduler/OS registration execution
- optional `prx_core` only if external-type interpretation is unavoidable

---

## 4. Case Study Pattern (Template)

### 4.1 Legacy Input

`legacy_motor.c` contains:
- business decisions
- protocol byte parsing
- direct GPIO/PWM calls

### 4.2 Refactored Output

- `ida_motor.c`: mode/threshold decisions
- `prx_motor.c`: protocol-to-domain interpretation
- `poi_motor.c`: HAL/OS wrapper calls

### 4.3 Acceptance Criteria

- business changes mostly touch `ida_`
- protocol interpretation changes touch `prx_`
- MCU/HAL changes mostly touch `poi_`/platform

---

## 5. Migration Checklist

### 5.1 Architecture

- [ ] every migrated function classified via 3-question discriminator
- [ ] no business logic left in `poi_`
- [ ] no mechanical-only wrapper left in `prx_`

### 5.2 Dependencies

- [ ] no `ida_` include of `mdw_`/`svc_`/`hal_`/`bsp_`/`cfg_`/`db_`/`stm_`
- [ ] no cross-feature direct include of `ida_`/`prx_`/`poi_`
- [ ] `stm_` used for feature-to-feature runtime sharing

### 5.3 Verification

- [ ] debug build passes
- [ ] release build passes
- [ ] grep checks show no prohibited patterns

Example grep checks:

```powershell
rg -n "#include .*features/.*/(ida_|prx_|poi_)" codes/
rg -n "#include .*\b(mdw_|svc_|hal_|bsp_|cfg_|db_|stm_)" codes/comsect1/project/features/*/ida_*.c
```

### 5.4 Documentation

- [ ] architecture docs updated to 3-layer terminology
- [ ] change recorded as architecture update in version history

---

## 6. Practical Tips

- prefer many small PRs over one large rewrite
- keep behavior unchanged while moving responsibilities
- after each phase: build, grep, checklist review

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
