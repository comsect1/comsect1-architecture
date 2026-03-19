# 11. Self-Verification Checklist

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.

---

## 11.0 Overview (Non-normative)

Before considering architecture work complete, verify layer placement and dependency direction.

---

## 11.1 Idea Layer Verification

- [ ] Idea contains business decision logic (WHAT/WHEN/WHICH)
- [ ] Idea contains substantive domain logic (state machines, policy
  evaluations, orchestration sequences, guard conditions) -- not merely
  forwarding calls
- [ ] Idea is readable as requirements-level intent
- [ ] Idea self-containment verified (§4.1.2): only `cfg_core.h` and own `prx_`/`poi_`

---

## 11.2 Praxis Layer Verification

- [ ] Praxis contains externally-coupled domain interpretation
- [ ] Praxis is limited to external type boundary translation; post-translation
  decisions (dispatch, orchestration, policy) are in Idea (Section 4.1.3 PRX scope rule)
- [ ] Praxis may call own `poi_` and `mdw_`/`svc_`/`hal_`/`cfg_`/`db_`/`stm_`
- [ ] Praxis does not include another feature's `ida_`/`prx_`/`poi_`
- [ ] Praxis does not call upward into Idea
- [ ] If judgment can be separated from external types, that judgment is in Idea

---

## 11.3 Poiesis Layer Verification

- [ ] Poiesis performs mechanical wrapping/bridging/forwarding
- [ ] Poiesis may call `mdw_`, `svc_`, `hal_`, and use `cfg_`, `db_`, `stm_`
- [ ] Poiesis does not include another feature's `ida_`/`prx_`/`poi_`
- [ ] Poiesis does not contain business decisions

---

## 11.4 Feature Isolation Verification

- [ ] Features communicate only through datastream (`stm_`)
- [ ] No direct include of another feature's `ida_`/`prx_`/`poi_`/`cfg_`/`db_`
- [ ] `ida_core.c` is the only file that includes feature `ida_*.h`
- [ ] Each feature exports idea interface object (stable ID + init/main + metadata)

---

## 11.5 3-Question Discriminator Verification

For every file that touches external dependencies:

- [ ] Q1: If external dependency is not required, file is in Idea
- [ ] Q2: If separable judgment exists, judgment is moved to Idea
- [ ] Q3: If judgment is inseparable from external type, file is Praxis; otherwise Poiesis

---

## 11.6 Resource Access Verification

- [ ] `cfg_core_<unit>.h` is treated as contract vocabulary and allowed in all layers
- [ ] `cfg_project_<unit>.h`, feature `cfg_`, feature `db_` are accessed only by Praxis/Poiesis
- [ ] `stm_` is accessed only by Praxis/Poiesis
- [ ] Capability components (`mdw_`, `svc_`) do not directly include project/feature resources

---

## 11.7 Dependency Direction Verification

Verify all include/import edges against the allowed sets and prohibited
directions defined in **Section 5** (§5.1–§5.4).

Key checks:
- [ ] Allowed set (§5.2.1): IDA uses only own PRX/POI
- [ ] Reverse dependency prohibition (§5.4): no PRX→IDA, no POI→IDA
- [ ] Cross-feature prohibition (§5.2.2): no Feature A→Feature B direct includes
- [ ] Platform direction (§5.4): no Platform→Feature reverse includes

---

## 11.8 Red Flags

| Red flag | Anti-pattern | Gate rule(s) |
|----------|-------------|--------------|
| Anemic Idea: ida_ primarily forwarding, smaller than prx_/poi_ | §10.5 | `layer-balance`, `red-flag-empty-idea` |
| Praxis Scope Overflow: PRX decodes, decides, and dispatches | §10.6 | `red-flag-praxis-overflow`, `red-flag-fat-praxis` |
| Fat Praxis: PRX holds mostly mechanical wrappers | §10.4 | `red-flag-fat-praxis` |
| Fat Poiesis: POI contains business/protocol interpretation | §10.4 | `red-flag-fat-poiesis` |
| Requirement changes modify only PRX/POI, Idea unchanged | §10.5 | (manual review) |
| Cross-feature includes outside `stm_` | §10.7 | `cross-feature-layer-ref`, `ida.include` |

