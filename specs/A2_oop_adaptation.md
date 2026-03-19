# Appendix B. OOP Language Adaptation

> **Terminology:** This appendix extends the normative rules of **Section 2.7 SSOT** to object-oriented languages.
> It does not redefine core principles; it re-expresses them through OOP-native constructs.

---

## A2.0 Scope

comsect1 constraints are **language-agnostic** (Section 1.2, Section 2.1).
The main specification illustrates dependency edges with C (`.c/.h`, `#include`).
This appendix maps those edges to OOP constructs: classes, interfaces, namespaces, access modifiers, and dependency injection.

**What this appendix is:**
- The normative companion for applying comsect1 to any OOP language.
- A mapping from C-illustrated conventions to their OOP equivalents.
- A definition of OOP-specific invariants and anti-patterns.

**What this appendix is not:**
- A binding to a specific OOP language or framework.
- A replacement for the main specification. Invariants defined in Sections 1–5 are not restated here unless their OOP expression requires clarification.

---

## A2.1 Invariants Across Languages

The following are **language-invariant**. They hold in C, OOP, functional, and any future language:

1. The Order → Intent → Structure triad (Section 1.1)
2. The 3-Layer Feature Model: Idea / Praxis / Poiesis (Section 2.3)
3. The 3-Question Discriminator (Section 2.3)
4. Dependency direction rules (Section 2.7.3)
5. Idea self-containment (Section 1.6.2)
6. Feature isolation via data plane (`stm_`) (Section 2.7.8)
7. Data plane / capability plane orthogonality (Section 2.7.8)
8. Resource prefix semantics: `cfg_` / `db_` / `stm_` (Section 2.7.4)
9. Core contract scope: `ida_core` (policy) + execution layer (Section 1.7)
10. AIAD gate as acceptance criterion (Section 1.3.3)
11. `svc_` placement: `/infra/service/` only (Section 7.5)
12. Only prefixes listed in Section 8.5 are valid: folder grouping does not change prefix semantics (Section 5.2.4)

These invariants are **not relaxed** by adopting an OOP language.

---

## A2.2 Layer-to-OOP Construct Mapping

### A2.2.1 Compilation Unit

In C, a `.c/.h` pair is the basic unit of encapsulation. In OOP, a **class** (or module) in a single source file serves the same role.

| C Convention | OOP Equivalent |
|---|---|
| `ida_feature.c` / `ida_feature.h` | `ida_Feature` class in `ida_Feature.ext` |
| `prx_feature.c` / `prx_feature.h` | `prx_Feature` class in `prx_Feature.ext` |
| `poi_feature.c` / `poi_feature.h` | `poi_Feature` class in `poi_Feature.ext` |
| `cfg_feature.h` (constants) | `cfg_Feature` static/const class in `cfg_Feature.ext` |
| `db_feature.h` (data tables) | `db_Feature` static/const class in `db_Feature.ext` |
| `stm_feature.h` (runtime state) | `stm_Feature` shared state container in `stm_Feature.ext`|

### A2.2.2 Idea Layer in OOP

An Idea class contains **business decisions, policy, and flow** (Section 4.1.2). It uses only language primitives and types defined in the core contract (`cfg_core.h` equivalent).

Two valid forms:

**(a) Static utility class** — all methods are static/shared, no instance fields. Direct equivalent of C's `ida_*.c` functions.

**(b) Value type** — readonly fields set at construction. OOP-native form where an object carries context needed for decisions. This form has no C equivalent; it is an OOP accommodation.

Allowed (both forms, per Section 4.1.2):
- Business decisions, policy, flow
- Reference to core contract types (`cfg_core.h` equivalent)
- Call to own `prx_` and `poi_` classes

Prohibited (both forms):
- External namespace imports (I/O, UI, networking, serialization, framework APIs) — self-containment, Section 1.6.2
- Feature resources (`cfg_<feature>`, `db_`, `stm_`) — self-containment, Section 4.1.2
- Infra capability (`mdw_`, `svc_`, `hal_`, `bsp_`) — self-containment, Section 4.1.2
- Other feature files — self-containment, Section 5.2.2
- Mutable instance state — purity, Section 2.7.9 "Idea remains stateless"

