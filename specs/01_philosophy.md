# 1. comsect1 Philosophy

> **Terminology:** This section defines core principles. For normative terminology and dependency SSOT, see **Section 2.7**.

---

## 1.1 Philosophical Foundation

### 1.1.1 The Order, Intent, and Structure

comsect1 is grounded in a philosophical model:

```
The Order -> Intent -> Structure
```

- **The Order**: The unreachable ideal state of architecture.
- **Intent**: The directional force that aligns implementation toward The Order.
- **Structure**: The vessel that carries intent through layers, boundaries, and dependency rules.

The gap between Structure and The Order is inherent. comsect1 does not claim perfection; it defines repeatable alignment rules.

Three stances toward The Order exist:
- **Ignorance**: not knowing that alignment matters — wandering without direction.
- **Delusion**: believing one has achieved perfect architecture — ending the journey prematurely.
- **Asymptotic awareness**: knowing the direction, acknowledging the unbridgeable distance, and persisting in the approach.

comsect1 operates in the third stance.

### 1.1.2 Alignment and Comprehension

Two directions exist in architecture:

- **Alignment**: toward The Order (upward)
- **Comprehension**: understanding by tracing dependency alignment upward

```
The Order
    ^
  Idea
    ^
  Praxis
    ^
 Poiesis
    ^
Middleware / HAL / BSP
```

To understand a piece of code, follow its alignment toward The Order.

---

## 1.2 Scope and Non-Goals

- comsect1 is an architecture **specification**: concepts, boundaries, and dependency rules.
- comsect1 is **not** a certification scheme, governance process, or tool mandate.
- comsect1 targets embedded firmware first, but its constraints are **language-agnostic**.
- C-style examples (`.c/.h`, `#include`) are illustrative dependency edges only.

---

## 1.3 AI-Assisted Development (AIAD)

### 1.3.1 AIAD as Design Premise

comsect1 is not merely compatible with AI-assisted development.
It is **designed to enable it**.

The architecture makes intent explicit, boundaries machine-verifiable,
and dependency rules enforceable — so that AI agents can operate
within the architecture's rules, not outside them.

This is not a claim that AI generated this specification.
comsect1 is a normative structure built on philosophical foundations (Section 1.8).
AIAD is the operational mode through which this structure is put into practice.

### 1.3.2 The AIAD Chain

```
Philosophical foundation (author's upstream work)
  -> Explicit intent in architecture (comsect1)
    -> Machine-verifiable boundaries (dependency rules, naming, layout)
      -> AI operates within verified rules (AIAD)
        -> Human owns intent and judgment; AI executes within structure
```

Each link in this chain is necessary:
- Without philosophical foundation, rules are arbitrary.
- Without explicit intent, AI cannot distinguish policy from mechanism.
- Without verifiable boundaries, conformance is unenforceable.
- Without AIAD awareness, the architecture is passive documentation.

### 1.3.3 Operative Principle

When an AI agent reads this specification, it should understand:

- The 3-layer model, dependency rules, and naming conventions are not suggestions — they are invariants.
- The 3-Question Discriminator (Section 2.3) is the mandatory decision procedure for code placement.
- Architecture verification (Section 11, Appendix scripts) is the acceptance gate for any output.
- Intent and architectural judgment remain with the human architect. AI operates within the structure, not above it.

This specification functions as both reference and operational directive.

---

## 1.4 Core Pattern: Idea-Praxis-Poiesis

The central pattern of comsect1 is the **Idea-Praxis-Poiesis** triad:

- **Idea (`ida_`)**: pure intent and domain decision (WHAT/WHEN)
- **Praxis (`prx_`)**: domain interpretation inseparable from external types/protocols
- **Poiesis (`poi_`)**: faithful mechanical production (wrapping, bridging, forwarding)

### Why These Names

The layer names are drawn from classical philosophy, deliberately unfamiliar to prevent silent mapping onto prior software conventions:

- **Idea** (Greek ἰδέα): Plato's concept of the eternal Form — the pure, uncorrupted archetype that exists independent of its material expression. In comsect1, `ida_` carries this sense: pure intent, untouched by implementation detail.
- **Praxis** (Greek πρᾶξις): Aristotle's concept of theory made manifest through action — knowledge that only exists in the doing. In comsect1, `prx_` is where abstract intent meets the concrete shapes of external systems.
- **Poiesis** (Greek ποίησις): Aristotle's concept of productive making — the craft of bringing something into being. In comsect1, `poi_` is faithful mechanical production: the act of making without domain judgment.

The naming itself encodes the relationship: Idea without Praxis is contemplation; Praxis without Poiesis is intention without production; Poiesis without Idea is activity without purpose.

Unfamiliar terms serve a deliberate function: when a developer encounters "Service" or "Controller," they map it to a prior mental model — often subtly wrong. An unfamiliar term forces the reader to learn the actual definition from the specification, preventing silent conceptual drift.

The 3-layer concept refers to **architecture layers** inside a functional unit. It is independent from folder layout or domain taxonomy.

---

## 1.5 Concepts Must Not Be Mixed

comsect1 distinguishes five axes to avoid ambiguity:

- **Architecture Layer**: Idea / Praxis / Poiesis
- **Domain**: Project / Infra Capability / Dependency Repository
- **Layout**: physical folder conventions (`/project`, `/infra/bootstrap`, `/infra/service`, `/infra/platform`, `/deps`)
- **Design Pattern**: repeatable implementation structure (idea-praxis-poiesis)
- **Execution Plane**: Data plane (`stm_`) vs Capability plane (`mdw_`, `svc_`, `hal_`, `bsp_`, core execution wrappers)

