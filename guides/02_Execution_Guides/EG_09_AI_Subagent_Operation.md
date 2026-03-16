# EG-09: AI Sub-Agent Pack Taxonomy

This guide defines the canonical sub-agent pack taxonomy for comsect1
refactoring and maintenance work.

The goal is not to standardize provider-specific role names. The goal is to
define the stable pack boundaries that every provider package must map to
through thin adapters.

---

## 1. Purpose

Use this guide when designing or maintaining AI tooling for:

- refactoring existing comsect1 projects
- maintaining conformance across long-lived projects
- redesigning provider tooling around stable comsect1 invariants

This guide complements:

- `guides/00_AI_ENTRYPOINT.md` for the shared entry policy
- `guides/00_Process_Overview.md` for the standard development workflow
- `guides/02_Execution_Guides/EG_07_Analysis_Procedure.md` for deep analysis
- `guides/02_Execution_Guides/EG_08_Review_Procedure.md` for compliance review

---

## 2. Single Entrypoint Principle

Every provider package MUST preserve a single shared operational entrypoint:

`guides/00_AI_ENTRYPOINT.md`

Provider-specific files do not become new sources of architecture truth.
They only provide:

- provider-native syntax
- provider-native packaging
- role selection and invocation surfaces

The meaning of each pack lives here, not in the provider package.

---

## 3. Pack Design Rule

Sub-agent packs MUST be derived from stable architecture pressures, not from
temporary session tasks or convenient conversational labels.

For comsect1, the stable pressures are:

- operating mode and workflow control
- physical structure and migration correctness
- semantic layer and dependency correctness
- anti-pattern and exception risk
- verification, governance, and escalation
- optional write-enabled execution

Packs should therefore be defined around those pressures.

---

## 4. Canonical Pack Taxonomy

Every multi-agent comsect1 package MUST expose the following core packs.

### 4.1 Director Pack

**Purpose**:

- classify the task and repository mode
- choose which packs are needed
- order the work
- merge outputs into one refactoring or maintenance plan
- own final verification and close-out

This pack is the only pack that should reason about the full task sequence from
intake to completion.

Primary references:

- `guides/00_AI_ENTRYPOINT.md`
- `guides/00_Process_Overview.md`
- `guides/03_Verification/V_01_Post_Task_Checklist.md`
- `guides/03_Verification/V_02_AIAD_Auto_Gate.md`

### 4.2 Structure & Migration Pack

**Purpose**:

- inspect folder skeleton and layout grouping
- inspect naming and path placement
- detect misplaced files and legacy layout leftovers
- detect build-path drift tied to structure
- define physical migration order before semantic rebuilding starts

Primary references:

- `specs/07_folder_structure.md`
- `specs/08_naming_conventions.md`
- `specs/11_checklist.md`
- `guides/02_Execution_Guides/EG_02_Refactoring_Legacy.md`

### 4.3 Layer & Dependency Pack

**Purpose**:

- apply the 3-question discriminator
- inspect `ida_` / `prx_` / `poi_` placement
- inspect layer balance and reverse dependencies
- inspect feature isolation and data-plane boundaries
- verify `svc_` role authenticity (infrastructure wrap or reusable
  computation, not cross-feature data dispatch)
- identify what logic must move, split, or be rebuilt across layers

Primary references:

- `specs/02_overview.md`
- `specs/04_layer_roles.md`
- `specs/05_dependency_rules.md`
- `specs/A2_oop_adaptation.md`
- `guides/01_Design_Principles/DP_03_Praxis_Justification.md`

### 4.4 Risk & Exception Pack

**Purpose**:

- scan for anti-patterns and red flags
- detect unreasonable logic placement and suspicious abstractions
- inspect exception growth, workaround accumulation, and review hotspots
- distinguish project error from spec ambiguity, gap, or overreach
- feed recurring patterns into the ADR and feedback loop

Primary references:

- `specs/10_anti_patterns.md`
- `specs/11_checklist.md`
- `guides/02_Execution_Guides/EG_05_Application_Feedback.md`
- `guides/04_Meta_Evaluation/ME_01_Upstream_Alignment.md`

### 4.5 Verification & Governance Pack

**Purpose**:

- run or coordinate post-task verification
- run gates and collect evidence
- check tooling drift and packaging consistency when this repository is edited
- route ADR and upstream-alignment escalation when needed

Primary references:

- `guides/03_Verification/V_01_Post_Task_Checklist.md`
- `guides/03_Verification/V_02_AIAD_Auto_Gate.md`
- `guides/03_Verification/V_03_Multi_Project_Gate.md`
- `guides/04_Meta_Evaluation/ME_01_Upstream_Alignment.md`

### 4.6 Execution Pack (Optional)

**Purpose**:

- perform write-enabled refactoring or implementation work
- apply the Director Pack plan and the constraints discovered by the other packs
- preserve discriminator records and verification discipline

This pack is optional because some provider packages may expose only analysis
and review surfaces, while leaving write-enabled execution to the main session
agent.

---

## 5. Pack Collaboration Order

The canonical sequence is:

1. Director Pack reads the shared entrypoint and this guide.
2. Structure & Migration Pack establishes physical conformance and migration
   order.
