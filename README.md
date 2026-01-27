# comsect1 Architecture

[![Spec Version](https://img.shields.io/badge/spec-v1.0.0-blue)]()
[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/Specs-CC_BY--NC--ND_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)
[![License: MIT](https://img.shields.io/badge/Scripts-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**COMmon Software Engineering Codex Top 1**

Intent-driven layered architecture for embedded systems and beyond.

An open architecture specification where **Idea's intent defines the contract**.

---

## Repository Structure

This repository is an **AIAD (AI-Assisted Development) operational environment**:
a normative specification that AI agents can read, understand, and enforce.

```text
.
|-- specs/                Normative specification (15 documents)
|-- guides/               Practical guides
|   |-- 00_*              Onboarding & process overview
|   |-- 01_Design_*/      Core architecture & realtime design principles
|   |-- 02_Execution_*/   New project, refactoring, testing, build
|   `-- 03_Verification/  Post-task checklist & AIAD auto gate
|-- scripts/              Verification & scaffolding tools
|-- CLAUDE.md             AI agent operational guidelines
|-- LICENSE               CC BY-NC-ND 4.0 (specs) + MIT (scripts)
`-- README.md             This file
```

---

## Architecture at a Glance

### The 3-Layer Feature Model

| Layer | Prefix | Responsibility |
|-------|--------|----------------|
| Idea | `ida_` | WHAT/WHEN intent and decisions |
| Praxis | `prx_` | External-type-coupled domain interpretation |
| Poiesis | `poi_` | Mechanical production/bridging/wrapping |

### Dependency Rules

```
IDA -> { own PRX, own POI }
PRX -> { own POI, mdw_, svc_, hal_, cfg_, db_, stm_ }
POI -> { mdw_, svc_, hal_, cfg_, db_, stm_ }
Feature <-> Feature: stm_ only
```

`IDA -> { own PRX, own POI }` is a fixed **allowed dependency set**, not a mandatory dual-call rule.

### Orthogonal Boundary Model

- **Data plane**: `stm_` for feature-to-feature runtime state/event flow.
- **Capability plane**: `mdw_`/`svc_`/`hal_`/`bsp_` for execution/resource control.

---

## Reading Paths

### For Humans

**Quick start**: [30-Minute Onboarding](./guides/00_Onboarding_30min.md)

**Full workflow**: [Standard Development Process](./guides/00_Process_Overview.md) (learn -> execute -> verify -> gate)

**Specification reading order**:

1. [00_why_architecture.md](./specs/00_why_architecture.md)
2. [01_philosophy.md](./specs/01_philosophy.md)
3. [02_overview.md](./specs/02_overview.md) - SSOT entry point
4. [03_architecture_structure.md](./specs/03_architecture_structure.md)
5. [04_layer_roles.md](./specs/04_layer_roles.md)
6. [05_dependency_rules.md](./specs/05_dependency_rules.md)
7. [08_naming_conventions.md](./specs/08_naming_conventions.md)
8. [11_checklist.md](./specs/11_checklist.md)
9. [12_version_history.md](./specs/12_version_history.md)

### For AI Agents

- **Operational guidelines**: [`CLAUDE.md`](./CLAUDE.md) - architecture conventions, dependency rules, 3-question discriminator, and verification policy.
- **Source of truth**: [`specs/02_overview.md`](./specs/02_overview.md) (Section 2.7 SSOT).
- **Verification**: `scripts/Verify-*.py` - machine-enforceable architecture gate.

---

## Verification

### Spec Gate

```powershell
python scripts/Verify-Spec.py
```

### Code Architecture Gate

```powershell
python scripts/Verify-Comsect1Code.py -Root codes/comsect1
```

### AIAD Unified Gate

```powershell
python scripts/Verify-AIADGate.py -CodeRoot codes/comsect1 -ReportPath .aiad-gate-report.json
```

All normative rules are enforced without relaxation profiles.
A task that fails the gate is not complete.

Guides: [Post-Task Checklist](./guides/03_Verification/V_01_Post_Task_Checklist.md) | [AIAD Auto Gate](./guides/03_Verification/V_02_AIAD_Auto_Gate.md)

---

## Specification Index

| Section | File |
|---------|------|
| 0. Preface | [00_why_architecture.md](./specs/00_why_architecture.md) |
| 1. Philosophy | [01_philosophy.md](./specs/01_philosophy.md) |
| 2. Overview (SSOT) | [02_overview.md](./specs/02_overview.md) |
| 3. Structure | [03_architecture_structure.md](./specs/03_architecture_structure.md) |
| 4. Layers | [04_layer_roles.md](./specs/04_layer_roles.md) |
| 5. Dependencies | [05_dependency_rules.md](./specs/05_dependency_rules.md) |
| 6. Errors | [06_error_handling.md](./specs/06_error_handling.md) |
| 7. Folders | [07_folder_structure.md](./specs/07_folder_structure.md) |
| 8. Naming | [08_naming_conventions.md](./specs/08_naming_conventions.md) |
| 9. Examples | [09_code_examples.md](./specs/09_code_examples.md) |
| 10. Anti-patterns | [10_anti_patterns.md](./specs/10_anti_patterns.md) |
| 11. Checklist | [11_checklist.md](./specs/11_checklist.md) |
| 12. History | [12_version_history.md](./specs/12_version_history.md) |
| 13. Middleware | [13_middleware_guideline.md](./specs/13_middleware_guideline.md) |
| Appendix A | [A1_exception_handling.md](./specs/A1_exception_handling.md) |

---

## License

| Content | License |
|---------|---------|
| Specification | CC BY-NC-ND 4.0 |
| Scripts | MIT License |

---

**Author:** Kim Hyeongjeong (Republic of Korea)
**Version:** 1.0.0

