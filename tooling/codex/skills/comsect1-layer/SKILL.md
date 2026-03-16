---
name: comsect1-layer
description: Layer & Dependency Pack for comsect1. Use when applying the discriminator, correcting ida_/prx_/poi_ placement, and cleaning dependency direction.
---

# comsect1 Layer

## Step 0: Load the Canonical Sources

Before starting layer and dependency work, read:

- `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
- `{{COMSECT1_ROOT}}/specs/02_overview.md`
- `{{COMSECT1_ROOT}}/specs/04_layer_roles.md`
- `{{COMSECT1_ROOT}}/specs/05_dependency_rules.md`
- `{{COMSECT1_ROOT}}/guides/01_Design_Principles/DP_03_Praxis_Justification.md`
- `{{COMSECT1_ROOT}}/specs/A2_oop_adaptation.md` for OOP projects

## Pack Responsibility

Focus only on semantic layer placement and dependency cleanup.

- apply the 3-question discriminator
- record discriminator results before modifying code
- identify logic that must move, split, or be rebuilt across ida_/prx_/poi_
- identify dependency cleanup targets, reverse dependencies, and layer-balance problems
