# comsect1 Architecture

[![Spec Version](https://img.shields.io/badge/spec-v1.0.1-blue)]()
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
|-- specs/                Normative specification
|-- guides/               Shared process and AI entrypoint
|-- scripts/              Verification and scaffolding tools
|-- tooling/              AI-specific packaging
|   |-- INSTALL.md        Shared packaging model (hybrid guide)
|   |-- claude-code/      Claude Code package
|   `-- codex/            Codex package
|-- AGENTS.md             Codex adapter
|-- CLAUDE.md             Claude adapter
`-- README.md             Human-facing overview
```

---

## AI Tooling

All AI integrations follow the **Reference-Based Tooling Principle**
(see `guides/00_AI_ENTRYPOINT.md` Section 9):

> Embed only what is platform-specific. Reference everything else.

Tool-specific configuration files contain only platform metadata and pointers.
All canonical rules, procedures, and output formats live in `guides/` and
`specs/` so that a `git pull` propagates changes to every AI tool at once.

Repository-managed AI tooling surfaces are synchronized by
`scripts/comsect1_ai_tooling.py` and verified by
`scripts/Verify-ToolingConsistency.py`. Do not hand-edit generated adapters,
skills, package docs, wrapper scripts, or the generated blocks inside
`tooling/INSTALL.md` in place.

- Shared entrypoint: [`guides/00_AI_ENTRYPOINT.md`](./guides/00_AI_ENTRYPOINT.md)
- Shared packaging guide: [`tooling/INSTALL.md`](./tooling/INSTALL.md)
  (manual overview + generated consistency blocks)

Tool-specific packages are thin adapters around that entrypoint:

| Tool | Package doc | What it installs |
|------|-------------|------------------|
| Claude Code | [`tooling/claude-code/INSTALL.md`](./tooling/claude-code/INSTALL.md) | minimal user-facing refactor/analyze/review surfaces backed by internal pack-aligned files |
| Codex | [`tooling/codex/INSTALL.md`](./tooling/codex/INSTALL.md) | minimal user-facing refactor/analyze/review skills + project bootstrap |

The generic sub-agent pack taxonomy is defined once in
[`guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`](./guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md)
and then exposed through thin provider-native surfaces.

Default command model:

- `comsect1-refactor`: primary end-to-end command, including internal analysis
- `comsect1-analyze`: standalone analysis-only command
- `comsect1-review`: standalone review-only command where supported

Pack taxonomy remains canonical underneath those commands, but end users should
not need to choose from a large pack-level command set during normal work.

---

## Architecture at a Glance

### 3-Layer Feature Model

| Layer | Prefix | Responsibility |
|-------|--------|----------------|
| Idea | `ida_` | WHAT/WHEN intent and decisions |
| Praxis | `prx_` | External-type-coupled domain interpretation |
| Poiesis | `poi_` | Mechanical production, bridging, wrapping |

### Dependency Rules

```text
IDA -> { own PRX, own POI }
PRX -> { own POI, mdw_, svc_, hal_, cfg_, db_, stm_ }
POI -> { mdw_, svc_, hal_, cfg_, db_, stm_ }
Feature <-> Feature: stm_ only
```

`IDA -> { own PRX, own POI }` is a fixed allowed dependency set, not a
mandatory dual-call rule.

---

## Reading Paths

### For Humans

- Quick start: [guides/00_Onboarding_30min.md](./guides/00_Onboarding_30min.md)
- Full workflow: [guides/00_Process_Overview.md](./guides/00_Process_Overview.md)
- SSOT entry point: [specs/02_overview.md](./specs/02_overview.md)

Recommended spec order:

1. [specs/00_why_architecture.md](./specs/00_why_architecture.md)
2. [specs/01_philosophy.md](./specs/01_philosophy.md)
3. [specs/02_overview.md](./specs/02_overview.md)
4. [specs/04_layer_roles.md](./specs/04_layer_roles.md)
5. [specs/05_dependency_rules.md](./specs/05_dependency_rules.md)
6. [specs/08_naming_conventions.md](./specs/08_naming_conventions.md)
7. [specs/11_checklist.md](./specs/11_checklist.md)

### For AI Agents

- Shared entrypoint: [`guides/00_AI_ENTRYPOINT.md`](./guides/00_AI_ENTRYPOINT.md)
- Thin adapters: [`CLAUDE.md`](./CLAUDE.md), [`AGENTS.md`](./AGENTS.md)
- Machine gate: `scripts/Verify-*.py`

---

## Verification

```powershell
python scripts/Verify-Spec.py
python scripts/Verify-ToolingConsistency.py
python scripts/Verify-Comsect1Code.py -Root codes/comsect1
python scripts/Verify-AIADGate.py -CodeRoot codes/comsect1 -ReportPath .aiad-gate-report.json
```

A task that fails the gate is not complete.

---

## Specification Index

| Section | File |
|---------|------|
| 0. Preface | [specs/00_why_architecture.md](./specs/00_why_architecture.md) |
| 1. Philosophy | [specs/01_philosophy.md](./specs/01_philosophy.md) |
| 2. Overview (SSOT) | [specs/02_overview.md](./specs/02_overview.md) |
| 3. Structure | [specs/03_architecture_structure.md](./specs/03_architecture_structure.md) |
| 4. Layers | [specs/04_layer_roles.md](./specs/04_layer_roles.md) |
| 5. Dependencies | [specs/05_dependency_rules.md](./specs/05_dependency_rules.md) |
| 6. Errors | [specs/06_error_handling.md](./specs/06_error_handling.md) |
| 7. Folders | [specs/07_folder_structure.md](./specs/07_folder_structure.md) |
| 8. Naming | [specs/08_naming_conventions.md](./specs/08_naming_conventions.md) |
| 9. Examples | [specs/09_code_examples.md](./specs/09_code_examples.md) |
| 10. Anti-patterns | [specs/10_anti_patterns.md](./specs/10_anti_patterns.md) |
| 11. Checklist | [specs/11_checklist.md](./specs/11_checklist.md) |
| 12. History | [specs/12_version_history.md](./specs/12_version_history.md) |
| 13. Middleware | [specs/13_middleware_guideline.md](./specs/13_middleware_guideline.md) |
| 14. Standard Packages | [specs/14_standard_packages.md](./specs/14_standard_packages.md) |
| Appendix A1 | [specs/A1_exception_handling.md](./specs/A1_exception_handling.md) |
| Appendix A2 | [specs/A2_oop_adaptation.md](./specs/A2_oop_adaptation.md) |

---

## License

| Content | License |
|---------|---------|
| Specification | CC BY-NC-ND 4.0 |
| Scripts | MIT License |

---

**Author:** Kim Hyeongjeong (Republic of Korea)  
**Version:** 1.0.1