If a statement is unclear, classify it first using Section **2.7 SSOT**.

---

## 1.6 Principles (Specification-Level Summary)

### 1.6.1 Idea is the contract subject

- Idea defines domain success/failure and intent.
- Requirement changes start at Idea; lower layers adapt.

### 1.6.2 Idea self-containment

- Idea depends only on:
  - Its own Praxis/Poiesis
  - The Core Contract header (`cfg_core.h`)
- Idea must not directly access:
  - Feature resources (`cfg_`, `db_`, `stm_`)
  - Infra capabilities (`mdw_`, `svc_`)
  - Platform (`hal_`, `bsp_`)

### 1.6.3 Praxis and Poiesis are distinct gateways

- Praxis handles externally coupled interpretation with domain meaning.
- Poiesis handles mechanical execution without domain judgment.
- Both layers may access infra capabilities, resources, and platform as allowed by dependency rules.
- Neither layer may directly depend on another feature's `ida_`/`prx_`/`poi_`.

### 1.6.4 BSP/HAL influence is confined to Praxis/Poiesis and below

- BSP/HAL details must not leak into Idea.
- Hardware independence means independence from BSP/HAL implementation details, not ignorance of real hardware capabilities.

### 1.6.5 Resource categories are prefix-based characteristics

Resource prefixes classify characteristics, not taxonomy:

- `cfg_`: compile-time configuration
- `db_`: compile-time static data tables
- `stm_`: runtime datastreams

Access rules are normative in Section 2.7 and Section 5.

### 1.6.6 Architecture completeness includes observability

Architecture completeness requires:

- **Module completeness**: responsibility/state/error handling behind public API
- **Observability**: one-way visibility for state monitoring (not reverse dependency)

### 1.6.7 Low entry barrier, high comprehension

comsect1 favors explicit structures that can be implemented and reviewed without mandatory tooling.

### 1.6.8 Infra is a capability fabric (orthogonal to layers)

- Infra is not a policy layer and does not replace `ida_`/`prx_`/`poi_`.
- Policy (what/when/why) remains in Idea/Praxis.
- Infra provides execution contracts (concurrency, timeout, error mapping, resource ownership).
- `stm_` is the feature-to-feature **data plane**.
- `mdw_`/`svc_`/`hal_`/`bsp_` (and core execution wrappers) form the **capability plane**.
- Prefixes remain role-based (`ida_`, `prx_`, `poi_`, `svc_`, `hal_`, ...); do not introduce `inf_` as a role prefix.

### 1.6.9 Clarity of purpose enables adaptation

A structure's ability to adapt to change is proportional to the clarity of its Core Intent.

When requirements change, a well-aligned architecture reveals where the change belongs: intent changes propagate from Idea downward; implementation changes stay contained in Praxis/Poiesis.

Architecture does not resist change or blindly embrace it. It adapts through alignment: maintaining direction while forging new paths.

---

## 1.7 Idea Interface Object (Contract Surface)

Ideas are exposed as objects conforming to a common interface (stable ID, init/main flow, metadata).

- Core policy is owned by `ida_core`.
- Core execution integration is done by the core execution layer (`poi_core` by default).
- The interface object is the unit of integration.

Shared interface types belong in `cfg_core.h`.

---

## 1.8 Upstream Philosophical Alignment

comsect1 is an application-layered specification derived from the author's upstream philosophical work on the nature of structure.

Alignment points:

- **The Order / Intent / Structure**:
  - comsect1 preserves the same triad and treats Structure as the vessel of Intent.
- **Boundary as membrane**:
  - dependency rules are selective permeability constraints, not isolation for its own sake.
- **Flow vs dependency inversion**:
  - business meaning flows downward through execution while dependency direction remains upward toward intent purity.
- **Great Alignment**:
  - architecture quality is judged by continuity of alignment, not by static completion.

Mapping note:
- The upstream work phrases practical propagation as `Idea -> Praxis -> implementation`.
- comsect1 refines `implementation` into explicit **Poiesis** (Greek ποίησις, "productive making") to separate:
  - externally-coupled interpretation (`prx_`, Praxis)
  - mechanical production (`poi_`, Poiesis)

This is a refinement for role clarity, not a philosophical divergence. The naming draws from the same Aristotelian tradition: Praxis is action with inherent meaning; Poiesis is production directed toward an external end.

AIAD connection:
- The upstream philosophy makes intent the governing force of structure.
- comsect1 translates this into explicit, machine-readable rules.
- This explicitness is what enables AI agents to operate within the architecture — the philosophical foundation is not incidental to AIAD; it is its precondition.

---

## 1.9 Reading Guide (Minimal)

- Start with Section 2 (Overview) and **2.7 SSOT**.
- Then read Section 4 (Role of Each Layer) and Section 5 (Dependency Rules).
- Use Sections 7-8 for layout and naming rules.
- Use Sections 9-11 for examples and verification.
- Use Section 13 for middleware integration rules.

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.0**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

You are free to:
- **Share** - copy and redistribute the material in any medium or format for non-commercial purposes only.

Under the following terms:
- **Attribution** - you must give appropriate credit to the author (Kim Hyeongjeong), provide a reference to the license, and indicate if changes were made.
- **NonCommercial** - you may not use the material for commercial purposes.
- **NoDerivatives** - if you remix, transform, or build upon the material, you may not distribute the modified material.

No additional restrictions - you may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
