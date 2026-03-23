# comsect1 Unified AI Entrypoint

This document is the single operational entrypoint for AI tools that work with
the comsect1 architecture. Tool-specific adapters such as `CLAUDE.md`,
`AGENTS.md`, installed global rules, and installed skills must stay thin and
point here.

Do not maintain duplicated architecture rules in multiple AI-specific files.
If a common instruction changes, update this document and the canonical spec,
not every adapter.

---

## 1. Operating Policy

- Conversation language: Korean unless the user clearly requests another
  language.
- All artifacts: English only.
  - Documentation
  - Code and comments
  - Commit messages
  - File names
- All text artifacts: UTF-8 without BOM unless the target tool explicitly
  requires another encoding.
- Never rely on OS-default encoding when reading or writing files. Explicitly
  choose UTF-8 when the tool allows it.
- Preserve philosophical precision when discussing intent and rationale.
- Prefer concrete, enforceable language when discussing technical rules.

### 1.1 Destructive Operation Safety

Treat workspace roots, multi-repository parent directories, drive roots, home
directories, and other shared parent paths as high-risk boundaries.

Rules:

- Never execute destructive commands against a high-risk boundary based on
  inference, convenience, or pattern matching.
- Destructive commands include, at minimum: recursive delete, force delete,
  mass move, overwrite restore, re-clone into an existing path, `git clean`,
  `git reset --hard`, and similar scope-expanding operations.
- If the requested action affects more than one repository or targets a parent
  directory above the current repository, the agent MUST restate the exact
  absolute paths and the exact destructive action, then obtain explicit user
  confirmation after that restatement before executing anything.
- A vague request such as "clean it", "delete the leftovers", "reclone
  everything", or "reset the repos" is not sufficient authorization for
  deleting inferred sibling paths.
- Repo-local artifact cleanup is allowed only for explicitly named build or
  output directories inside the current repository.
- Prefer non-destructive recovery first: clone into a separate recovery path
  or sibling `*_recovered` directory before deleting or overwriting the
  original path.
- Before any destructive action, capture and report the current state of the
  target scope: absolute path, whether it is a git repository, and what
  immediate children will be affected.
- If target ownership or scope is ambiguous, stop and ask. Do not widen the
  scope.

---

## 2. Canonical Source Priority

Treat this repository as the canonical comsect1 source of truth.

Priority order:

1. `specs/01_philosophy.md`
2. `specs/02_overview.md`
3. `specs/04_layer_roles.md`
4. `specs/05_dependency_rules.md`
5. `specs/07_folder_structure.md`
6. `specs/08_naming_conventions.md`
7. `specs/11_checklist.md`
8. `specs/14_standard_packages.md`
9. `specs/A2_oop_adaptation.md` for OOP projects
10. `guides/00_Process_Overview.md`
11. Task-specific guides under `guides/01_*`, `guides/02_*`, `guides/03_*`
12. Gate scripts under `scripts/`

If something is defined in `specs/`, do not override it with summaries, memory,
or AI-specific adapter files.

---

## 3. Architecture Quick Reference

### 3.1 3-Layer Feature Model

| Layer | Prefix | Responsibility |
|-------|--------|----------------|
| Idea | `ida_` | WHAT/WHEN/WHICH intent and business decisions |
| Praxis | `prx_` | Externally-coupled domain interpretation |
| Poiesis | `poi_` | Mechanical production, wrapping, bridging |

Core defaults:
- `ida_core` is the policy anchor.
- `poi_core` is the execution anchor.
- `prx_core` is optional and requires discriminator-based justification.

### 3.2 Dependency Rules

```text
IDA -> { own PRX, own POI }
PRX -> { own POI, mdw_, svc_, hal_, cfg_, db_, stm_ }
POI -> { mdw_, svc_, hal_, cfg_, db_, stm_ }
Feature <-> Feature: stm_ only
Platform: HAL -> BSP
```

Interpret `IDA -> { own PRX, own POI }` as a fixed allowed dependency set, not a
mandatory dual-call rule.

### 3.3 Access Rules

| Resource | Idea | Praxis/Poiesis |
|----------|------|----------------|
| `cfg_core` | Yes | Yes |
| project config | No | Yes |
| feature `cfg_` / `db_` | No | Yes |
| `stm_` datastream | No | Yes |

---

## 4. Mandatory Working Procedure

1. Identify the task type.
   - Spec editing
   - New project setup
   - Legacy refactoring
   - Architecture review
   - Gate-only validation
2. Read the minimum relevant canonical files before acting.
3. For any code or class placement decision, explicitly answer the
   3-question discriminator before writing code.
4. Execute using the standard workflow in `guides/00_Process_Overview.md`.
5. Verify with `guides/03_Verification/V_01_Post_Task_Checklist.md`.
6. Run the appropriate machine gate from `scripts/`.
7. Treat any failed gate as incomplete work.

---

## 5. Mandatory 3-Question Discriminator

Before writing or refactoring any `ida_`, `prx_`, or `poi_` unit, explicitly
answer:

1. External dependency required?
   - No -> `ida_`
   - Yes -> Question 2
2. Separable domain judgment without external types?
   - Yes -> split `ida_` + `poi_`
   - No -> Question 3
3. Inseparable domain judgment coupled to external types?
   - Yes -> `prx_`
   - No -> `poi_`

Record the discriminator result before generating code:

```text
Feature: [name]
Q1 (external dep?): [Yes/No] -> [...]
Q2 (separable judgment?): [Yes/No] -> [...]
Q3 (inseparable coupling?): [Yes/No] -> [...]
Final layer assignment: [...]
```

When `prx_` is proposed, justify it explicitly. If the logic is only mechanical,
it belongs in `poi_`. If the logic is pure domain judgment, it belongs in
`ida_`.

