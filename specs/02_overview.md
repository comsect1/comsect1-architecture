# 2. Overview

> **Terminology:** This section is the normative SSOT entry point.
> For principle background, see **Section 1.6**.

---

## 2.1 What is comsect1?

comsect1 is an **intent-driven architecture specification** that defines packaging boundaries and dependency direction.

Originally shaped by embedded firmware practice, the rules are **language-agnostic**:
examples may use C (`.c/.h`, `#include`), but the concepts map to any language's module/package system.

---

## 2.2 Design Intent

comsect1 is designed to:

- Separate **intent** (WHAT/WHEN) from implementation coupling
- Keep domain judgment close to intent and isolate mechanical production work
- Keep the architecture implementable and reviewable without mandatory tooling
- Enable **AI-assisted development (AIAD)** as an operational premise: explicit intent and machine-verifiable boundaries allow AI agents to produce conformant output within the architecture's rules (Section 1.3)

---

## 2.3 Core Concepts

### The 3-Layer Feature Model

Each feature in comsect1 consists of three **Architecture Layers**:

| Layer | Prefix | Role | Question Answered |
|-------|--------|------|-------------------|
| **Idea** | `ida_` | Domain decisions, policy, orchestration, and domain computation | "WHAT does the system do, WHEN, and under WHICH conditions?" |
| **Praxis** | `prx_` | Domain interpretation coupled to external types | "WHAT-in-HOW must be interpreted?" |
| **Poiesis** | `poi_` | Faithful mechanical production / wrapping | "HOW is it executed?" |

`cfg_`, `db_`, and `stm_` are external resources. Idea does not access them directly.

### The 3-Question Discriminator

Use this discriminator before placing code:

1. Does this code require external dependency context?
   - No: **Idea**
   - Yes: go to Q2
2. Is there separable domain judgment without external types?
   - Yes: move judgment to **Idea**, keep remainder in **Poiesis**
   - No: go to Q3
3. Is there inseparable domain judgment coupled to external types?
   - Yes: **Praxis** (translation only — see scope note below)
   - No: **Poiesis**

**Q3 scope note**: "Inseparable" means the **minimum interpretation**
that cannot be expressed without referencing the external type's internal
structure. Praxis translates external types into domain-neutral forms;
it does not decide what to do with the translated result. Post-translation
decisions (dispatch, orchestration, policy evaluation) belong in Idea,
not Praxis. See Section 4.1.3 PRX scope rule.

### The 3 Principles

1. **Idea is the contract subject**
   - Idea expresses complete intent; lower layers fulfill it.

2. **Idea self-containment** (§4.1.2)
   - Idea depends only on its own `prx_`/`poi_` and `cfg_core.h`. Full rules in §4.1.2.

3. **Praxis and Poiesis split adaptation by nature**
   - Praxis: interpretation logic inseparable from external type/protocol shape.
   - Poiesis: mechanical wrapping/bridging/forwarding without domain judgment.

---

## 2.4 Key Characteristics

- **Explicit packaging rules** implemented directly by developers
- **Clear dependency direction** enforced by include/import rules
- **Reusable modules remain pure**; adaptation is localized in `prx_`/`poi_`
- **Hardware independence (correct scope)**:
  - Independent from BSP/HAL implementation details
  - Not independent from real hardware structure and capabilities (realizable requirements)

---

## 2.5 Target Domains

- Embedded Systems / Firmware / IoT / Automotive
- Web Backend / Mobile Apps / Desktop Applications

---

## 2.6 What Follows

The sections that follow define:

| Section | Content |
|---------|---------|
| 0. (Preface) | Motivation and context (non-normative) |
| 1. Philosophy | Core intent and principle summary |
| 3. Architecture Structure | Physical structure and conceptual model |
| 4. Role of Each Layer | Idea, Praxis, Poiesis, Infra capability, bootstrap core scope |
| 5-8. Implementation Rules | Dependencies, error handling, folder structure, naming |
| 9-11. Examples and Verification | Code examples, anti-patterns, checklist |
| 12. Version History | Change log and superseded ideas |
| 13. Middleware Guideline | Middleware integration and fractal pattern |
| 14. Standard Packages | Foundation and reference implementation packages |
| Appendix A | Exception handling template |
| Appendix B | OOP adaptation (A2) |

