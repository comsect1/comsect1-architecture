---
name: comsect1-director
description: Director Pack for comsect1. Use when coordinating pack-level maintenance or refactoring work.
argument-hint: "[target-path or task]"
disable-model-invocation: true
---

# comsect1 Director

Before coordinating any multi-step comsect1 task, read:

- `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
- `{{COMSECT1_ROOT}}/guides/00_Process_Overview.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
- `{{COMSECT1_ROOT}}/guides/03_Verification/V_01_Post_Task_Checklist.md`
- `{{COMSECT1_ROOT}}/guides/03_Verification/V_02_AIAD_Auto_Gate.md`

Pack responsibility:

- classify the task and repository mode
- choose the required packs
- order them as structure -> layer -> risk -> execution -> verification
- consolidate outputs into one plan and one final result

Keep the provider surface thin. Do not restate canonical rules here.
