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
| `stm_feature.h` (runtime state) | `stm_Feature` shared state container in `stm_Feature.ext` |

### A2.2.2 Idea Layer in OOP

An Idea class contains **pure domain logic**: immutable, referentially transparent methods that compute, decide, and validate using only language primitives and types defined in the core contract.

Two valid forms:

**(a) Static utility class** — all methods are static/shared, no fields. Equivalent to the C pattern.

**(b) Immutable value type** — readonly fields set at construction, pure methods. No mutable state, no side effects. This is the OOP-native form: an object that IS something but does not change.

Characteristics (both forms):
- **Referentially transparent**: same inputs always produce same outputs, regardless of call order
- **No mutable state**: no mutable fields, properties, or external side effects
- No external namespace imports (no I/O, UI, networking, serialization, or framework APIs)
- May reference core contract types (the OOP equivalent of `cfg_core.h`)
- May call its own `prx_` and `poi_` classes

The Idea class is the OOP expression of ἰδέα: the uncorrupted archetype that exists independent of its material expression. Plato's Form is not the absence of being — it is *eternal, unchanging* being. An immutable value object with pure methods is a faithful expression of this concept: it IS something, it just does not change.

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

### A2.3.2 Direction Rules Restated for OOP

The allowed dependency set from Section 2.7.3, expressed in OOP terms:

```
ida_ → { own prx_, own poi_ }           (call / reference)
prx_ → { own poi_, mdw_, svc_, hal_,
          cfg_, db_, stm_ }              (import / inject)
poi_ → { mdw_, svc_, hal_,
          cfg_, db_, stm_ }              (import / inject)
Feature ↔ Feature: stm_ only            (shared state / event)
```

**Prohibited:**
- `prx_` or `poi_` importing or referencing any `ida_` class
- Any layer of Feature A importing `ida_`/`prx_`/`poi_` of Feature B
- `ida_` importing `cfg_`/`db_`/`stm_`/`mdw_`/`svc_`/`hal_`/`bsp_`
- Capability providers (`mdw_`, `svc_`) referencing feature layer classes

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

### A2.5.1 Idea Purity: Immutability, Not Statelessness

In C, `ida_` functions are inherently stateless because the language lacks object encapsulation. In OOP, the same invariant is expressed differently.

**Idea classes MUST be immutable and referentially transparent.**

- No mutable fields or properties.
- Methods produce outputs determined solely by their inputs and the object's immutable state.
- No side effects: no I/O, no modifying external state, no observable interaction with the world.
- Both static utility classes (form a) and immutable value types (form b) satisfy this rule (A2.2.2).

**What is permitted:**
- Readonly/final fields set at construction (immutable state)
- Pure methods that compute from immutable fields and parameters
- Immutable domain value objects (e.g., a chromaticity coordinate with methods)

**What is prohibited:**
- Mutable fields or properties
- Methods that modify external state or depend on call order
- Lazy initialization or caching (introduces hidden temporal coupling)

Rationale: The invariant is not the absence of being but the absence of change. Plato's ἰδέα is the eternal Form — it IS something, it just does not change. Temporal coupling (mutable state, call-order dependency) is the implementation leakage that this rule prevents. Immutability preserves purity; statelessness was merely C's mechanism for achieving it.

### A2.5.2 Shared Domain Utilities

OOP encourages reusable classes. When pure domain logic is needed by multiple features, the feature isolation rule (Section 2.7.3: `Feature ↔ Feature: stm_ only`) creates apparent friction. This is resolved by correct classification, not by relaxing the rule.

Shared pure logic is not a feature's Idea layer — it is a **shared resource** or **capability service**. The C specification already provides `svc_` for this purpose (Section 5.1 example: `prx_motor.c` includes `svc_math.h`).

Three categories for shared logic in OOP:

| Category | Prefix/Location | Accessible from | When to use |
|---|---|---|---|
| **Contract vocabulary** | `cfg_Core` (core contract scope) | All layers including Idea | Trivial domain types, constants, and simple utility functions that define the shared language |
| **Domain computation service** | `svc_` prefix class | Praxis/Poiesis only | Substantial computation reused across features |
| **Feature-internal utility** | Inside the feature's layer files | Within the feature only | Logic specific to one feature |

