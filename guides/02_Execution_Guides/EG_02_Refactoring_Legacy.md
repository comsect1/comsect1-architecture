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
- repo-root build references that select MCU/BSP/platform code paths

### 1.2 Smell Checklist

| Symptom | Severity | Direction |
|--------|----------|-----------|
| business logic mixed with HAL calls | high | split ida/poi |
| protocol parsing buried in wrappers | high | isolate prx |
| cross-feature direct include | high | replace with `stm_` |
| idea directly reading cfg/db/stm | high | route through prx/poi |
| giant prx with mixed concerns | high | split prx+poi |
| ida_ has only init/main/GetInterface | critical | FIX-RF-1: move domain logic to ida_ |
| prx_ larger than ida_ | critical | FIX-RF-3: split translation from decisions |
| poi_ contains if/switch on domain keywords | high | FIX-RF-2: move decisions to ida_ |
| poi_ functions are single-call wrappers to prx_ | medium | FIX-RF-4: register prx_ directly |

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

During planning, treat direct vendor/device/BSP/CMSIS includes, raw register
symbols, and board wiring APIs as platform evidence even when they appear in
`svc_`, `mdw_`, feature files, or legacy folders.

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

#### 3.4.0 Two-Tier Balance Enforcement

Layer balance enforcement operates in two tiers. Both tiers are mandatory.

**Tier 1 — Gate Detection**: Run the gate script. If any of the following
rules fire, apply the corresponding fix procedure in Section 3.4.1:

| Gate rule | Severity | Trigger |
|-----------|----------|---------|
| `layer-balance` | error | ida_ < 10 code lines AND poi_ has domain conditionals |
| `red-flag-empty-idea` | warning | ida_ < 10 code lines |
| `red-flag-fat-poiesis` | warning | poi_ contains domain-semantic conditionals |
| `red-flag-fat-praxis` | warning | prx_ has code but no domain-semantic conditionals |
| `red-flag-poi-wrapper` | warning | poi_ has 2+ pure pass-through functions to prx_ |

**Tier 2 — Manual Balance Review**: If the gate reports zero red flags for a
feature, the refactoring agent MUST still perform a manual balance check:

1. Compare code line counts: `ida_` vs `prx_` and `ida_` vs `poi_`.
2. If `ida_` is smaller than or equal in size to `prx_` or `poi_`, Tier 2
   triggers.
3. When Tier 2 triggers, re-read the following spec sections and re-evaluate
   every function in the feature against them:
   - §4.1.2 Idea Responsibility Catalog
   - §4.1.3 PRX scope rule
   - §10.5 Anemic Idea
   - §10.6 Praxis Scope Overflow
4. For each function in `prx_`/`poi_` that contains domain-meaningful logic
   (state transitions, policy evaluation, threshold comparison, dispatch
   decisions, orchestration sequences), apply the 3-Question Discriminator
   and record the result.
5. Move all functions that answer Q1 with "No" to `ida_`.
6. For functions that answer Q1 "Yes" and Q2 "Yes", split: judgment to
   `ida_`, external wrapping to `poi_`.

Tier 2 exists because the gate uses heuristic thresholds (10-line minimum,
regex-based conditional detection). A feature can pass the gate while
carrying domain logic in `prx_`/`poi_` that the heuristics do not detect.

> **Governing principle**: In a well-structured feature, `ida_` is the
> **heaviest logic layer** (§4.1.2). `prx_` and `poi_` are thin adapters
> for external dependencies that `ida_` cannot resolve internally. If
> `ida_` contains only `init`/`main`/`GetInterface` and delegates to
> `prx_`/`poi_`, the feature is structurally wrong regardless of gate
> result.

#### 3.4.1 Canonical Fix Procedures (Per Structural Error)

When the gate reports **errors** (not warnings), apply the matching
procedure below before proceeding to red-flag analysis.

##### FIX-LAY: Layout Violations (`layout.*`)

**Trigger**: `layout.required`, `layout.legacy`, `layout.examples_misplaced`,
`layout.api-misplaced`, `layout.root_boundary`.

**Procedure**:
1. Create missing required directories per §7.5 skeleton.
2. For `layout.legacy`: move contents of legacy folders (`/modules/`,
   `/platform/`, `/core/config/`, `/features/`) to canonical locations.
   Do NOT delete legacy folders until all contents are relocated and
   build passes.