### A2.2.3 Praxis Layer in OOP

A Praxis class contains **domain interpretation inseparable from external types**. It may hold state that bridges domain decisions to external system shapes.

Characteristics:
- May import external namespaces required for type-coupled interpretation
- Receives external dependencies via constructor or method parameters
- Contains domain judgment (not just forwarding)
- Must not call or reference its own `ida_` class (reverse dependency prohibition)

### A2.2.4 Poiesis Layer in OOP

A Poiesis class performs **mechanical production**: wrapping, bridging, and forwarding external APIs without domain judgment.

Characteristics:
- May import any external namespace needed for wrapping
- Contains no domain interpretation or business branching
- Must not call or reference its own `ida_` or `prx_` classes
- Typically manages lifecycle of external resources (connections, handles, streams)

### A2.2.5 Idea Interface Object in OOP

In C, the Idea Interface Object is a struct with function pointers (Section 2.7.5). In OOP, it becomes an **interface** or **abstract class**:

Minimum elements (unchanged from Section 1.7):
- Stable ID
- Init entry point
- Main flow entry point
- Metadata (optional)

The interface definition resides in the core contract scope (the OOP equivalent of `cfg_core.h`), not inside any layer file.

---

## A2.3 Dependency Direction in OOP

### A2.3.1 Import/Using as Trust Statement

Section 5.0 states: *"Every include/import is a trust statement."*

In OOP, this applies to all forms of dependency expression:
- `import` / `using` / `Imports` statements
- Constructor parameter types
- Method parameter types
- Generic type constraints
- Interface implementations

Each is a dependency edge. Dependency direction rules (Section 2.7.3) govern all of them.

### A2.3.2 Direction Rules in OOP

The allowed dependency sets and prohibited directions from **§5.1–§5.4**
apply without modification. In OOP, each dependency edge manifests as
`import`/`using`/`Imports`, constructor parameter, method parameter,
generic constraint, or interface implementation.

OOP-specific interpretation of each edge type:
- `ida_ → prx_/poi_`: call or reference (composition, not inheritance)
- `prx_/poi_ → capability/resource`: import or inject
- Feature ↔ Feature: `stm_` shared state containers only (§5.2.2)

### A2.3.3 Dependency Injection and Direction

OOP commonly uses dependency injection (DI). DI does not exempt code from direction rules.

Correct pattern: Idea creates or receives Praxis/Poiesis → calls downward.
Incorrect pattern: Praxis receives Idea via injection → reverse dependency.

If a DI container is used, registration must respect direction: Idea is resolved; it is never injected into Praxis/Poiesis as a dependency.

### A2.3.4 Access Modifiers as Enforcement

OOP access modifiers (`internal`, `package-private`, `protected`, `private`) provide compile-time enforcement that C lacks:

- Feature layer classes should use the most restrictive visibility that still allows correct composition.
- Cross-feature types intended for the data plane (`stm_`) should be the only types with public/exported visibility across feature boundaries.
- Access modifier choices are language-specific; this appendix does not prescribe a specific modifier. The invariant is: **restrict cross-boundary access to the minimum required by dependency rules**.

---

## A2.4 The Discriminator in OOP Context

The 3-Question Discriminator (Section 2.3) applies identically in OOP. What changes is the definition of "external dependency."

### A2.4.1 What Counts as External Dependency in OOP

In C, external dependency is measured by `#include` of non-language headers. In OOP:

**External** = any import/using of a namespace, package, or module that is not:
- The language's primitive/built-in types
- The project's core contract types (equivalent of `cfg_core.h`)

**Not external** = language primitives (`int`, `string`, `bool`, `List`, `Dictionary`, `Math`, etc.)

### A2.4.2 Discriminator Application

No change from Section 2.3. Restatement with OOP vocabulary:

1. Does this code require importing external namespaces?
   - No → **Idea**
   - Yes → Q2

2. Can domain judgment be separated from external types?
   - Yes → judgment to **Idea**, mechanical remainder to **Poiesis**
   - No → Q3