Decision rule:
1. Is the logic **trivial and part of the domain vocabulary** (type conversions, coordinate scaling, basic math)? → `cfg_Core`
2. Is the logic **substantial computation reused across multiple features**? → `svc_` service, accessed through Praxis/Poiesis
3. Do two "features" need to share Idea-level logic directly? → They are one feature; merge them

This classification resolves the apparent conflict: Idea may reference `cfg_Core` (core contract, allowed by Section 2.7.3), Praxis/Poiesis may reference `svc_` services (allowed by Section 2.7.3), and no feature-to-feature layer reference is needed.

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

### A2.5.5 Praxis Justification Threshold

Praxis is **optional** in every feature. The discriminator's Q3 ("inseparable domain judgment coupled to external types?") sets a high bar.

In OOP, interface-based abstraction (A2.5.4) often eliminates the need for Praxis entirely:
- Idea defines an interface expressing WHAT is needed
- Poiesis implements the interface expressing HOW it is done
- No intermediate interpretation layer is required

The `ida_` ↔ `poi_` binary, connected through an interface, is often sufficient.

Praxis is genuinely needed only when **domain judgment is inseparable from external type shapes** — when the interpretation itself requires knowledge of both the domain AND the specific protocol/format/API structure simultaneously, and this knowledge cannot be abstracted behind an interface.

Example where Praxis IS needed: LIN gateway response parsing where frame timing decisions vary by protocol command type — the timing decision is domain judgment coupled to byte-level protocol structure.

Example where Praxis is NOT needed: reading a file — the decision "which file to read" is Idea, the reading itself is Poiesis, and an interface bridges them cleanly.

### A2.5.6 Feature-Centric Co-location

The co-location principle (Section 3.1) applies in OOP:

All layer files for a feature reside together — in the same folder, package, or namespace scope. The feature is the unit of cohesion, not the layer.

```
/features/gamut/
    ida_Gamut.ext
    prx_Gamut.ext        (if discriminator requires)
    poi_Gamut.ext        (if discriminator requires)
    cfg_Gamut.ext
    db_Gamut.ext
```

### A2.5.7 Data Plane in OOP (stm_)

In C, `stm_` headers expose shared runtime state. In OOP, the data plane can be expressed through:

- Shared state container objects
- Event bus / observer pattern
- Message queue / pub-sub mechanism

The mechanism is a design choice. The invariant: **inter-feature communication uses the data plane only; direct import of another feature's layer classes is prohibited.**

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

### A2.6.4 Idea Holding Mutable State

**Violation:** Idea purity (A2.5.1).

Idea class declares mutable fields or properties. Immutable readonly fields are permitted (A2.2.2 form b); mutable state is not.

Impact: temporal coupling; test order sensitivity; referential transparency lost.

### A2.6.5 Cross-Feature Layer Import

**Violation:** feature isolation (Section 2.7.3).

Feature A's Praxis imports Feature B's Poiesis class directly.

Impact: tight coupling between features; changes in B propagate into A's adaptation layer.

Correct: use `stm_` data plane for inter-feature communication.

### A2.6.6 God-Class (Layer Collapse)

**Violation:** layer role clarity (Section 10.4).

A single class mixes UI handling, domain logic, external API calls, and state management.

Resolution: apply the 3-Question Discriminator to decompose into `ida_`/`prx_`/`poi_` classes.

---

## A2.7 File Naming Convention

The file prefix convention from the main specification is retained in OOP:

| Prefix | Role | Example |
|--------|------|---------|
| `ida_` | Idea layer | `ida_Motor.cs`, `ida_Gamut.vb` |
| `prx_` | Praxis layer | `prx_Motor.cs`, `prx_LinProtocol.vb` |
| `poi_` | Poiesis layer | `poi_Motor.cs`, `poi_SerialComm.vb` |
| `cfg_` | Configuration resource | `cfg_Motor.cs`, `cfg_Core.vb` |
| `db_`  | Static data table | `db_ColorTable.cs` |
| `stm_` | Runtime datastream | `stm_SensorData.cs` |

Class/module name matches the file name: `ida_Motor` class resides in `ida_Motor.ext`.

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
| `ida_` class with mutable instance state | Possible purity violation | Manual review recommended |

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