---

## 6. Review Standard

Review is not summarization. Review verifies that philosophy propagates
correctly into constraints, structure, and examples.

Check every review across three dimensions:

| Dimension | Question |
|-----------|----------|
| Consistency | Does this contradict the canonical spec or SSOT terminology? |
| Coherence | Are numbering, references, naming, and dependency logic aligned? |
| Detailing | Are principles instantiated as concrete, enforceable rules? |

For review tasks:
- Cite the specific spec file or guide that governs each finding.
- Distinguish blocking violations from advisory observations.
- When code is present, run the relevant gate if feasible.

---

## 7. Verification Policy

Use these gates as the acceptance criteria:

- `python scripts/Verify-Spec.py`
- `python scripts/Verify-ToolingConsistency.py`
- `python scripts/Verify-Comsect1Code.py -Root <comsect1-root>`
- `python scripts/Verify-OOPCode.py -Root <comsect1-root>`
- `python scripts/Verify-AIADGate.py -CodeRoot <comsect1-root> -ReportPath .aiad-gate-report.json`

Golden rule:

> A task that fails the gate is not complete.

Use `guides/03_Verification/V_02_AIAD_Auto_Gate.md` as the operational guide for
machine validation.

---

## 8. Repository Modes

### 8.1 Canonical Spec Repository

When the current repository is `comsect1-doc-architecture` itself:

- Treat `specs/`, `guides/`, `scripts/`, and `tooling/` as the product.
- Run at least the spec gate after editing normative documents or tooling that
  depends on them.
- When AI tooling adapters, skills, wrapper scripts, or generated blocks inside
  `tooling/INSTALL.md` change, run
  `python scripts/comsect1_ai_tooling.py sync-repo` and
  `python scripts/Verify-ToolingConsistency.py`.
- Use `guides/04_Meta_Evaluation/ME_01_Upstream_Alignment.md` when upstream
  alignment becomes relevant.

### 8.2 Downstream Implementation Repository

When another project references this repository as SSOT:

- Read this entrypoint first through the local AI adapter file.
- Use this repository's `scripts/` as the architecture gate.
- Keep the downstream `CLAUDE.md` or `AGENTS.md` thin.
- Put only project-local additions in the downstream adapter file.

---

## 9. AI Tooling Design Principle

All AI tool configuration files (SKILL.md, AGENT.md, rules files, templates)
MUST reference canonical specs and guides rather than embed their content.

### Rule

> Embed only what is platform-specific. Reference everything else.

**Platform-specific content** (allowed to embed):
- Tool-specific YAML frontmatter (name, description, model, maxTurns, tools)
- Tool-specific invocation syntax (`$ARGUMENTS`, `!git ls-files`, etc.)
- Step 0: list of canonical sources to load before acting

**Canonical content** (must reference, never embed):
- Architecture rules, check lists, procedures, output formats
- Any rule that would also apply to a different AI tool

### 9.1 Generic Sub-Agent Pack Taxonomy

When a provider package exposes multiple AI surfaces, those surfaces MUST map
to the same canonical pack taxonomy defined in:
`guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`

Required core packs:
- Director Pack
- Structure & Migration Pack
- Layer & Dependency Pack
- Risk & Exception Pack
- Verification & Governance Pack

Optional pack:
- Execution Pack

Provider packages may express these packs as skills, agents, reviewers, or
equivalent provider-native surfaces, but the pack meaning MUST remain aligned
with the canonical guide and the provider surface MUST remain thin.

Provider packages SHOULD also expose one primary end-to-end refactoring
surface for normal use. That surface is a user-facing command layer above the
pack taxonomy, not a replacement for it.

When the provider supports multiple visible commands, keep the user-facing
surface minimal. Prefer exposing only:

- `refactor` for end-to-end work
- `analyze` for analysis-only work
- `review` for findings-only review

Pack-specific surfaces may still exist as provider-internal implementation
detail, but they should not be multiplied as user-facing commands unless the
provider has a concrete operational reason.

### Rationale

Embedding canonical content in AI configuration files creates drift: when a
rule changes, every configuration file that copied it must also change. A
single missed update produces inconsistency across tools.

Referencing instead means a `git pull` propagates every rule change to all
tools simultaneously. This is SSOT applied to the AI tooling layer.

### Enforcement

Any AI configuration file that restates a rule already defined in a canonical
spec or guide is in violation of this principle. The fix is always: remove
the embedded content and add a reference path using `{{COMSECT1_ROOT}}/`.

Generated AI tooling surfaces and generated blocks inside `tooling/INSTALL.md`
are synchronized by `scripts/comsect1_ai_tooling.py`. If those surfaces drift
from the generator, `scripts/Verify-ToolingConsistency.py` must fail.

---

## 10. When Uncertain

1. Re-read `specs/02_overview.md`.
2. Re-read the relevant layer or dependency spec.
3. Read `guides/01_Design_Principles/DP_03_Praxis_Justification.md` when
   `prx_` justification is unclear.
4. Run the relevant gate or checklist.
5. Ask the user only if ambiguity remains after those steps.

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.1**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

You are free to:
- **Share** - copy and redistribute the material in any medium or format for
  non-commercial purposes only.

Under the following terms:
- **Attribution** - You must give appropriate credit to the author (Kim
  Hyeongjeong), provide a reference to the license, and indicate if changes
  were made.
- **NonCommercial** - You may not use the material for commercial purposes.
- **NoDerivatives** - If you remix, transform, or build upon the material, you
  may not distribute the modified material.

No additional restrictions - You may not apply legal terms or technological
measures that legally restrict others from doing anything the license permits.

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