3. Does inseparable domain judgment exist, coupled to external types?
   - Yes → **Praxis**
   - No → **Poiesis**

---

## A2.5 OOP-Specific Considerations

### A2.5.1 Idea Constraints: Self-Containment and Purity

Two orthogonal constraints govern Idea. Both originate from the base specification and are **not relaxed** by adopting an OOP language.

**1. Self-containment (dependency dimension, Section 1.6.2, Section 4.1.2):**

What Idea may depend on:

- Own `prx_`/`poi_` classes
- Core contract types (`cfg_core` equivalent)

What Idea must not depend on:

- External namespace imports (I/O, UI, networking, serialization, framework APIs)
- Feature resources (`cfg_<feature>`, `db_`, `stm_`)
- Infra capability (`mdw_`, `svc_`, `hal_`, `bsp_`)
- Other feature files

**2. Purity (behavioral dimension, Section 2.7.9 "Idea remains stateless"):**

In C, `ida_` is stateless: no file-scope `static` variables. Functions operate on parameters only. The OOP equivalent is **immutability and referential transparency**:

- No mutable instance fields — state, once constructed, does not change
- Same inputs produce same outputs — no hidden side effects

Two valid forms:

**(a) Static utility class** — all methods are static/shared, no instance fields. Direct equivalent of C's `ida_*.c` functions. **Preferred default.**

**(b) Value type** — readonly fields set at construction. OOP accommodation where an object carries context needed for decisions. The readonly fields are analogous to curried parameters: frozen at construction time, immutable thereafter.

Both forms satisfy purity: no mutable state means no hidden side effects; referential transparency means same inputs always produce same outputs.

**Why both constraints are necessary:**

Satisfying only self-containment (no external imports) while allowing mutable state would make Idea state-dependent — its behavior changes over time based on internal mutation. This violates "Idea remains stateless" (Section 2.7.9) and "pure, uncorrupted archetype that exists independent of its material expression" (Section 1.4).

**Recommendation**: Prefer stateless static methods (form a) as the default. Use form (b) only when decision context must be carried across method calls within the same Idea class.

**C accommodation**: In C, `ida_` may own domain state via file-scope `static` variables (§2.7.9, §9.6). This is not a relaxation of purity — C's compilation-unit encapsulation prevents external aliasing, achieving the same boundary isolation that OOP immutability enforces through the type system.

### A2.5.2 Shared Domain Utilities

OOP encourages reusable classes. When pure domain logic is needed by multiple features, the feature isolation rule (§5.2.2) creates apparent friction. This is resolved by correct classification, not by relaxing the rule.

Shared pure logic is not a feature's Idea layer — it is a **shared resource** or **capability service**. The C specification already provides `svc_` for this purpose (Section 5.1 example: `prx_sensor.c` includes `svc_math.h`).

Three categories for shared logic in OOP:

| Category | Prefix/Location | Accessible from | When to use |
|---|---|---|---|
| **Contract vocabulary** | `cfg_Core` (core contract scope) | All layers including Idea | Domain types, constants that define the shared language (Section 5.2.3) |
| **Domain computation service** | `svc_` prefix class | Praxis/Poiesis only | Substantial computation reused across features |
| **Feature-internal utility** | Inside the feature's layer files | Within the feature only | Logic specific to one feature |

Decision rule:
1. Is the logic **part of the domain vocabulary** (types, constants, enums)? → `cfg_Core`
2. Is the logic **substantial computation reused across multiple features**? → `svc_` service, accessed through Praxis/Poiesis
3. Do two "features" need to share Idea-level logic directly? → They are one feature; merge them

This classification resolves the apparent conflict: Idea may reference `cfg_Core` (core contract, allowed by Section 2.7.3), Praxis/Poiesis may reference `svc_` services (allowed by Section 2.7.3), and no feature-to-feature layer reference is needed.

Service documentation and lifecycle rules from Section 4.2.3 apply equally to OOP `svc_` classes: each must document its purpose and consumers, and must be reviewed for consolidation when consuming features change.

