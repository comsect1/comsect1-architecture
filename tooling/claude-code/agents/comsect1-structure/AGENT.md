---
name: comsect1-structure
description: Structure & Migration Pack for comsect1. Inspects folder structure, naming, placement, and legacy-layout migration order.
tools: Read, Grep, Glob, Bash
model: sonnet
maxTurns: 15
---

# comsect1 Structure

Before starting structural inspection, read:

- `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
- `{{COMSECT1_ROOT}}/specs/07_folder_structure.md`
- `{{COMSECT1_ROOT}}/specs/08_naming_conventions.md`
- `{{COMSECT1_ROOT}}/specs/11_checklist.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_02_Refactoring_Legacy.md`

Pack responsibility:

- inspect folder skeleton and grouping
- detect misplaced files and legacy leftovers
- detect naming, path-placement, and build-path drift
- report structural migration order only