Domain conditional detection is heuristic. The gate uses keyword pattern
matching (`DOMAIN_CONDITIONAL_RE`) which may match hardware state checks
(e.g., `HAL_STATE_IDLE`) in `poi_` files. Known hardware prefixes (`HAL_`,
`BSP_`, `UART_`, `SPI_`, etc.) are automatically excluded. For remaining
false positives, add the `GATE_MECHANICAL_CONDITIONAL` comment on the line
to suppress detection.

---

## 11.9 Infra Capability Verification

- [ ] `stm_` is used as data plane only (feature-to-feature runtime state/event).
- [ ] `svc_`/`mdw_`/`hal_` APIs stay capability-oriented (no feature policy embedding).
- [ ] Capability components do not include feature `ida_`/`prx_`/`poi_`.
- [ ] Non-platform files do not directly include vendor/device/BSP/CMSIS headers or raw platform symbols.
- [ ] Feature `prx_`/`poi_` consume platform through `hal_` APIs rather than direct device headers.
- [ ] Files mixing peripheral abstraction and board wiring are reviewed as HAL/BSP mixed responsibility.
- [ ] No unlisted file-role prefix exists (only prefixes from §8.5 are valid).
- [ ] Infra-integrated layout keeps dependency rules unchanged (no semantic relaxation by folder grouping).
- [ ] Each `svc_` file has a header comment stating computation purpose and consumer features.
- [ ] If a feature consuming a `svc_` was modified or removed, `svc_` consolidation/removal reviewed.

---

## 11.10 Migration Cleanup Verification

- [ ] Canonical folder skeleton (Section 7.5) is fully present
- [ ] No legacy layout folders remain (`/modules/`, `/platform/` at project root, etc.)
- [ ] No files exist outside canonical locations within `/comsect1`
- [ ] Files not belonging to comsect1 scope are moved outside `/comsect1` boundary
- [ ] No orphaned/unused headers or sources remain from pre-migration
- [ ] Build system references (include paths, source lists, target links, conditional source selection) match final folder structure
- [ ] Repo-root build files are reviewed for platform evidence (MCU/BSP macro branches, BSP include paths, BSP target links, dummy fallbacks)
- [ ] When platform-coupled code exists elsewhere, missing `hal_`/`bsp_` structure is treated as misplaced responsibility, not `<ABSENT>`

---

## 11.12 External Library Deployment Review

(Applicable when the project depends on external reference libraries —
`mdw_`, `svc_`, or third-party packages)

### 11.12.1 Discovery

- [ ] All external library dependencies are inventoried (git submodules, `add_subdirectory` targets, vendored copies)
- [ ] Each library's repository root is inspected for a deployment review document (e.g., `DEPLOYMENT_REVIEW.md`, `INTEGRATION_CHECKLIST.md`, or equivalent)
- [ ] If a library provides a deployment review procedure, that procedure is executed and results recorded in the project

### 11.12.2 Execution

For each library that provides a deployment review:

- [ ] Library-specific checklist items are completed with project-specific values
- [ ] All formulas and thresholds defined by the library are evaluated
- [ ] Pass/Fail summary is recorded per library

### 11.12.3 Known Library Reviews

| Library | Review Document | Scope |
|---------|----------------|-------|
| `hatbit-lib-mdw-storage-manager` | `DEPLOYMENT_REVIEW.md` | Flash key inventory, area layout, heap fitness, linker match, build artifacts, config audit |

When a library is not listed above but provides its own review procedure,
follow that procedure and consider adding it to this table.

---

## 11.11 Conformance Verification (Gate Execution)

### Gate Scripts

| Script | Scope | Purpose |
|--------|-------|---------|
| `scripts/Verify-Spec.py` | Specification files (`specs/*.md`) | Structural hygiene, cross-references, SSOT term consistency |
| `scripts/Verify-ToolingConsistency.py` | Generated AI tooling surfaces + generated blocks in `tooling/INSTALL.md` | Detect drift between generated adapters/skills/wrappers/common packaging blocks and the Python tooling SSOT |
| `scripts/Verify-Comsect1Code.py` | C/embedded source files | 3-layer dependency, placement, naming rules + Red Flag heuristics |
| `scripts/Verify-OOPCode.py` | OOP source files (`.cs`/`.vb`) | A2 adaptation rules, immutability, interface boundaries + Red Flag heuristics |
| `scripts/Verify-AIADGate.py` | Unified runner | Runs all applicable stages + Stage 0 meta-evaluation advisory |

