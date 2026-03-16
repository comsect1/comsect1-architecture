---
name: comsect1-execute
description: Execution Pack for comsect1. Use when applying an approved refactoring or maintenance plan.
argument-hint: "[approved-plan or target-path]"
disable-model-invocation: true
---

# comsect1 Execute

Before write-enabled execution, read:

- `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
- `{{COMSECT1_ROOT}}/guides/00_Process_Overview.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
- the pack outputs that defined the approved plan

Pack responsibility:

- apply the approved plan
- preserve discriminator records and boundary reasoning
- do not invent new policy here
- hand work back to verification after implementation