3. Layer & Dependency Pack inspects semantic correctness and rebuild targets.
4. Risk & Exception Pack scans for anti-patterns, exception creep, and
   escalation signals.
5. Director Pack merges outputs into one ordered plan.
6. Execution Pack performs code changes when needed.
7. Verification & Governance Pack runs final verification and evidence capture.

Do not reverse this order without a concrete reason.
Structural repair comes before semantic rebuilding. Semantic rebuilding comes
before anti-pattern judgment. Verification closes the loop.

---

## 6. Output Contract

Each pack should produce a focused output.

### 6.1 Director Pack Output

- task classification
- selected packs
- ordered execution plan
- verification plan
- final synthesis

### 6.2 Structure & Migration Pack Output

- structural violations
- misplaced files
- naming/path issues
- migration sequencing
- build-path cleanup targets

### 6.3 Layer & Dependency Pack Output

- discriminator records
- boundary violations
- dependency cleanup targets
- layer split or rebuild plan
- layer balance findings

### 6.4 Risk & Exception Pack Output

- anti-pattern name
- file or feature scope
- rule or checklist reference
- blocking or advisory classification
- feedback-loop escalation note when the pattern suggests ambiguity, overreach,
  or false-positive heuristics

### 6.5 Verification & Governance Pack Output

- checklist status
- gate results
- evidence paths
- ADR or upstream-alignment escalation note when needed

### 6.6 Execution Pack Output

- implemented changes
- discriminator record preservation note
- verification readiness note

---

## 7. Provider Packaging Rules

Provider packages under `tooling/<tool>/` MUST stay thin.

Rules:

- Do not copy canonical rules into provider files.
- Do not define different pack meanings per provider.
- Do not let install docs become architecture manuals.
- Provider packages may differ in syntax and file layout, but not in the
  semantic pack taxonomy.

Minimum provider surface for a full multi-agent package:

- one Director Pack surface
- one Structure & Migration Pack surface
- one Layer & Dependency Pack surface
- one Risk & Exception Pack surface
- one Verification & Governance Pack surface

Optional provider surface:

- one Execution Pack surface

Additional provider surfaces such as general analysis or compatibility review
may exist, but they do not replace the canonical pack taxonomy above.

---

## 8. Pack-to-Surface Mapping Rule

The canonical unit is the **pack**, not the provider-native surface.

Examples:

- one provider may expose a pack as a skill
- another provider may expose the same pack as an agent
- a provider may use a compatibility helper surface such as `analyze` or
  `review`, but that helper is not the canonical taxonomy

Provider naming may vary slightly, but the provider documentation must make the
mapping back to the canonical pack explicit.

### 8.1 Primary One-Command Surface

For normal downstream use, provider packages SHOULD expose one primary
refactoring surface, such as `refactor`, that performs the full sequence:

0. Analysis pre-phase (using `EG_07` as the internal analysis procedure)
1. Director
2. Structure & Migration
3. Layer & Dependency
4. Risk & Exception
5. Execution (when needed)
6. Verification & Governance

This one-command surface is the preferred user entry for end-to-end
maintenance and refactoring work.

Rules:

- it MUST still read the shared entrypoint first
- it MUST perform an initial analysis phase before implementation decisions
- it MUST internally follow the canonical pack order
- it MUST not redefine pack meanings
- it MAY reuse helper surfaces such as `analyze` or `review`, but those remain
  secondary utilities

Interpretation:

- `refactor` = end-to-end command that includes analysis internally
- `analyze` = standalone analysis-only surface when diagnosis/reporting is wanted
- `review` = standalone compliance-review surface when findings-only output is wanted

### 8.2 Visible Surface Minimization

The canonical pack taxonomy does not require every pack to appear as a
separate user-visible command.

For normal downstream use, providers SHOULD keep the visible command set
minimal:

- `refactor`
- `analyze`
- `review`

The pack taxonomy remains canonical underneath that command layer. Provider
packages may keep Director, Structure, Layer, Risk, Verification, and
Execution surfaces as internal implementation detail, but should avoid
presenting them all as top-level user commands unless there is a concrete,
tool-specific reason.

---

## 9. Downstream Project Rule

Downstream projects should not hand-author their own multi-agent architecture.

They should receive:

- one thin project adapter from the provider package
- the shared canonical entrypoint reference
- project-local rules only

If a project needs a local exception, record it in project-local notes or ADRs.
Do not fork the canonical pack taxonomy in the provider package.

---

## 10. Maintenance Rule

When the pack taxonomy changes:

1. update this guide first
2. update the generator in `scripts/comsect1_ai_tooling.py`
3. sync generated provider surfaces
4. verify tooling consistency
5. update package documentation

When only provider syntax changes:

1. update the provider-specific generated surface or template
2. sync
3. verify tooling consistency

When only a downstream project note changes:

1. update the downstream thin adapter
2. do not modify the canonical pack definitions

---

## 11. Verification

For this repository, changes to the multi-agent tooling model should be
verified with:

```powershell
python scripts/comsect1_ai_tooling.py sync-repo
python scripts/Verify-ToolingConsistency.py
python scripts/Verify-Spec.py
```

The gate remains an acceptance surface, not the primary place where role
meaning is maintained.

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.0**.

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