### C/Embedded Rules (Verify-Comsect1Code.py)

| Rule family | Enforced |
|-------------|----------|
| Layer/dependency direction (`ida_`/`prx_`/`poi_`, reverse include bans) | Yes |
| Root folder convention (`/comsect1` boundary) | Yes |
| Unlisted role prefix (only §8.5 prefixes valid) | Yes |
| Infra/deps required-root checks (`layout.required`) | Yes |
| Placement/path checks (`path.*`) including `cfg_`/`db_`/`stm_` | Yes |
| Direct `deps/...` include path ban (`include.deps_path`) | Yes |
| Module resource purity (`module.resource`) | Yes |
| Resource include direction (`resource.include`) | Yes |
| Legacy layout detection (`layout.legacy`) | Yes (error) |
| Layer Balance Invariant: Empty Idea / Fat Poiesis (v1.0.1) | Yes (error) |
| Red Flag heuristics: Fat Praxis (§11.8) | Yes (advisory) |

All structural rules and Layer Balance violations produce errors. Red Flag heuristics produce advisory warnings.

### OOP Rules (Verify-OOPCode.py)

| Rule family | Enforced |
|-------------|----------|
| Root folder convention (`/comsect1` boundary) | Yes |
| Folder structure skeleton (`layout.required`) | Yes |
| Unit identity detection + unit-qualified naming (`naming.unit_qualified`) | Yes |
| Extended role detection (all §8.5 prefixes: `ida_`–`app_`, `inf_` invalid) | Yes |
| Placement/path checks (`path.*`) including `cfg_`/`db_`/`stm_` | Yes |
| Unlisted role prefix detection (`naming.prefix`) | Yes |
| Idea forbidden imports and API calls (`ida-no-*`) | Yes |
| Reverse dependency checks (`prx_`→`ida_`, `poi_`→`ida_`/`prx_`) | Yes |
| Cross-feature layer references (`cross-feature-layer-ref`) | Yes |
| Module resource purity — `svc_`/`mdw_` must not import `cfg_`/`db_`/`stm_` (`module.resource`) | Yes |
| Service ownership OOP — thin facades, misclassified registries (`service.*`) | Yes |
| Orphan datastream detection (`datastream.orphan`) | Yes (advisory) |
| Dead shell detection — `svc_` with <3 code lines (`structure.dead_shell`) | Yes |
| Layer Balance Invariant: Empty Idea / Fat Poiesis (v1.0.1) | Yes (error) |
| Red Flag heuristics: Fat Praxis, Praxis Scope Overflow (§11.8) | Yes (advisory) |
| OOP-specific: ida_ feature resource access, ida_ mutable fields (A2.8.2) | Yes (advisory) |

All structural rules and Layer Balance violations produce errors. Red Flag and OOP-specific heuristics produce advisory warnings.

See `specs/A2_oop_adaptation.md` for full OOP adaptation rules.

### Static Analysis Scope

Gate scripts verify dependency direction and layer placement through static
analysis of `#include`/`import` statements and file naming conventions.
This scope does not cover runtime dependency paths: function-pointer
callbacks, event dispatch tables, and observer registrations can create
implicit coupling that static analysis cannot detect. Callback compliance
rules (§4.0.5) govern these paths; manual review is required to verify
them. When callback-heavy designs are used, document the registration
flow so reviewers can trace the runtime dependency direction.

### Execution

- Legacy folder layouts (`/modules/`, `/platform/`, `/core/config/`, `/features/`) are detected and reported as errors.
- For migration guidance, see `guides/02_Execution_Guides/EG_02_Refactoring_Legacy.md`.
- For Praxis layer decision criteria, see `guides/01_Design_Principles/DP_03_Praxis_Justification.md`.
- For multi-project gate configuration, see `guides/03_Verification/V_03_Multi_Project_Gate.md`.
- For upstream alignment after spec changes, see `guides/04_Meta_Evaluation/ME_01_Upstream_Alignment.md`.
- For application feedback and ADR process, see `guides/02_Execution_Guides/EG_05_Application_Feedback.md`.

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