**This specification is the contract.** Read it to understand what rules are normative.

---

## 2.7 SSOT Appendix (Terminology and Core Rules)

This appendix is the **single source of truth (SSOT)** for terminology used across this specification.
If a term is defined here, other sections should reference it rather than redefining it.

### 2.7.1 Axes: Layer / Domain / Layout / Pattern

comsect1 separates five axes. Mixing them creates ambiguity.

| Axis | Meaning | Examples |
|------|---------|----------|
| **Architecture Layer** | dependency-level separation | Idea Layer, Praxis Layer, Poiesis Layer |
| **Domain** | responsibility boundary | Project domain, Infra capability domain, Dependency repository domain |
| **Layout** | physical folder conventions | `/project`, `/infra/bootstrap`, `/infra/service`, `/infra/platform`, `/deps` |
| **Design Pattern** | repeatable implementation structure | idea-praxis-poiesis |
| **Execution Plane** | runtime interaction boundary | data plane (`stm_`) vs capability plane (`mdw_`, `svc_`, `hal_`, `bsp_`, core execution wrappers) |

### 2.7.2 Architecture layers (the 3-layer concept)

The 3-layer concept refers to architectural separation inside a unit of functionality (typically a feature):

- **Idea Layer** (`ida_`): domain decisions, policy, orchestration, and domain computation (WHAT/WHEN/WHICH)
- **Praxis Layer** (`prx_`): externally coupled interpretation that still carries domain meaning
- **Poiesis Layer** (`poi_`): mechanical production, wrapping, and bridging (HOW execution)

This is independent from folder layout and domain taxonomy.

### 2.7.3 Dependency direction (summary)

The full dependency diagram, allowed sets, and all direction rules are
defined in **Section 5** (§5.1–§5.4). Key invariants for quick reference:

- Dependency diagram and allowed sets: §5.1, §5.3
- IDA allowed set — not mandatory dual call: §5.2.1
- Idea self-containment prohibitions: §4.1.2
- Cross-feature isolation (`stm_` only): §5.2.2
- Prohibited directions (reverse, cross-feature, platform→feature): §5.4
- Data plane (`stm_`) vs capability plane (`mdw_`/`svc_`/`hal_`/`bsp_`): §5.2.4
- `/api/` entry point exception: §5.2.4

### 2.7.4 Resource prefixes (cfg_ / db_ / stm_) and core contract header

The **Core Contract header** (`cfg_core.h`) is a reserved header located in `/infra/bootstrap/`.
It defines shared contract types and interfaces used across domains (for example `Result_t`, idea interface descriptor types).
It is not a feature resource.

In the infra-integrated layout:
- Project-scoped resources live in `/project/config/`.
- Feature-scoped resources live in `/project/features/<feature>/`.
- Reusable datastream resources may be supplied by dependencies under `/deps/*`.
- `cfg_project.h` is a reserved project-scoped header for target hardware configuration (Praxis/Poiesis include only).
- Project-specific **contract vocabulary** (types used in idea interfaces, for example `Ida_Id_t`) belongs in `cfg_core.h`, not in `cfg_project.h`. See Section 3.6.1.

Resource prefixes classify **resource characteristics**, not feature taxonomy.

| Prefix | Meaning | Typical mutability | Typical scope |
|--------|---------|--------------------|---------------|
| `cfg_` | compile-time configuration | immutable | project or feature |
| `db_`  | compile-time static data tables | immutable | project or feature |
| `stm_` | runtime datastreams | mutable | cross-feature (via module) |

Access rules (summary):
- Idea: may include `cfg_core.h`; no direct access to `cfg_`/`db_`/`stm_`
- Praxis/Poiesis: may include project-scoped headers from `/project/config/`, may access own feature `cfg_`/`db_`, and `stm_` for inter-feature communication
- Capability/dependency providers (`mdw_`, `svc_`): do not depend on `cfg_`/`db_`/`stm_` directly

