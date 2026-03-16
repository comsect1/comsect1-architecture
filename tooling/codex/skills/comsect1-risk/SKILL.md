---
name: comsect1-risk
description: Risk & Exception Pack for comsect1. Use when scanning for anti-patterns, unreasonable logic placement, and recurring exception hazards.
---

# comsect1 Risk

## Step 0: Load the Canonical Sources

Before scanning for risks and exceptions, read:

- `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
- `{{COMSECT1_ROOT}}/specs/10_anti_patterns.md`
- `{{COMSECT1_ROOT}}/specs/11_checklist.md`
- `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_05_Application_Feedback.md`
- `{{COMSECT1_ROOT}}/guides/04_Meta_Evaluation/ME_01_Upstream_Alignment.md`
- `{{COMSECT1_ROOT}}/specs/A2_oop_adaptation.md` for OOP projects

## Pack Responsibility

Focus only on recurring design hazards and escalation signals.

- identify known anti-patterns
- flag unreasonable logic placement, suspicious abstractions, and exception creep
- distinguish blocking issues from advisory findings
- note when a recurring pattern should enter the feedback loop instead of being treated as a one-off mistake
