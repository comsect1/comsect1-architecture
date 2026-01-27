# comsect1 Post-Task Verification Checklist

This checklist is mandatory after each development/refactoring task unit.
If any item fails, the task is not complete.

---

## A. Idea (`ida_`) Integrity Verification

1. Pure intent logic
- [ ] `ida_` contains WHAT/WHEN decisions only (no HOW implementation details).

2. No direct platform/module coupling
- [ ] `ida_` has zero direct `hal_`/`bsp_` calls.
- [ ] `ida_` does not include `mdw_`/`svc_` headers.

3. No direct resource coupling
- [ ] `ida_` does not include feature `cfg_`/`db_`/`stm_` directly.
- [ ] only `cfg_core.h` is included as shared contract vocabulary.

4. Feature isolation
- [ ] `ida_A` does not include any header from Feature B (`ida_`, `prx_`, `poi_`, `cfg_`, `db_`).

5. Allowed dependencies only
- [ ] `ida_` includes only own `prx_` and/or own `poi_` interfaces (+ `cfg_core.h`).

---

## B. Praxis (`prx_`) Role Compliance Verification

1. PRX role correctness
- [ ] `prx_` contains externally-coupled interpretation with domain meaning.

2. No business policy leakage
- [ ] `prx_` does not own WHAT/WHEN policy decisions that should live in `ida_`.

3. No mechanical-wrapper accumulation
- [ ] purely mechanical forwarding code is moved to `poi_`.

4. Dependency direction
- [ ] `prx_` includes only own `poi_` or lower domains (`mdw_`, `svc_`, `hal_`, `cfg_`, `db_`, `stm_`).
- [ ] `prx_` has no reverse include to `ida_`.

5. Inter-feature rule
- [ ] cross-feature access uses `stm_` only (no direct include of other feature headers).

---

## C. Poiesis (`poi_`) Role Compliance Verification

1. POI role correctness
- [ ] `poi_` code is mechanical execution (wrapping/bridging/forwarding).

2. No interpretation or policy
- [ ] `poi_` contains no domain interpretation that depends on external type semantics.
- [ ] `poi_` contains no business decision logic.

3. Dependency direction
- [ ] `poi_` depends only on lower domains/resources (`mdw_`, `svc_`, `hal_`, `cfg_`, `db_`, `stm_`).
- [ ] `poi_` has no reverse include to `ida_`.

4. Inter-feature rule
- [ ] `poi_` does not include another feature's `ida_`/`prx_`/`poi_`.

---

## D. Module (`mdw_`, `svc_`) Integrity Verification

1. No upward dependency
- [ ] module files do not include `ida_`/`prx_`/`poi_`.

2. Resource independence
- [ ] modules do not directly include project/feature `cfg_`/`db_`/`stm_`.

3. Completeness
- [ ] public APIs validate arguments and return structured errors.

---

## E. Datastream (`stm_`) Verification

1. Communication contract
- [ ] inter-feature runtime sharing is done through `stm_` only.

2. Purity
- [ ] `stm_` files contain no logic and no reverse dependency.

3. Plane separation
- [ ] `stm_` is used as data plane only (not as hidden capability/service API).

---

## F. Core Domain Verification

1. Core idea policy ownership
- [ ] `ida_core` is the only file including feature `ida_*.h`.

2. Core execution purity
- [ ] core execution layer (`poi_core` by default) performs registration/scheduler execution only.
- [ ] no direct HAL/BSP include in core execution.

3. Optional `prx_core` guardrail
- [ ] if `prx_core` exists, it is justified by externally-coupled interpretation; otherwise keep only `poi_core`.

---

## G. 3-Question Discriminator Audit

For each newly added/modified file touching external dependencies:

- [ ] Q1: If no external dependency required, code is in `ida_`.
- [ ] Q2: If separable judgment exists, moved to `ida_`; remainder in `poi_`.
- [ ] Q3: Only inseparable external-type-coupled judgment remains in `prx_`.

---

## H. Build and Search Verification

1. Build
- [ ] Debug build passes.
- [ ] Release build passes.

2. Dependency grep checks
- [ ] no prohibited cross-feature include (`ida_`/`prx_`/`poi_`).
- [ ] no prohibited `ida_` include of lower domain/resource headers.

Suggested commands:

```powershell
rg -n "#include .*features/.*/(ida_|prx_|poi_)" codes/
rg -n "#include .*\b(mdw_|svc_|hal_|bsp_|cfg_|db_|stm_)" codes/comsect1/project/features/*/ida_*.c
```

---

## I. Infra Capability Verification

1. Prefix discipline
- [ ] no `inf_` file-role prefix is introduced.

2. Capability direction
- [ ] `svc_`/`mdw_`/`hal_` components do not include feature `ida_`/`prx_`/`poi_`.

3. Layout invariants
- [ ] infra-integrated folders do not relax layer dependency rules.

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
