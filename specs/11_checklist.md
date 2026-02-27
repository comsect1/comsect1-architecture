# 11. Self-Verification Checklist

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.

---

## 11.0 Overview (Non-normative)

Before considering architecture work complete, verify layer placement and dependency direction.

---

## 11.1 Idea Layer Verification

- [ ] Idea contains business decision logic (WHAT/WHEN)
- [ ] Idea is readable as requirements-level intent
- [ ] Idea includes only `cfg_core.h` and own `prx_`/`poi_` headers
- [ ] Idea does not include `cfg_`, `db_`, `stm_`, `mdw_`, `svc_`, `hal_`, `bsp_`
- [ ] Idea does not include another feature's files

---

## 11.2 Praxis Layer Verification

- [ ] Praxis contains externally-coupled domain interpretation
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

- [ ] `cfg_core.h` is treated as contract vocabulary and allowed in all layers
- [ ] `cfg_project.h`, feature `cfg_`, feature `db_` are accessed only by Praxis/Poiesis
- [ ] `stm_` is accessed only by Praxis/Poiesis
- [ ] Capability components (`mdw_`, `svc_`) do not directly include project/feature resources

---

## 11.7 Dependency Direction Verification

Allowed:

```
IDA -> { own PRX, own POI }
PRX -> { own POI, mdw_, svc_, hal_, cfg_, db_, stm_ }
POI -> { mdw_, svc_, hal_, cfg_, db_, stm_ }
HAL -> BSP
```

Interpretation:
- `IDA -> { own PRX, own POI }` is an allowed dependency set.
- IDA may use PRX only, POI only, or both as required.

Prohibited:

```
PRX -> IDA
POI -> IDA
Feature A -> Feature B direct includes
Platform -> Feature reverse includes
```

---

## 11.8 Red Flags

- [!] Empty Idea: Idea is only one-line pass-through
- [!] Fat Praxis: PRX holds mostly mechanical wrappers
- [!] Fat Poiesis: POI contains business or protocol interpretation logic
- [!] Requirement changes modify only PRX/POI while Idea stays unchanged
- [!] Cross-feature includes exist outside `stm_`

---

## 11.9 Infra Capability Verification

- [ ] `stm_` is used as data plane only (feature-to-feature runtime state/event).
- [ ] `svc_`/`mdw_`/`hal_` APIs stay capability-oriented (no feature policy embedding).
- [ ] Capability components do not include feature `ida_`/`prx_`/`poi_`.
- [ ] No `inf_` file-role prefix exists.
- [ ] Infra-integrated layout keeps dependency rules unchanged (no semantic relaxation by folder grouping).

---

## 11.10 Conformance Verification (Gate Execution)

### Gate Scripts

| Script | Scope | Purpose |
|--------|-------|---------|
| `scripts/Verify-Spec.py` | Specification files (`specs/*.md`) | Structural hygiene, cross-references, SSOT term consistency |
| `scripts/Verify-Comsect1Code.py` | C/embedded source files | 3-layer dependency, placement, naming rules + Red Flag heuristics |
| `scripts/Verify-OOPCode.py` | OOP source files (`.cs`/`.vb`) | A2 adaptation rules, immutability, interface boundaries + Red Flag heuristics |
| `scripts/Verify-AIADGate.py` | Unified runner | Runs all applicable stages + Stage 0 meta-evaluation advisory |

### C/Embedded Rules (Verify-Comsect1Code.py)

| Rule family | Enforced |
|-------------|----------|
| Layer/dependency direction (`ida_`/`prx_`/`poi_`, reverse include bans) | Yes |
| Invalid role prefix (`inf_`) | Yes |
| Infra/deps required-root checks (`layout.required`) | Yes |
| Placement/path checks (`path.*`) including `cfg_`/`db_`/`stm_` | Yes |
| Direct `deps/...` include path ban (`include.deps_path`) | Yes |
| Module resource purity (`module.resource`) | Yes |
| Resource include direction (`resource.include`) | Yes |
| Legacy layout detection (`layout.legacy`) | Yes (error) |
| Red Flag: Empty Idea / Fat Poiesis (§11.8) | Yes (advisory) |

All structural rules produce errors. Red Flag heuristics produce advisory warnings.

### OOP Rules (Verify-OOPCode.py)

For OOP projects, `Verify-OOPCode.py` additionally enforces:

- Idea immutability and referential transparency (Appendix A2)
- Interface-Owned Layer Boundaries
- Praxis justification checks
- Red Flag heuristics (§11.8)

See `specs/A2_oop_adaptation.md` for full OOP adaptation rules.

### Execution

- Legacy folder layouts (`/modules/`, `/platform/`, `/core/config/`, `/features/`) are detected and reported as errors.
- For migration guidance, see `guides/02_Execution_Guides/EG_02_Refactoring_Legacy.md`.
- For Praxis layer decision criteria, see `guides/01_Design_Principles/DP_03_Praxis_Justification.md`.
- For multi-project gate configuration, see `guides/03_Verification/V_03_Multi_Project_Gate.md`.
- For upstream alignment after spec changes, see `guides/04_Meta_Evaluation/ME_01_Upstream_Alignment.md`.
- For application feedback and ADR process, see `guides/02_Execution_Guides/EG_05_Application_Feedback.md`.

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