### A2.5.3 Inheritance Across Layers

OOP inheritance creates an implicit dependency: a derived class depends on its base class.

**Layer classes MUST NOT form inheritance hierarchies across layers.**

- `prx_Feature` inheriting from `ida_Feature` is forbidden (creates reverse dependency from lower to higher layer).
- `poi_Feature` inheriting from `prx_Feature` is forbidden (creates hidden coupling across distinct roles).

Use **composition**: Idea calls Praxis/Poiesis; it does not extend them. Praxis delegates to Poiesis; it does not derive from it.

### A2.5.4 Interface-Owned Layer Boundaries

OOP interfaces provide compile-time enforcement of dependency direction — stronger than C's convention-based approach and stronger than gate-script verification alone.

**Interface ownership rule**: The interface is owned by the upper layer or the feature root. The implementation lives in the lower layer.

```
Feature scope:
  IFeatureTransport (interface)   ← owned by feature, defines WHAT
  ida_Feature                     ← uses IFeatureTransport (calls down)
  poi_Feature                     ← implements IFeatureTransport (provides HOW)
```

This aligns OOP's Dependency Inversion Principle with comsect1's direction rules:
- The interface defines the contract (owned by the intent side)
- The implementation fulfills it (owned by the mechanical side)
- The compiler enforces direction: Poiesis knows only the interface, not Idea

Benefits:
- **Compiler-enforced direction**: no reverse dependency can compile
- **Testability**: inject a mock Poiesis implementation for unit testing Idea
- **Explicit contract surface**: the interface IS the boundary between intent and execution

The Idea Interface Object (Section 1.7, A2.2.5) — the feature's public contract (`Init`, `Main`) — resides in the **core contract scope** (`cfg_Core`), not inside any layer file. Feature-internal interfaces between layers reside at the **feature root** level.

### A2.5.5 Core Scope in OOP

Section 4.0 defines the bootstrap core scope. In OOP, the same structure applies:

| Core layer | Prefix | Location | Primary role |
|---|---|---|---|
| Core Idea | `ida_core` | `/infra/bootstrap/` | Feature registration policy and orchestration intent |
| Core Poiesis | `poi_core` | `/infra/bootstrap/` | Host/scheduler wrapping and task registration execution |
| Core Praxis (optional) | `prx_core` | `/infra/bootstrap/` | Externally-coupled interpretation in core context |
| Core Contract | `cfg_core` | `/infra/bootstrap/` | Contract vocabulary accessible by ALL layers |

OOP-specific mapping:
- `ida_core` collects feature interface objects (OOP equivalent of `#include "ida_<feature>.h"` for registration)
- `poi_core` wraps the host execution model (event loop, task scheduler, application framework entry point)
- `cfg_core` defines shared contract types (enums, value types, constants)

Dependency rules from Section 4.0 apply without modification:
- `ida_core` → feature `ida_*` interfaces, `poi_core`, `cfg_core`
- `ida_core` must NOT reference `mdw_`, `svc_`, `hal_`, `bsp_`, or feature `prx_`/`poi_`
- `poi_core` → `mdw_` (scheduler/host middleware), `cfg_core`
- `poi_core` must NOT reference feature `ida_*` or HAL/BSP directly

Execution models (Section 4.0.8) map to OOP hosts:

| Model | `poi_core` OOP behavior |
|---|---|
| Console / service | Sequentially dispatch each feature main entry |
| WinForms / WPF | Register features with application event loop |
| ASP.NET / web | Register features as middleware/services |

### A2.5.6 Praxis Justification Threshold

Praxis is **optional** in every feature. The discriminator's Q3 ("inseparable domain judgment coupled to external types?") sets a high bar.

In OOP, interface-based abstraction (A2.5.4) often eliminates the need for Praxis entirely:
- Idea defines an interface expressing WHAT is needed
- Poiesis implements the interface expressing HOW it is done
- No intermediate interpretation layer is required

The `ida_` ↔ `poi_` binary, connected through an interface, is often sufficient.

