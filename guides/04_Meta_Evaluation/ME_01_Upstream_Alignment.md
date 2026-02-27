# ME-01: Upstream Alignment Guide

> **Purpose**: Define the evaluation hierarchy above the comsect1 specification and provide a process for validating spec changes against upstream philosophy.

---

## 1. The Evaluation Hierarchy

The comsect1 architecture specification does not exist in isolation. It is one layer in a hierarchy of increasingly abstract authorities:

```
The Order          (unreachable ideal; axiom)
    |
Core Intent        (pre-textual; the architect's original recognition)
    |
The_Architect      (upstream philosophy; manuscript)
    |
comsect1 spec      (normative specification; specs/*.md)
    |
AIAD infra         (operational enforcement; Rules/Skill/Agent/Hook/Gate)
    |
Application code   (concrete implementation; project code)
```

**Key principle**: Each layer can only be fully evaluated by the layer above it. The comsect1 spec can verify its own internal consistency (via Verify-Spec.py), but it cannot validate whether its constraints faithfully express the upstream philosophy. That requires consulting The_Architect or, in edge cases, the pre-textual Core Intent.

---

## 2. The_Architect to comsect1 Mapping

| The_Architect Chapter | Core Concept | comsect1 Spec Section | Relationship |
|---|---|---|---|
| Ch. 1: The Order | Unreachable axiom, asymptotic awareness | specs/01_philosophy.md (§1.1) | Foundation: The Order defines the direction |
| Ch. 2: Intent | Core Intent as primary energy | specs/00_why_architecture.md (§0.4), specs/01_philosophy.md (§1.6.9) | Intent drives the 3-Question Discriminator |
| Ch. 3: Structure | Selective Extraction Principle, Grain, Perturbation | specs/05_dependency_rules.md (§5.0), specs/01_philosophy.md (§1.8), specs/03_architecture_structure.md (§3) | Selective Extraction (§5.0) governs dependency rules; Grain manifests as folder layout (§7) and naming (§8); Perturbation justifies layer differentiation (§1.8) |
| Ch. 4: Layer & Boundary | Layer as fossil record, Boundary as membrane | specs/04_layer_roles.md (§4), specs/05_dependency_rules.md (§5) | ida_/prx_/poi_ are the layers; dependency rules define boundaries |
| Ch. 5: Flow | Inversion Principle, Gaze | specs/05_dependency_rules.md (§5.3-5.4), specs/01_philosophy.md (§1.1.2, §1.8) | Dependency direction = inverted flow direction; Gaze = comprehension through upward dependency tracing (§1.1.2) |
| Ch. 6: Change | Adaptation through purpose clarity | specs/01_philosophy.md (§1.6.9), specs/12_version_history.md (§12), guides/02_Execution_Guides/EG_05_Application_Feedback.md | Adaptation capacity proportional to Core Intent clarity (§1.6.9); version history records actual adaptation (§12); feedback loop formalizes the change process (EG_05) |
| Coda: Great Alignment | Continuous alignment process | specs/01_philosophy.md (§1.8), specs/11_checklist.md (§11), scripts/Verify-*.py | Gate scripts enforce ongoing alignment |

### Canonical Term Source

The glossary at `The_Architect/manuscript/glossary.md` is the authoritative source for philosophical terms used across the comsect1 ecosystem. When a spec term appears to conflict with the glossary definition, the glossary takes precedence unless the deviation is explicitly justified and documented.

---

## 3. When to Consult Upstream

### Self-Verification Suffices

- Renaming a section without changing its meaning
- Adding code examples that illustrate existing rules
- Fixing typos, formatting, or cross-reference errors
- Adding checklist items that are already implied by existing rules
- Updating gate scripts to enforce existing normative rules

### Upstream Evaluation Required

- **Adding a new normative rule**: Does it follow from the Selective Extraction Principle?
- **Modifying the 3-Question Discriminator**: Does the change preserve the Intent -> Structure -> Layer philosophical chain?
- **Changing dependency direction rules**: Does the change maintain the Inversion Principle?
- **Redefining a layer role**: Does the redefinition align with the Idea/Praxis/Poiesis etymology (Forms/Action/Production)?
- **Introducing a new resource prefix**: Does the new prefix fit within the data plane / capability plane framework?
- **Modifying philosophical sections (§0, §1)**: These are direct reflections of The_Architect and must be cross-checked.

### Core Intent Required (Beyond The_Architect)

- When The_Architect itself is ambiguous about a particular application domain
- When two upstream principles appear to conflict in a specific context
- When extending the architecture to a paradigm not addressed in The_Architect (e.g., functional programming, distributed systems)

---

## 4. Upstream Alignment Checklist

Before finalizing any spec change that requires upstream evaluation:

- [ ] Identify which The_Architect chapter(s) are relevant to this change
- [ ] Read the relevant chapter and its glossary entry
- [ ] Verify that the change preserves (or strengthens) the concept's meaning
- [ ] If the change extends a concept, document the extension rationale in the spec
- [ ] If the change contradicts upstream, escalate to the author for Core Intent validation
- [ ] Run `Verify-Spec.py` to confirm internal consistency after the change

---

## 5. Documenting Deviations

If a spec decision intentionally deviates from The_Architect's framing:

1. Add a non-normative note in the relevant spec section explaining the deviation
2. Reference the specific The_Architect concept that was adapted
3. Provide the rationale for adaptation (e.g., "embedded constraints require...")
4. Tag the deviation for periodic upstream review

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.0**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