3. For `layout.examples_misplaced`: move `examples/` outside `/comsect1`.
4. For `layout.api-misplaced`: create `/api` at comsect1 root and move
   public headers there.

**Cascading prevention**:
- Create canonical directories BEFORE moving files (Step 1 of §3.2).
- Update build include paths in the same work unit as the file move.
- Do NOT rename files during layout moves — naming fixes are a separate step.

##### FIX-NAM: Naming Violations (`naming.*`)

**Trigger**: `naming.prefix`, `naming.unit_qualified`, `naming.api_anchor`,
`naming.unit_conflict`, `naming.anchor_mismatch`, `naming.missing_unit_anchor`,
`naming.service_export`, `naming.service_header_export`.

**Procedure**:
1. For `naming.prefix` (invalid `inf_`): rename to the correct role prefix
   per §8.5. Apply 3-Question Discriminator to determine the correct prefix.
2. For `naming.unit_qualified`: append `_<unit>` suffix per §8.6.
3. For `naming.missing_unit_anchor`: rename `cfg_project.h` to
   `cfg_project_<unit>.h` per §8.6.1.
4. For `naming.service_export`/`naming.service_header_export`: rename
   exported functions to use `Svc_<Module>_` prefix.

**Cascading prevention**:
- After renaming, update ALL `#include` statements and build source lists
  in the same commit. A partial rename breaks the build.
- Run `rg -n "<old_name>"` across the tree to find all references.

##### FIX-PATH: Path Placement Violations (`path.*`)

**Trigger**: `path.bootstrap`, `path.infra_service`, `path.infra_hal`,
`path.infra_bsp`, `path.app`, `path.deps_middleware`, `path.project_feature`,
`path.project_config`, `path.feature_resource`, `path.datastream`.

**Procedure**:
1. Move the file to its canonical location per §7.5 and §8.2.
2. Update all `#include` paths that reference the moved file.
3. Update build system source lists and include paths.

**Cascading prevention**:
- Move one file (or one feature's files) at a time. Build after each move.
- Do NOT change file contents during a path move — content refactoring is
  a separate step (§3.4 Step 3).

##### FIX-DEP: Dependency Direction Violations (`ida.include`, `prx.include`,
`poi.include`, `ida_core.include`, `poi_core.include`, `prx_core.include`,
`include.deps_path`, `resource.include`, `module.include`, `module.resource`,
`platform.include`, `platform.direction`)

**Trigger**: Any include/dependency error from CAT-4.

**Procedure**:
1. Identify the forbidden include and the spec rule it violates
   (use `.comsect1-spec-index.json` for the exact §).
2. Determine where the needed functionality should be accessed from:
   - If `ida_` includes `mdw_`/`svc_`/`hal_`: route through `prx_` or `poi_`.
     Create a wrapper function in the appropriate layer.
   - If `ida_` includes `cfg_`/`db_`/`stm_`: pass the needed value as a
     parameter from `prx_`/`poi_`, or move the logic that needs the
     resource to `prx_`/`poi_`.
   - If `prx_`/`poi_` includes another feature's layer file: replace with
     `stm_` datastream access.
   - If `resource.include` (cfg_/db_/stm_ includes ida_/prx_/poi_): remove
     the upward include. Resources are pure data.
   - If `platform.direction` (bsp_ includes hal_): reverse the dependency.
     HAL may depend on BSP, not vice versa (§4.3.2).
3. Remove the forbidden `#include`.

**Cascading prevention**:
- When creating wrapper functions in `prx_`/`poi_`, ensure the new function
  does NOT contain domain logic — keep it mechanical. Otherwise you create
  a Fat Poiesis or Praxis Scope Overflow.
- When replacing cross-feature includes with `stm_`, define the datastream
  header in `/project/datastreams/`, not inside either feature folder.

##### FIX-OOP: OOP Dependency Violations (CAT-5)

**Trigger**: `ida-no-*`, `cross-feature-layer-ref`, reverse dependency refs.

**Procedure**:
1. For `ida-no-*` (forbidden namespace): move the external API call to
   `poi_`. Create a domain-neutral interface that `ida_` calls and `poi_`
   implements (§A2.5.4).