### 2.7.5 Idea interface object

Ideas are exposed as objects that conform to a common idea interface.
The interface is the unit of integration for Core policy and tooling (including AI-assisted development).
Core bootstrap scope (`ida_core`, `poi_core`) in `/infra/bootstrap/` includes feature idea headers and registers interface objects with the OS/scheduler.

Minimum elements:
- **Stable ID**: unique identifier for the idea
- **Entry points**: init and main flow
- **Metadata**: name/version (optional descriptive fields allowed)

Example (C, illustrative):

```c
typedef struct {
    uint32_t id;
    const char* name;
    const char* version;
    void (*init)(void);
    void (*main)(void);
} Ida_Interface_t;
```

Notes:
- In C, the interface object usually contains function pointers, but the core execution layer consumes the **object** (descriptor), not separate raw pointer registrations.
- A common exposure pattern is `const Ida_Interface_t* Ida_<feature>_GetInterface(void);`.
- `Ida_Interface_t` belongs in `cfg_core.h` because core and features share this contract surface.

### 2.7.6 BSP/HAL scope

- BSP/HAL are part of the **infra platform subdomain**.
- BSP/HAL influence is confined to **Praxis/Poiesis and below**.
- Implementation details must not leak into Idea.

### 2.7.7 Completeness and observability

Architecture completeness includes:

- **Module completeness**: responsibilities/state/error handling are contained behind a public API.
- **Observability**: transparent outputs for monitoring state.
  - Observability is one-way visibility for state monitoring, not bidirectional coupling or reverse dependencies.

### 2.7.8 Orthogonal boundary model (data plane vs capability plane)

`ida_`/`prx_`/`poi_` classify policy and execution layers.
Execution-facing boundaries are orthogonal:

- **Data plane**: `stm_` for feature-to-feature runtime state/event flow. Three communication models are supported: latest-value (Get/Set), notification (Set triggers observer callbacks), and queue (Enqueue/Dequeue with bounded buffer). See §4.2.4.5 for model definitions and selection criteria
- **Capability plane**: `mdw_`, `svc_`, `hal_`, `bsp_`, core execution wrappers for resource/control operations

Rules:
- Feature-to-feature communication uses `stm_` only.
- Feature-to-capability calls are allowed from Praxis/Poiesis (and core execution scope).
- Capability components must not include feature-layer headers (`ida_`/`prx_`/`poi_`).
- Prefixes remain role-based. Only prefixes listed in Section 8.5 are valid.

### 2.7.9 OOP language mapping

comsect1 rules are language-agnostic (Section 1.2). When applied to object-oriented languages, the following mappings hold:

- `.c/.h` compilation unit → class in a single source file
- `#include` dependency → `import`/`using`/`Imports` statement, constructor parameter, or interface reference
- Function-pointer interface struct → interface or abstract class
- File-scope `static` variables → In C, `ida_` may own domain state via file-scope `static` variables (see §9.6). In OOP, mutable instance state belongs in Praxis/Poiesis; Idea must be immutable (see A2.5.1).
  **Rationale**: This is a language accommodation, not a philosophical
  divergence. C's `static` variables are confined to the compilation unit
  — no external code can alias or observe them. The compilation unit is
  the encapsulation boundary, achieving the same isolation that OOP
  immutability guarantees through type-system enforcement. Both approaches
  prevent Idea state from leaking across boundaries; the mechanism differs
  because the language's encapsulation primitive differs

For the complete OOP adaptation guide including layer-to-class mapping, OOP-specific anti-patterns, and gate verification requirements, see **Appendix B (A2)**.

### 2.7.10 Standard Package

A **Standard Package** is a published, reusable package maintained by the
comsect1 architecture project. Standard packages serve as canonical
examples of how to apply the architecture to common embedded
responsibilities (vocabulary types, OS scheduling, flash storage).

Using a standard package is not required for comsect1 compliance.
Projects may define their own implementations for any responsibility
covered by a standard package.

Current instances: comsect1-std, comsect1-mdw-os,
comsect1-mdw-storage_manager. See Section 14.

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
