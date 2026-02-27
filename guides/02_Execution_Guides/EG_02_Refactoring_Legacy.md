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

Migration follows a spatial-first progression: establish physical structure before semantic refactoring.

1. **Scaffold** canonical folder structure (empty skeleton per Section 7.5)
2. **Place** existing files into canonical folders; split unseparated files into `ida_`/`prx_`/`poi_`
3. **Verify & refactor** layer roles, balance, and dependency direction
4. **Clean up** non-conformant remnants (legacy folders, orphaned files, boundary violations)

### 2.3 Risk Control

- keep each phase buildable
- avoid large unverified batch moves
- run dependency grep after each phase

---

## 3. Execution Phase

### 3.1 Build Safety Net

Before edits, confirm the legacy project builds:

```powershell
cmake -S cmake -B .cmakeBuild -G Ninja -DCMAKE_BUILD_TYPE=Debug
ninja -C .cmakeBuild
```

### 3.2 Step 1: Scaffold Canonical Folder Structure

Create the canonical folder skeleton (Section 7.5) before moving any files.

```text
/comsect1
  /project
    /config
    /datastreams        (optional)
    /features
  /infra
    /bootstrap
    /service
    /platform
      /hal
      /bsp
  /deps
    /extern
    /middleware
```

This step produces empty directories only — no files are moved yet.

Verify: folder tree matches the reference structure in Section 7.5.

### 3.3 Step 2: File Placement and Layer Separation

Move existing files into the canonical folder structure. Two sub-operations:

**(a) Direct placement** — files that already carry correct role prefixes (`ida_`, `prx_`, `poi_`, `cfg_`, `db_`, `stm_`, `hal_`, `bsp_`, `svc_`, `mdw_`) are moved to their canonical location.

**(b) Split and placement** — monolithic or unseparated files are decomposed using the 3-question discriminator (Section 2.3):

1. Extract raw HAL/OS wrappers → `poi_<feature>.c`
2. Keep external-type interpretation with domain meaning → `prx_<feature>.c`
3. Move business decisions → `ida_<feature>.c`

Each feature should end with at minimum `ida_` + `poi_`; `prx_` only when the discriminator requires it.

Build after each feature placement to maintain buildability.

### 3.4 Step 3: Layer Role & Balance Check → Refactoring

After physical placement is complete, verify and refactor the content of each layer.

**Layer balance check** (Section 11.8, Layer Balance Invariant):
- `ida_` must contain domain decisions (conditionals with business meaning).
  One-line forwarding is an **Empty Idea violation**.
- `poi_` must not contain domain-semantic conditionals.
  If `poi_` has `if/switch/case` based on business rules, those belong in `ida_`.
- `prx_` must not accumulate mechanical-only wrappers (move to `poi_`).

**Dependency direction cleanup** (Section 11.7):
- `ida_` includes only own `prx_`/`poi_` + `cfg_core.h`
- `prx_`/`poi_` do not include other feature headers

**Cross-feature refactoring:**

Forbidden legacy pattern:

```c
#include "features/sensor/prx_sensor.h"
```

Target pattern:

```c
#include "stm_sensor_data.h"
```

**Core pattern update:**
- `ida_core` remains policy owner
- `poi_core` performs scheduler/OS registration execution
- optional `prx_core` only if external-type interpretation is unavoidable

Build + grep verification after each refactoring unit.

**Service (`svc_`) lifecycle review:**

After layer refactoring, review all `svc_` files affected by the migration:
- If a feature that consumed a `svc_` was modified or removed, assess whether the `svc_` is still needed, should be consolidated with another, or should be removed.
- Ensure every `svc_` file has a header comment documenting its purpose and consumer features (Section 4.2.3).
- If uncertain about consolidation, consult the user before proceeding.

### 3.5 Step 4: Boundary Cleanup

After refactoring is complete, remove non-conformant remnants:

1. **Remove legacy folders** — delete empty legacy layout directories (`/modules/`, `/platform/` at project root, `/core/config/`, etc.)
2. **Move non-comsect1 files** — files that do not belong in comsect1 scope (e.g., application-level entry points, test harnesses, vendor code not in `/deps`) are moved outside the `/comsect1` boundary
3. **Remove orphans** — delete unused headers and sources that were superseded during migration
4. **Update build system** — ensure CMakeLists.txt, include paths, and source lists reflect the final folder structure

Final build verification (debug + release).

---

## 4. Case Study Pattern (Template)

### 4.1 Legacy Input

`legacy_sensor.c` contains:
- business decisions
- protocol byte parsing
- direct GPIO/PWM calls

### 4.2 Refactored Output

- `ida_sensor.c`: mode/threshold decisions
- `prx_sensor.c`: protocol-to-domain interpretation
- `poi_sensor.c`: HAL/OS wrapper calls

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

### 5.4 Boundary Cleanup

- [ ] no legacy layout folders remain (`/modules/`, `/platform/` at root, etc.)
- [ ] no files outside canonical locations within `/comsect1`
- [ ] non-comsect1 files moved outside `/comsect1` boundary
- [ ] no orphaned/unused headers or sources from pre-migration
- [ ] build system references match final folder structure

### 5.5 Documentation

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
