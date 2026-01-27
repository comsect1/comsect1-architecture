# comsect1 Testing Strategy: Fractal Approach

## 1. Core Insight

comsect1 testing is fractal: the same role-based strategy repeats at every scale.

Architecture roles are now:
- Idea (`ida_`): intent logic
- Praxis (`prx_`): externally-coupled interpretation
- Poiesis (`poi_`): mechanical execution

---

## 2. Universal Testing Pattern

### 2.1 Testing Idea (Logic Unit Test)

- Target: `ida_*.c`
- Environment: host PC
- Method:
  1. compile Idea
  2. mock own `prx_`/`poi_` interfaces
  3. verify business decisions and state transitions

### 2.2 Testing Praxis (Interpretation Integration Test)

- Target: `prx_*.c`
- Environment: target hardware or high-fidelity simulator
- Method:
  1. feed external-type/protocol shaped inputs
  2. verify interpretation result and downstream calls (`poi_`, `mdw_`, `svc_`)

### 2.3 Testing Poiesis (Execution Integration Test)

- Target: `poi_*.c`
- Environment: target hardware or simulator
- Method:
  1. call POI interfaces directly
  2. verify HAL/OS/module side effects
  3. verify wrappers/bridges are deterministic and decision-free

---

## 3. Applying the Strategy

### 3.1 Feature Level

- Idea test: mock `prx_`/`poi_` and verify decision outputs.
- Praxis test: validate protocol/type interpretation and mapping.
- Poiesis test: validate hardware/API forwarding behavior.

### 3.2 Middleware/Internal Modules

For complex middleware, apply the same split internally (logic vs interpretation vs execution) where beneficial.

### 3.3 HAL/BSP

Keep logic-like behavior testable separately from direct pin/register manipulation.

---

## 4. Summary

| Component | Role | Environment | Dependency Style |
|-----------|------|-------------|------------------|
| Idea | business logic | host PC | mocked PRX/POI |
| Praxis | external interpretation | target/sim | real or simulated module inputs |
| Poiesis | execution bridge | target/sim | real HAL/OS/modules |

If it is intent logic, test it as Idea. If it is type-coupled interpretation, test it as Praxis. If it is mechanical forwarding, test it as Poiesis.

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
