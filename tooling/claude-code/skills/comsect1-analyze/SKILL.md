---
name: comsect1-analyze
description: Analyze and design code according to comsect1 architecture. Use when starting refactoring or new design work on any codebase.
argument-hint: "[target-path or feature-name]"
disable-model-invocation: true
---

# comsect1 Architecture Analysis

You are performing an architectural analysis of the target codebase according to
the comsect1 architecture specification.

## Step 0: Read the Canonical Sources

Before doing anything, read the canonical source list defined in:
`{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_07_Analysis_Procedure.md`

All prefix definitions, layer roles, discriminator logic, and dependency rules
come from the canonical specs. Do NOT use hardcoded rules. Read the spec every
time.

## Target

Analyze: `$ARGUMENTS`

## Project context

Current files: !`git ls-files --others --cached --exclude-standard 2>/dev/null | head -80`

## Analysis procedure

Follow the canonical 8-step procedure defined in:
`{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_07_Analysis_Procedure.md`

Read that guide before starting the analysis. Perform each step in order and
report findings as you go.

## Report format

Read the canonical report format guide before generating the report:
`{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_06_Analysis_Report_Format.md`

Write the report to **`.comsect1-analysis.md`** at the target root AND display
in conversation. The guide defines the exact format. Do not improvise.
