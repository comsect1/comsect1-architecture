# comsect1 30-Minute Onboarding (Junior Engineer)

This guide is a time-boxed reading path to reach safe-to-contribute understanding of comsect1.

---

## Goal (After 30 Minutes)

- Read `ida_*.c` and explain WHAT/WHEN.
- Read `prx_*.c` and explain externally-coupled interpretation.
- Read `poi_*.c` and explain mechanical execution.
- Spot common boundary violations quickly.
- Place new code in the correct layer on first attempt.

---

## 30-Minute Reading Path

| Time | Document | Focus |
|------|----------|-------|
| 0-5 min | `specs/02_overview.md` | SSOT terms and 3-layer model |
| 5-15 min | `specs/04_layer_roles.md` | Role constraints for Idea/Praxis/Poiesis |
| 15-22 min | `specs/05_dependency_rules.md` | Allowed and prohibited dependency directions |
| 22-27 min | `specs/10_anti_patterns.md` | Typical violations and why they are harmful |
| 27-30 min | `specs/11_checklist.md` | Post-task verification |

---

## Comprehension Questions

### `specs/02_overview.md`

1. What does "Idea is the contract subject" mean in practice?
2. What is the 3-layer feature model, and what does each layer answer?
3. How does the 3-question discriminator separate PRX from POI?

### `specs/04_layer_roles.md`

1. What may `ida_` include, and what is prohibited?
2. When is code `prx_` instead of `poi_`?
3. Why is core execution placed in `poi_core` by default?

### `specs/05_dependency_rules.md`

1. List three prohibited dependencies and what each prohibition protects.
2. Why can every layer include `/infra/bootstrap/cfg_core.h`?
3. How should features communicate with each other?
4. What is the difference between data plane (`stm_`) and capability plane (`mdw_`/`svc_`/`hal_`)?

---

## 5-Minute Micro Exercise

Classify each item: `ida_` / `prx_` / `poi_` / `svc_` / `mdw_` / `hal_` / `bsp_` / `cfg_` / `db_` / `stm_`.

1. Stop motor when overheat condition is detected.
2. Parse protocol byte fields to decide operation mode.
3. Wrap OS task creation API without any decision logic.
4. Convert raw ADC value to Celsius.
5. Share latest temperature across features without direct include.

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