Praxis is genuinely needed only when **domain judgment is inseparable from external type shapes** — when the interpretation itself requires knowledge of both the domain AND the specific protocol/format/API structure simultaneously, and this knowledge cannot be abstracted behind an interface.

Example where Praxis IS needed: communication protocol response parsing where frame timing decisions vary by protocol command type — the timing decision is domain judgment coupled to byte-level protocol structure.

Example where Praxis is NOT needed: reading a file — the decision "which file to read" is Idea, the reading itself is Poiesis, and an interface bridges them cleanly.

### A2.5.7 Feature-Centric Co-location

The co-location principle (Section 3.1) applies in OOP:

All layer files for a feature reside together — in the same folder, package, or namespace scope. The feature is the unit of cohesion, not the layer.

```
/features/logger/
    ida_Logger.ext
    prx_Logger.ext        (if discriminator requires)
    poi_Logger.ext        (if discriminator requires)
    cfg_Logger.ext        (feature-local config)
```

Resource placement follows Section 7.6:
- Feature-local `cfg_`: in feature folder
- Project-wide `cfg_` and `db_`: in `/project/config/`
- Core contract `cfg_core`: in `/infra/bootstrap/`
- Datastream `stm_`: in `/project/datastreams/`

### A2.5.8 Data Plane in OOP (stm_)

In C, `stm_` headers expose shared runtime state. In OOP, `stm_` maps to **shared state container objects** — the direct equivalent of C's `stm_` headers.

The invariant from Section 5.2.2: **inter-feature communication uses the data plane (`stm_`) only; direct import of another feature's layer classes is prohibited.**

`stm_` placement follows Section 7.6:
- Project-specific inter-feature state: `/project/datastreams/`
- Reusable datastream definitions: `/deps/middleware/` or dependency-provided

---

## A2.6 OOP Anti-Patterns

These extend Section 10 with OOP-specific violations.

### A2.6.1 Idea Importing External Namespace

**Violation:** Idea self-containment (Section 1.6.2).

Idea class imports UI, I/O, networking, serialization, or framework-specific namespace.

Impact: Idea becomes coupled to implementation detail; portability and testability degrade.

### A2.6.2 Reverse Dependency via Inheritance

**Violation:** dependency direction (Section 2.7.3).

Praxis or Poiesis class inherits from Idea class.

Impact: circular coupling; Idea changes propagate downward through inheritance chain, but Praxis/Poiesis changes can break Idea's contract surface.

### A2.6.3 Reverse Dependency via Injection

**Violation:** dependency direction (Section 2.7.3).

Praxis or Poiesis receives Idea as a constructor parameter or interface.

Impact: lower layer calls upward; dependency inversion misused to circumvent direction rules.

### A2.6.4 Idea Accessing Feature Resources

**Violation:** Idea self-containment (Section 1.6.2, Section 4.1.2).

Idea class accesses `cfg_<feature>`, `db_`, `stm_`, or any feature resource directly.

Impact: Idea becomes coupled to feature implementation detail; the decision/policy layer acquires hidden dependencies on data format and runtime state.

### A2.6.5 Idea Holding Mutable State

**Violation:** Idea purity (Section 2.7.9 "Idea remains stateless").

Idea class declares mutable instance fields, public setters, or void methods with side effects on internal state.

Impact: Idea behavior becomes state-dependent; the same method call can produce different results depending on prior mutations. This violates "pure, uncorrupted archetype" (Section 1.4) and breaks referential transparency.

### A2.6.6 Cross-Feature Layer Import

**Violation:** feature isolation (Section 2.7.3).

Feature A's Praxis imports Feature B's Poiesis class directly.

Impact: tight coupling between features; changes in B propagate into A's adaptation layer.

Correct: use `stm_` data plane for inter-feature communication.

### A2.6.7 God-Class (Layer Collapse)

**Violation:** layer role clarity (Section 10.4).

A single class mixes UI handling, domain logic, external API calls, and state management.

Resolution: apply the 3-Question Discriminator to decompose into `ida_`/`prx_`/`poi_` classes.

---

## A2.7 File Naming Convention

The file prefix convention from the main specification is retained in OOP:

