# Project Guidelines for Claude

## Language Policy

- **Conversation**: Korean (match user's language)
- **All artifacts**: English only
  - Documentation (`.md`, `.txt`)
  - Code and comments
  - Commit messages
  - File names

## Writing Style

### Philosophical Content

1. Preserve conceptual precision and impactful expressions.
2. Keep links between intent, meaning, and direction explicit.
3. Avoid shallow summaries when architectural rationale is requested.

### Technical Content

- Concise and precise
- Examples over abstraction
- Practical enforceability matters

## comsect1 Core Values

- **Intent-driven architecture**: Idea's intent defines the contract.
- **Architecture as vessel**: structure carries intent through change.
- **The Order**: unreachable ideal state; architecture is continuous alignment.
- **Comprehension over compliance**: rules exist to preserve meaning, not ritual.

## File Structure (Specification)

```text
specs/
  00_why_architecture.md
  01_philosophy.md
  02_overview.md
  03_architecture_structure.md
  04_layer_roles.md
  05_dependency_rules.md
  06_error_handling.md
  07_folder_structure.md
  08_naming_conventions.md
  09_code_examples.md
  10_anti_patterns.md
  11_checklist.md
  12_version_history.md
  13_middleware_guideline.md
  A1_exception_handling.md
```

---

## CRITICAL: comsect1 Architecture Conventions

Never deviate from these rules without explicit user confirmation.

### 3-Layer Feature Model

| Layer | Prefix | Responsibility |
|-------|--------|----------------|
| **Idea** | `ida_` | WHAT/WHEN intent and business decisions |
| **Praxis** | `prx_` | Externally-coupled domain interpretation |
| **Poiesis** | `poi_` | Mechanical production (wrapping/bridging/forwarding) |

Core defaults:
- `ida_core` (policy)
- `poi_core` (execution)
- `prx_core` is optional and justified only when core has unavoidable external-type interpretation.

### Feature-Centric Layout

```text
/comsect1
  /project
    /config
      cfg_project.h
    /datastreams
      stm_*.h
    /features
      /<feature>
        ida_<feature>.c/h
        prx_<feature>.c/h   (optional by discriminator)
        poi_<feature>.c/h   (optional by discriminator)
        cfg_<feature>.h
        db_<feature>.h
  /infra
    /bootstrap
      ida_core.c/h
      poi_core.c/h
      cfg_core.h
      prx_core.c/h   (optional by discriminator)
    /service
    /platform
      /hal
      /bsp
  /deps
    /extern
    /middleware
```

Layout rules:
- `infra` is the default shared capability fabric layout.
- Keep role prefixes unchanged (`ida_`/`prx_`/`poi_`/`mdw_`/`svc_`/`hal_`/`bsp_`/`stm_`/`cfg_`/`db_`).
- Do not introduce `inf_` as a file-role prefix.


### Dependency Rules (Invariant)

```text
IDA -> { own PRX, own POI }
PRX -> { own POI, mdw_, svc_, hal_, cfg_, db_, stm_ }
POI -> { mdw_, svc_, hal_, cfg_, db_, stm_ }
Feature <-> Feature: stm_ only
Platform: HAL -> BSP
```

Interpretation:
- `IDA -> { own PRX, own POI }` is a fixed allowed dependency set.
- IDA may call PRX only, POI only, or both.

Orthogonal runtime planes:
- Data plane: `stm_`
- Capability plane: `mdw_`/`svc_`/`hal_`/`bsp_` (+ core execution wrappers)

### Access Rules

| Resource | Idea | Praxis/Poiesis |
|----------|------|----------------|
| `/infra/bootstrap/cfg_core.h` | Yes | Yes |
| `/project/config/*` | No | Yes |
| feature `cfg_`/`db_` | No | Yes |
| `stm_` datastream | No | Yes |

---

## 3-Question Discriminator (Mandatory)

For any code touching external dependencies:

1. External dependency required?
- No -> `ida_`
- Yes -> Q2

2. Separable domain judgment without external types?
- Yes -> move judgment to `ida_`, leave remainder in `poi_`
- No -> Q3

3. Inseparable domain judgment coupled to external types?
- Yes -> `prx_`
- No -> `poi_`

---

## Review Principles

### Source of Truth

Priority order:
1. `specs/01_philosophy.md`
2. `specs/02_overview.md` (SSOT terminology/dependency)
3. Remaining `specs/*`
4. `guides/*`

### What Review Means

Review is not section summarization.
Review verifies that philosophy propagates consistently into constraints and examples.

### Three Dimensions of Review

| Dimension | Question |
|-----------|----------|
| Consistency | Does this contradict normative principles/SSOT? |
| Coherence | Are numbering, references, and dependency logic consistent? |
| Detailing | Are principles concretely instantiated as enforceable rules? |

### Minimum Review Checklist

1. No contradiction to `specs/01_philosophy.md`
2. Terminology consistency (`ida_`/`prx_`/`poi_`)
3. Section numbering and cross-reference validity
4. Dependency direction preserved
5. AIAD gate passes after spec edits

---

## AIAD Auto-Gate Policy

AIAD outputs are accepted only if the gate passes.

### Gate Stages

1. **Spec gate**
- `scripts/Verify-Spec.py`

2. **Code architecture gate**
- `scripts/Verify-Comsect1Code.py` (3-layer include/dependency checks)

3. **Unified runner**
- `scripts/Verify-AIADGate.py`

### Recommended Commands

```powershell
# Spec-only
python scripts/Verify-Spec.py

# Code architecture check
python scripts/Verify-Comsect1Code.py -Root codes/comsect1

# Unified gate (JSON report)
python scripts/Verify-AIADGate.py -CodeRoot codes/comsect1 -ReportPath .aiad-gate-report.json
```

### Golden Rule

A task that fails the gate is not complete.

---

## Common Mistakes to Avoid

- Putting business policy into `poi_`
- Keeping mechanical wrappers in `prx_`
- `ida_` including `mdw_`/`svc_`/`hal_`/`bsp_`/`cfg_`/`db_`/`stm_`
- Direct cross-feature include (`ida_`/`prx_`/`poi_`) instead of `stm_`
- Skipping gate/report generation after changes

## When Uncertain

1. Read `specs/02_overview.md` (Section 2.7 SSOT)
2. Read `specs/04_layer_roles.md`
3. Read `specs/05_dependency_rules.md`
4. Run the AIAD gate before deciding
5. Ask the user if ambiguity remains

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

