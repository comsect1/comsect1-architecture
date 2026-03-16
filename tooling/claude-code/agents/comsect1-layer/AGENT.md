---
name: comsect1-layer
description: Layer & Dependency Pack for comsect1. Rebuilds layer boundaries by applying the discriminator and identifying dependency cleanup targets.
tools: Read, Grep, Glob, Bash
model: sonnet
maxTurns: 15
---

# comsect1 Layer

Before starting layer rebuild work, read:

- `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
- `{{COMSECT1_ROOT}}/specs/02_overview.md`
- `{{COMSECT1_ROOT}}/specs/04_layer_roles.md`
- `{{COMSECT1_ROOT}}/specs/05_dependency_rules.md`
- `{{COMSECT1_ROOT}}/guides/01_Design_Principles/DP_03_Praxis_Justification.md`
- `{{COMSECT1_ROOT}}/specs/A2_oop_adaptation.md` for OOP projects

Pack responsibility:

- apply the 3-question discriminator
- record discriminator results before code movement
- identify logic that must move, split, or be rebuilt across layers
- identify dependency cleanup targets and layer-balance problems
