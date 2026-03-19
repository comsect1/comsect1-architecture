# DP-04: Middleware vs Service Classification (mdw_ / svc_)

> **Purpose**: Provide a concrete decision guide for the mdw_/svc_ boundary.
> The spec defines middleware as "reusable integration/stateful logic" and
> service as "reusable computation/transform logic", but this distinction is
> a continuous spectrum. This guide makes the boundary discrete.

---

## 1. The Problem

Both `mdw_` and `svc_` are infra capability components consumed by
`prx_`/`poi_`. Both may hold internal state. The question is: when does a
stateful module cross from `svc_` into `mdw_` territory?

---

## 2. The 2-Question Discriminator

### Q1: Does the module maintain persistent state spanning multiple calls?

- **No** → `svc_`. The module is a pure computation or transform. Each call
  is independent. (Example: `svc_math`, `svc_crc`.)
- **Yes** → Go to Q2.

### Q2: Is the persistent state for integration/coordination or for computation?

- **Integration state** → `mdw_`. The state coordinates interaction between
  multiple consumers, manages a shared resource lifecycle, or tracks session
  continuity. Consumers are aware that the middleware manages this state on
  their behalf. (Examples: `mdw_scheduler` task table, `mdw_comm` session
  tracking, `mdw_storage` transaction management.)

- **Computational state** → `svc_`. The state is an implementation detail of
  the computation itself — callers neither observe nor depend on it. The
  module could theoretically be rewritten statelessly without changing its
  API contract. (Examples: `svc_filter` with internal buffer, `svc_avg`
  with running accumulator.)

- **Both equally** → `mdw_` (conservative default). If the distinction is
  genuinely ambiguous after analysis, classify as middleware. Middleware has
  stricter lifecycle expectations, so the conservative choice avoids
  under-engineering.

---

## 3. Decision Flowchart

```text
                  ┌─────────────────────────────┐
                  │ Persistent state across      │
                  │ multiple calls?              │
                  └──────────┬──────────────────┘
                       │              │
                      No             Yes
                       │              │
                       ▼              ▼
                    svc_      ┌──────────────────┐
                              │ State purpose?    │
                              └──┬───────────┬───┘
                                 │           │
                          Integration   Computation
                                 │           │
                                 ▼           ▼
                              mdw_        svc_
```

---

## 4. Worked Examples

| Module | Q1 (persistent state?) | Q2 (purpose?) | Classification |
|--------|----------------------|---------------|----------------|
| `svc_crc` — CRC computation | No | — | `svc_` |
| `svc_filter` — FIR filter with tap buffer | Yes | Computation (buffer is impl detail) | `svc_` |
| `mdw_scheduler` — task table, dispatch | Yes | Integration (consumers register tasks) | `mdw_` |
| `mdw_comm` — protocol session management | Yes | Integration (tracks session for consumers) | `mdw_` |
| `svc_avg` — running average accumulator | Yes | Computation (accumulator is impl detail) | `svc_` |
| `mdw_storage` — NVM transaction manager | Yes | Integration (manages write lifecycle) | `mdw_` |

---

## 5. Key Signals

### Signals pointing to `mdw_`

- Module provides `Init`/`DeInit` or lifecycle management
- Multiple consumers register with or subscribe to the module
- Module arbitrates between concurrent accessors
- Module's state is part of the consumer's expected contract

### Signals pointing to `svc_`

- Module could be stateless with a different algorithm
- Callers are unaware of internal state
- Each consumer could independently instantiate the logic
- Module provides a `Reset` that returns it to initial state

---

## 6. Relationship to Other Rules

- §4.2.2: middleware rules (consumed by `prx_`/`poi_`, public API only)
- §4.2.3: service rules (no upper-layer include, no feature coupling)
- §4.2.3.3: service justification checklist
- `DP_03`: Praxis justification (analogous discriminator for layers)

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
