---
name: comsect1-refactor
description: Primary one-command comsect1 refactoring surface. Use when you want end-to-end automatic refactoring or maintenance flow under the canonical pack taxonomy.
---

# comsect1 Refactor

## Step 0: Load the Canonical Sources

Before doing anything, read:

- `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
- `{{COMSECT1_ROOT}}/guides/00_Process_Overview.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_07_Analysis_Procedure.md`
- `{{COMSECT1_ROOT}}/guides/03_Verification/V_01_Post_Task_Checklist.md`
- `{{COMSECT1_ROOT}}/guides/03_Verification/V_02_AIAD_Auto_Gate.md`

## Command Contract

This is the primary one-command entry for end-to-end comsect1 work.

Start with an internal analysis phase using the canonical analysis
procedure from `EG_07`. Do not skip analysis.

Internally follow the canonical pack order:

0. Analysis pre-phase
1. Director
2. Structure & Migration
3. Layer & Dependency
4. Risk & Exception
5. Execution
6. Verification & Governance

## Required Behavior

- classify the task and repository mode
- perform analysis before implementation decisions
- inspect structure before semantic rebuilding
- apply the discriminator before layer-changing edits
- perform code or spec changes when needed
- run the relevant verification checklist and gate
- treat failed verification as incomplete work

## Constraints

- Keep pack meanings aligned with the canonical taxonomy.
- Treat `analyze` as the standalone analysis-only surface; `refactor` already includes analysis internally.
- Do not treat helper surfaces such as analyze/review as replacements for the full pack sequence.
- Produce one coherent end-to-end result, not disconnected pack notes.