2. For reverse dependency (`prx_`/`poi_` referencing `ida_`): use
   composition. If `poi_` needs to call `ida_`, the design is inverted —
   `ida_` should call `poi_`, not the other way around.
3. For `cross-feature-layer-ref`: introduce `stm_` shared state container
   (§A2.5.8).

##### FIX-PLAT: Platform Boundary Violations (`platform.misplaced`,
`platform.misplaced.build`)

**Trigger**: Non-platform file owns raw platform coupling.

**Procedure**:
1. Identify all platform evidence in the file: vendor includes, register
   symbols, board wiring APIs.
2. Extract peripheral abstraction → create/move to `hal_` file under
   `/infra/platform/hal/`.
3. Extract board wiring → create/move to `bsp_` file under
   `/infra/platform/bsp/`.
4. Replace direct platform access in the original file with `hal_`/`bsp_`
   API calls.
5. For build evidence: update build paths from legacy `platform/`/`port/`
   to `/infra/platform/`.

**Cascading prevention**:
- Do NOT mix HAL and BSP in one file. If the extracted code has both
  peripheral abstraction and board wiring, split into two files.
- After extraction, verify the original file no longer triggers
  `platform.misplaced`.

##### FIX-SVC: Service Ownership Violations (`service.*`, `structure.dead_shell`)

**Trigger**: `service.file-facade`, `service.public-nonservice-delegate`,
`service.public-backend-bounce`, `service.internal-public-bounce`,
`structure.dead_shell`.

**Procedure**:
1. For `service.file-facade` / `service.public-nonservice-delegate`:
   the `svc_` file is not a real service. Either:
   - (a) Inline the delegated logic into the `svc_` and own it, OR
   - (b) Remove the `svc_` file and have consumers call the actual
     owner directly (if the owner is an allowed dependency).
2. For `service.public-backend-bounce`: merge the backend function into
   the public API or remove the extra membrane.
3. For `service.internal-public-bounce`: replace the public API call with
   the internal function call.
4. For `structure.dead_shell`: delete the empty file or implement the
   service logic.

**Cascading prevention**:
- Before removing a `svc_` file, check all consumers. Update their
  includes and calls.
- After consolidation, verify the remaining `svc_` passes the
  service justification criteria (§4.2.3.3).

#### 3.4.2 Canonical Fix Procedures (Per Red Flag — CAT-8/9)

When a red flag is detected (Tier 1) or a balance violation is found
(Tier 2), apply the corresponding procedure below. Each procedure is
designed to avoid triggering secondary violations.

##### FIX-RF-1: Empty Idea / Anemic Idea

**Trigger**: `red-flag-empty-idea`, `layer-balance`, or Tier 2 finding
that `ida_` is smaller than `prx_`/`poi_`.

**Danger level**: Highest. An `ida_` with only `init`/`main` forwarding
functions means the feature has no architectural contract surface.

**Root cause**: Misreading "WHAT/WHEN" as "which features exist and when
to boot them." All domain logic was pushed to `prx_`/`poi_` (§10.5).

**Procedure**:

1. Read `ida_` and list every function. Identify which are pure forwarding
   (single call to `prx_`/`poi_` with no conditional or computation).
2. Read `prx_` and `poi_`. For each function, classify:
   - Does it contain `if`/`switch`/`case` with domain-meaningful conditions?
   - Does it perform domain computation (conversion, normalization, averaging)?
   - Does it implement state transitions or scheduling policy?
   - Does it evaluate thresholds, guards, or acceptance criteria?
3. For each "yes" answer, apply the 3-Question Discriminator:
   - Q1=No → move entire function to `ida_`.
   - Q1=Yes, Q2=Yes → split: domain judgment to `ida_`, external wrapping
     stays in `poi_`.
   - Q1=Yes, Q2=No, Q3=Yes → keep in `prx_`, but only the **minimum
     translation**. Post-translation decisions move to `ida_`.
   - Q1=Yes, Q2=No, Q3=No → keep in `poi_`.
4. After moving, update `ida_` to call the remaining `prx_`/`poi_`
   functions and own the dispatch/orchestration logic.
5. Verify: `ida_` must now be the largest file in the feature.

**Cascading violation prevention**:
- Do NOT move external-type-coupled translation out of `prx_`. Only move
  the post-translation logic.