| Prefix | Role | Example |
|--------|------|---------|
| `ida_` | Idea layer | `ida_Sensor.cs`, `ida_Logger.vb` |
| `prx_` | Praxis layer | `prx_Sensor.cs`, `prx_CommProtocol.vb` |
| `poi_` | Poiesis layer | `poi_Sensor.cs`, `poi_SerialComm.vb` |
| `cfg_` | Configuration resource | `cfg_Sensor.cs`, `cfg_Core.vb` |
| `db_`  | Static data table | `db_ColorTable.cs` |
| `stm_` | Runtime datastream | `stm_SensorData.cs` |

Class/module name matches the file name: `ida_Sensor` class resides in `ida_Sensor.ext`.

Rationale:
- Prefix enables filename-based gate verification (consistent with C convention).
- Immediately visible in file explorers and IDE project trees.
- No namespace hierarchy required for layer identification — the prefix is sufficient.

---

## A2.8 Gate Verification for OOP

The AIAD gate (Section 1.3, Section 11) must verify OOP-specific rules:

### A2.8.1 Minimum Gate Checks

| Check | Rule | Detection Method |
|-------|------|------------------|
| `ida_` forbidden imports | Idea self-containment | Scan `import`/`using`/`Imports` for external namespaces |
| `ida_` forbidden API calls | Idea self-containment | Scan for UI/IO/threading API patterns |
| `prx_` → `ida_` reference | Dependency direction | Scan for `ida_` class names in `prx_` files |
| `poi_` → `ida_`/`prx_` reference | Dependency direction | Scan for `ida_`/`prx_` class names in `poi_` files |
| Cross-feature layer import | Feature isolation | Scan for layer class names from other features; `svc_`/`cfg_`/`db_`/`stm_` prefix files are shared resources, not features |

### A2.8.2 Warning-Level Heuristics

| Heuristic | Concern | Action |
|-----------|---------|--------|
| `poi_` file with complex domain conditionals | Possible PRX/POI role collapse | Manual review recommended |
| `ida_` class with feature resource access | Possible self-containment violation (Section 1.6.2) | Manual review recommended |
| `ida_` class with mutable instance fields | Possible purity violation (Section 2.7.9) | Manual review recommended |

---

## A2.9 Error Handling in OOP

Section 6 defines error handling for C. This section maps those rules to OOP.

### A2.9.1 Exception vs Result Pattern

OOP languages provide exceptions. comsect1 does not mandate one pattern over
the other, but the layer boundary rules apply:

| Pattern | When to use |
|---------|-------------|
| `Result_t` return | Cross-layer boundaries, API contracts, infrastructure wrappers |
| Exceptions | Language-idiomatic internal flow within a single layer |

Rule: Layer boundary methods (the methods that `ida_` calls on `prx_`/`poi_`)
should return explicit status. Internal helper methods within a layer may use
exceptions if the language convention favors them.

### A2.9.2 Exception Ownership by Layer

| Layer | Exception responsibility |
|-------|------------------------|
| `poi_` | Catch infrastructure exceptions, translate to `Result_t` or domain exception |
| `prx_` | Catch external-type exceptions during translation, translate to domain form |
| `ida_` | Decide recovery strategy: retry, fallback, safe-state, or fatal |

Rule: Lower layers report; Idea decides. This is unchanged from S6.3.

### A2.9.3 Try/Catch at Layer Boundaries

`poi_` and `prx_` must not let infrastructure exceptions propagate to `ida_`
uncaught. Idea should never need to catch `IOException`, `SerialPortException`,
or framework-specific exceptions.

Correct:
- `poi_` catches `IOException` -> returns `RESULT_FAIL`
- `ida_` checks `RESULT_FAIL` -> decides retry or fallback

Wrong:
- `ida_` catches `IOException` -> Idea is now coupled to I/O infrastructure

### A2.9.4 Fatal Handler in OOP

The fatal handler pattern (S6.4, Appendix A) maps to OOP as an application-level
unhandled exception handler or a static fatal method in the core contract scope.

The handler must:
- log context (source, message, stack trace)
- transition to a safe state
- not attempt recovery

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
