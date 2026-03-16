---
name: comsect1-refactor
description: Primary one-command comsect1 refactoring surface. Use for end-to-end maintenance or refactoring under the canonical pack taxonomy.
argument-hint: "[target-path or task]"
disable-model-invocation: true
---

# comsect1 Refactor

Before doing anything, read:

- `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
- `{{COMSECT1_ROOT}}/guides/00_Process_Overview.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_07_Analysis_Procedure.md`
- `{{COMSECT1_ROOT}}/guides/03_Verification/V_01_Post_Task_Checklist.md`
- `{{COMSECT1_ROOT}}/guides/03_Verification/V_02_AIAD_Auto_Gate.md`

This is the preferred one-command entry for end-to-end comsect1 work.

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

`analyze` is the standalone analysis-only surface. `refactor` already
includes analysis internally.

Produce one coherent end-to-end result and do not redefine pack meanings.
