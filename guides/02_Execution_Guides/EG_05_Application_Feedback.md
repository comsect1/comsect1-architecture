# EG-05: Application Feedback Loop

> **Purpose**: Define how lessons from applying comsect1 in real projects feed back into specification improvement. This guide bridges the gap between theoretical completeness and operational maturity.

---

## 1. The Feedback Loop

The comsect1 specification is not a static document. It evolves through contact with real projects:

```
Specification → Application → Friction → Analysis → Improvement → Specification
```

Not all friction indicates a spec gap. The first task is to distinguish between:

1. **Application error**: The project misunderstood or misapplied the spec. Fix the project.
2. **Spec gap**: The spec does not address a legitimate concern. Extend the spec.
3. **Spec ambiguity**: The spec is unclear, leading to divergent interpretations. Clarify the spec.
4. **Spec overreach**: The spec imposes a constraint that harms the project without serving intent. Relax the spec.

---

## 2. Identifying Friction Points

### Symptoms of Friction

- Repeated gate failures on the same rule across different features
- Developers creating workarounds (e.g., "utility" files that bypass layer structure)
- Praxis layer appearing in most features (possible overuse)
- Feature boundaries that feel arbitrary or change frequently
- Cross-feature data flow that requires multiple stm_ indirections

### Recording Friction

When a friction point is identified, document it immediately using the Architecture Decision Record (ADR) template below. Do not wait for resolution.

---

## 3. Architecture Decision Record (ADR) Template

Create ADR files in the project's `docs/adr/` directory (not in the spec repo).

**Filename convention**: `ADR-NNN-short-description.md`

```markdown
# ADR-NNN: [Short Title]

## Status
[Proposed | Accepted | Superseded by ADR-XXX | Rejected]

## Date
YYYY-MM-DD

## Context
What is the situation? What constraint or friction triggered this decision?

## comsect1 Reference
Which spec section(s) are relevant? (e.g., §4.3 3-Question Discriminator, §5.2 dependency rules)

## Decision
What was decided and why?

## Classification
- [ ] Application error (project-side fix)
- [ ] Spec gap (spec improvement needed)
- [ ] Spec ambiguity (clarification needed)
- [ ] Spec overreach (relaxation needed)
- [ ] None of the above (project-specific tradeoff)

## Consequences
What are the positive and negative outcomes of this decision?

## Upstream Escalation
- [ ] Not needed — resolved within project scope
- [ ] Spec clarification submitted (link/issue)
- [ ] Spec change proposed (link/issue)
```

---

## 4. Decision Tree: Application Error vs. Spec Issue

```
Friction observed
    |
    Q1: Does the spec clearly address this case?
    |-- Yes: Is the project following the spec correctly?
    |   |-- Yes: Is the constraint causing real harm?
    |   |   |-- Yes → Spec overreach (consider relaxation)
    |   |   |-- No  → Not a friction point (false alarm)
    |   |-- No  → Application error (fix the project)
    |-- No: Is the case a reasonable extension of existing rules?
        |-- Yes → Spec gap (extend the spec)
        |-- No  → Spec ambiguity (clarify existing rules)
```

---

## 5. Escalation Process

### Level 1: Project-Local (Most Common)

- Document in ADR
- Apply project-specific resolution
- Run gate to verify compliance
- No spec change needed

### Level 2: Spec Clarification

The spec text is correct but ambiguous. Resolution:

1. Identify the ambiguous section
2. Propose clarifying text or example
3. Verify against upstream alignment (see ME_01_Upstream_Alignment.md)
4. Submit clarification to spec repo

### Level 3: Spec Change

The spec needs a new rule, modified rule, or relaxed constraint. Resolution:

1. Document the friction in ADR with classification "spec gap" or "spec overreach"
2. Draft the proposed spec change
3. Verify upstream alignment — does the change preserve the philosophical chain?
4. Run Verify-Spec.py after the change
5. If the change touches §0-§1 (philosophy) or the 3-Question Discriminator → upstream evaluation required (see ME_01 §3)

---

## 6. Common Feedback Patterns

### Pattern: Praxis Proliferation

**Symptom**: Every feature has a prx_ file.

**Diagnosis**: Usually an application error. Teams default to prx_ when unsure, treating it as a "middle ground." The 3-Question Discriminator (§4.3) should eliminate most prx_ files.

**Resolution**: Apply the Quick Decision Checklist from DP_03_Praxis_Justification.md. If most prx_ files fail the checklist, refactor them to ida_+poi_ splits.

### Pattern: Feature Boundary Instability

**Symptom**: Files move between features frequently; feature boundaries are redrawn.

**Diagnosis**: Often a spec gap — the project's domain doesn't map cleanly to the spec's feature model.

**Resolution**: Document the domain mapping in an ADR. Consider whether the feature boundaries reflect domain aggregates or are drawn along technical lines. comsect1 features should align with domain capabilities, not technical modules.

### Pattern: Middleware Creep

**Symptom**: mdw_ or svc_ layers grow large and contain domain-specific logic.

**Diagnosis**: Spec ambiguity — the boundary between "shared capability" and "feature-specific logic" is unclear.

**Resolution**: If the logic serves a single feature, move it into that feature's prx_ or poi_. Middleware must remain domain-agnostic.

### Pattern: Gate False Positives

**Symptom**: Gate scripts flag code that is architecturally correct.

**Diagnosis**: Gate scripts are heuristic-based and may not understand context.

**Resolution**: Record the false positive pattern. If it recurs, improve the gate heuristic or add an exclusion mechanism. Do not suppress the gate.

---

## 7. Feedback Aggregation

Periodically (e.g., per release cycle or quarterly), review accumulated ADRs:

1. Count ADRs by classification (application error, spec gap, spec ambiguity, spec overreach)
2. Identify clusters — multiple ADRs pointing to the same spec section indicate a hotspot
3. For each hotspot, decide whether spec improvement is warranted
4. If improvement is warranted, follow the escalation process (§5)

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.0**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