- Do NOT create new `#include` in `ida_` for `cfg_`/`db_`/`stm_`/`mdw_`/
  `svc_`/`hal_`/`bsp_`. If the moved logic needs these, it must receive
  values through parameters from `prx_`/`poi_`, or the logic is not
  pure domain and must stay below `ida_`.
- Do NOT break the `ida_` → `prx_`/`poi_` dependency direction. `ida_`
  calls down; `prx_`/`poi_` never call up.

##### FIX-RF-2: Fat Poiesis

**Trigger**: `red-flag-fat-poiesis` or Tier 2 finding.

**Root cause**: Domain decisions were placed in `poi_` during initial split,
typically because the decision is adjacent to a HAL/OS call (§10.4).

**Procedure**:

1. In `poi_`, identify every conditional with domain-meaningful keywords
   (mode, state, threshold, enable, disable, level, type, flag).
2. For each conditional:
   - Can the decision be expressed without external types? → Move to `ida_`.
   - Does the decision require external type context? → Move to `prx_`
     (translation portion only).
3. Replace the removed conditional in `poi_` with a parameter or enum
   received from `ida_`. `poi_` executes mechanically based on the value
   `ida_` provides.

**Cascading violation prevention**:
- The new parameter/enum type belongs in `cfg_core.h` (if cross-feature)
  or in the `ida_` header (if feature-local).
- Do NOT introduce `poi_` → `ida_` reverse includes to make the moved
  logic work. The interface direction is always `ida_` → `poi_`.

##### FIX-RF-3: Fat Praxis / Praxis Scope Overflow

**Trigger**: `red-flag-fat-praxis` or Tier 2 finding that `prx_` > `ida_`.

**Root cause**: `prx_` was used as a "convenient middle ground" (§DP-03
Anti-Pattern). Translation and post-translation decisions are merged in
one function (§10.6).

**Procedure**:

1. In each `prx_` function, identify the **boundary crossing point**: the
   line where external-type data becomes domain-neutral.
2. Everything before and including the boundary crossing stays in `prx_`.
3. Everything after the boundary crossing (dispatch, policy evaluation,
   state transitions, publish) moves to `ida_`.
4. `prx_` returns a domain-neutral result (struct, enum, primitive).
   `ida_` receives it and makes all subsequent decisions.

**If `prx_` has no domain conditionals at all** (pure `get`/`set`/
`read`/`write` wrappers):
- These are `poi_` functions. Move them to `poi_`.
- Remove the `prx_` file if no genuine translation remains.

**Cascading violation prevention**:
- The domain-neutral return type from `prx_` must not require `ida_` to
  include the external type's header. Define the return type in the `prx_`
  header or in `cfg_core.h`.
- After splitting, verify `prx_` still has the 4-criterion justification
  (§DP-03 Section 5). If not, demote remaining code to `poi_`.

##### FIX-RF-4: Poi Wrapper (Pass-through to Prx)

**Trigger**: `red-flag-poi-wrapper`.

**Root cause**: `poi_` functions exist only to forward calls to `prx_`.
This typically means the ops-table or callback registration references
`poi_` when it should reference `prx_` directly.

**Procedure**:

1. Identify each `poi_` function that is a single-call pass-through to a
   `prx_` function.
2. Update the ops table, callback registration, or `ida_` call site to
   reference the `prx_` function pointer directly.
3. Remove the pass-through `poi_` functions.
4. If `poi_` becomes empty after removal, delete the `poi_` file only if
   the feature has no other mechanical wrapping needs.

**Cascading violation prevention**:
- Verify that the ops table or `ida_` call site does not now need to
  include `prx_` headers that violate dependency direction. If `ida_`
  already includes its own `prx_` header, this is safe.
- Do NOT remove `poi_` if it still contains non-pass-through functions.

#### 3.4.3 Post-Fix Verification Sequence

After applying any fix procedure above, execute this sequence before
proceeding to Step 4:

1. **Build**: debug + release must pass.
2. **Gate**: re-run `Verify-Comsect1Code.py` or `Verify-OOPCode.py`.
3. **Tier 2 re-check**: compare `ida_` size vs `prx_`/`poi_` again.
4. **Requirement test**: pick one likely business requirement change for
   the feature. Verify it would primarily modify `ida_`, not `prx_`/`poi_`.

