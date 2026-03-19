# EG-10: Feature Scaling and Communication Model Selection

> **Purpose**: Guide datastream communication model selection and feature
> organization for projects that grow beyond a handful of features.

---

## 1. Communication Model Selection

§4.2.4.5 defines three valid `stm_` communication models. Use this
decision guide to choose between them.

### 1.1 Decision Table

| Criterion | Latest-value | Notification | Queue |
|-----------|-------------|-------------|-------|
| Consumer needs current state only | Yes | — | — |
| Consumer must react to every change | — | Yes | — |
| Every value must be consumed in order | — | — | Yes |
| Producer frequency > consumer frequency | Safe (overwrite) | Risky (callback storm) | Requires sizing |
| Multiple producers | Requires arbitration | Requires arbitration | Requires arbitration |
| Implementation complexity | Low | Medium | Medium |

### 1.2 Default Choice

Use **latest-value** unless a specific requirement demands otherwise. It is
the simplest model, requires no callback registration, and naturally handles
producer/consumer frequency mismatch.

### 1.3 When to Use Notification

- Consumer must act on every state change (not just poll current value)
- Event-driven features that should not spin in a polling loop
- Low-frequency state changes where callback overhead is negligible

Constraint: callbacks execute in the producer's context and must be
non-blocking. If the consumer's reaction is complex, the callback should
set a flag and defer processing to the consumer's own task cycle.

### 1.4 When to Use Queue

- Command/message passing where ordering and delivery guarantee matter
- Producer and consumer run at different rates and every item must be processed
- Batch processing patterns (consumer drains queue periodically)

Constraint: queue size must be determined at compile time. Size it for the
worst-case burst that the producer can generate between consumer drain cycles.

---

## 2. Multi-Producer Arbitration

When multiple features produce to the same datastream, define an explicit
arbitration mechanism:

| Strategy | When to use |
|----------|-------------|
| **Last-writer-wins** | Latest-value model; consumer only needs most recent |
| **Priority-based** | Higher-priority producer's value takes precedence |
| **Merge function** | Values must be combined (e.g., OR of alarm flags) |

Arbitration logic belongs in the `stm_` implementation itself or in a
dedicated `svc_` that mediates writes. It must not live in any single
feature's `ida_` layer.

---

## 3. Feature Grouping for Larger Projects

Projects with 30+ features benefit from explicit grouping under
`/project/features/`:

```text
/project/features/
    /sensor/
        /temperature/       ← feature: ida_, prx_, poi_, cfg_
        /pressure/          ← feature: ida_, prx_, poi_
    /actuator/
        /motor_control/     ← feature
        /valve/             ← feature
    /diagnostic/
        /self_test/         ← feature
        /error_reporter/    ← feature
```

Rules:
- Groups are organizational folders only; they do not change prefix
  semantics, dependency rules, or access constraints.
- A group folder must not contain source files directly — only feature
  sub-folders.
- Inter-feature communication within a group still uses `stm_` only
  (§5.2.2 is not relaxed by grouping).

### 3.1 Datastream Organization with Groups

When feature count grows, datastream files benefit from domain-based naming
that matches the grouping:

```text
/project/datastreams/
    stm_temperature.h       ← sensor group data
    stm_pressure.h          ← sensor group data
    stm_motor_status.h      ← actuator group data
    stm_diagnostic_flags.h  ← diagnostic group data
```

The datastream name describes the data domain, not the producing feature
(§4.2.4.4).

---

## 4. Team Scaling Note

Feature isolation via `stm_` naturally enables parallel team ownership:
each team owns a set of features and communicates with other teams'
features exclusively through datastreams. The architecture does not
prescribe team organization — it provides the structural foundation
that makes independent ownership possible.

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
