---
name: comsect1-refactor
description: Single comsect1 entry point. Use for analysis, refactoring, or maintenance under the canonical pack taxonomy.
argument-hint: "[target-path or task]"
disable-model-invocation: true
---

# comsect1 Refactor

Before doing anything, read:

- `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
- `{{COMSECT1_ROOT}}/guides/00_Process_Overview.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_07_Analysis_Procedure.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_06_Analysis_Report_Format.md`
- `{{COMSECT1_ROOT}}/guides/03_Verification/V_01_Post_Task_Checklist.md`
- `{{COMSECT1_ROOT}}/guides/03_Verification/V_02_AIAD_Auto_Gate.md`

## Target

Analyze / refactor: `$ARGUMENTS`

## Project context

Current branch: !`git branch --show-current 2>/dev/null`
Recent commits: !`git log --oneline -5 2>/dev/null`
Current files: !`git ls-files --others --cached --exclude-standard 2>/dev/null | head -80`

## Procedure

This is the single entry point for all comsect1 work.

Start with the analysis phase using the canonical 8-step procedure from
`EG_07`. Do not skip analysis. Write the analysis report to
**`.comsect1-analysis-report.md`** at the target root (format defined in
`EG_06`).

Then follow the canonical pack order:

1. Director — classify task, choose required packs, order them
2. Structure & Migration
3. Layer & Dependency
4. Risk & Exception
5. Execution — apply the approved plan, preserve discriminator records
6. Verification & Governance

Produce one coherent end-to-end result and do not redefine pack meanings.

## Gate execution

After the Verification pack completes, run the bundled gate script:

```bash
bash scripts/run-gates.sh [code-root-if-applicable]
```

This executes `Verify-AIADGate.py` (spec + tooling + code gates) and
writes `.aiad-gate-report.json`. If the gate fails, fix findings before
reporting the task as complete.