If Tier 2 still triggers after fix, re-read §4.1.2 and repeat the
discriminator analysis. Do not proceed until `ida_` is the heaviest
layer or an explicit justification exists (documented in a comment at
the top of `ida_` explaining why the feature's domain logic is minimal).

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

**Misplaced platform cleanup:**

After layer cleanup, review whether platform responsibility is still sitting in
non-platform files:
- raw vendor/device/BSP/CMSIS includes outside `/infra/platform/`
- direct register, interrupt, or board-wiring symbols outside `hal_`/`bsp_`
- build files referencing legacy `platform/` or `port/` paths instead of the final `/infra/platform/` structure

Do not mark HAL/BSP as absent while those signals already exist elsewhere in
the tree. Extract and relocate the responsibility instead.

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
- [ ] `ida_` is the largest layer file in every feature (Tier 2 balance check)
- [ ] no `ida_` consists solely of init/main/GetInterface forwarding
- [ ] requirement test passed: a business change would primarily modify `ida_`

### 5.2 Dependencies

- [ ] no `ida_` include of `mdw_`/`svc_`/`hal_`/`bsp_`/`cfg_`/`db_`/`stm_`
- [ ] no cross-feature direct include of `ida_`/`prx_`/`poi_`
- [ ] `stm_` used for feature-to-feature runtime sharing

### 5.3 Middleware Type Contracts

When external middleware dependencies are replaced, forked, or upgraded
(e.g., `add_subdirectory` targets, git submodules), verify that shared
type contracts have not changed silently.

Required checks after any middleware swap:

- [ ] struct field semantics: confirm that field names with unchanged types
      still carry the same meaning (e.g., `lenTotal` may or may not include
      NAD/PCI overhead depending on the middleware version)
- [ ] length/offset conventions: verify every consumer that computes array
      offsets or minimum-length guards from middleware-provided values
- [ ] callback invocation context: confirm that middleware callbacks are
      still invoked at the same point in the processing pipeline (ISR vs
      task context, before vs after transport assembly)
- [ ] return value semantics: confirm that `RESULT_OK`/`RESULT_FAIL` or
      equivalent status codes carry the same meaning

**Known incident**: `hatbit-lib-lin-stack` changed
`LinDiagRequest_t.lenTotal` from `NAD + SID + data` to `SID + data`
(PCI LEN field, NAD excluded). All consumer length checks and payload
extraction offsets required a `-1` adjustment. This caused all
multi-frame NcId write commands to silently reject.

### 5.4 Verification

- [ ] debug build passes
- [ ] release build passes
- [ ] grep checks show no prohibited patterns

Example grep checks:

```powershell
rg -n "#include .*features/.*/(ida_|prx_|poi_)" codes/
rg -n "#include .*\b(mdw_|svc_|hal_|bsp_|cfg_|db_|stm_)" codes/comsect1/project/features/*/ida_*.c
```

### 5.5 Boundary Cleanup

- [ ] no legacy layout folders remain (`/modules/`, `/platform/` at root, etc.)
- [ ] no files outside canonical locations within `/comsect1`
- [ ] non-comsect1 files moved outside `/comsect1` boundary
- [ ] no orphaned/unused headers or sources from pre-migration
- [ ] build system references match final folder structure
- [ ] repo-root build files reviewed for MCU/BSP branches, BSP include paths, BSP target links, and dummy fallbacks
- [ ] missing `hal_`/`bsp_` is not called absent when platform-coupled code still exists elsewhere

### 5.6 Documentation

- [ ] architecture docs updated to 3-layer terminology
- [ ] change recorded as architecture update in version history

---

## 6. Practical Tips

- prefer many small PRs over one large rewrite
- keep behavior unchanged while moving responsibilities
- after each phase: build, grep, checklist review

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.1**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

You are free to:
- **Share** - copy and redistribute the material in any medium or format for non-commercial purposes only.

Under the following terms:
- **Attribution** - You must give appropriate credit to the author (Kim Hyeongjeong), provide a reference to the license, and indicate if changes were made.
- **NonCommercial** - You may not use the material for commercial purposes.
- **NoDerivatives** - If you remix, transform, or build upon the material, you may not distribute the modified material.

No additional restrictions - You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
