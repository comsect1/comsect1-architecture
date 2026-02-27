# comsect1 AI Tooling Setup

This document is the shared packaging guide for AI-specific integrations in this
repository.

This guide is hybrid:

- manual prose explains the packaging model and project-local policy
- generated blocks below carry drift-sensitive commands, tool matrix data,
  and update rules

## Common Model

All AI packages in this repository follow the same structure:

- Shared operational entrypoint: `guides/00_AI_ENTRYPOINT.md`
- Canonical law: `specs/`
- Machine gate: `scripts/`
- Python tooling SSOT: `scripts/comsect1_ai_tooling.py`
- Root adapters stay thin
- Tool packages reference the cloned repo path and do not embed architecture
  rules

When adding or updating an AI package, change the common instruction body once
and keep tool-specific files focused on installation and invocation only.

<!-- BEGIN GENERATED: tooling-install.common-model -->
Generated AI tooling surfaces are synchronized by:

```text
python scripts/comsect1_ai_tooling.py sync-repo
```

Verify them with:

```text
python scripts/Verify-ToolingConsistency.py
```

The managed surface includes:

- root adapters such as `AGENTS.md` and `CLAUDE.md`
- tool-specific skills, reviewers, and rules files
- install/bootstrap wrapper scripts under `tooling/`
- tool-specific package docs under `tooling/<tool>/INSTALL.md`
- generated blocks inside this shared packaging guide
<!-- END GENERATED: tooling-install.common-model -->

## Tool Matrix

<!-- BEGIN GENERATED: tooling-install.tool-matrix -->
| Tool | Package doc | Installs | Project-local adapter |
|------|-------------|----------|-----------------------|
| Claude Code | `tooling/claude-code/INSTALL.md` | global rule + reviewer + analyze skill | optional thin `CLAUDE.md` |
| Codex | `tooling/codex/INSTALL.md` | analyze skill + review skill | required thin `AGENTS.md` via bootstrap |
<!-- END GENERATED: tooling-install.tool-matrix -->

## Update Policy

<!-- BEGIN GENERATED: tooling-install.update-policy -->
| What changed | Action needed |
|-------------|---------------|
| `specs/` | `git pull` only |
| `guides/00_AI_ENTRYPOINT.md` | `git pull` only |
| `scripts/` | `git pull` only |
| `scripts/comsect1_ai_tooling.py` or generated AI tooling surfaces | run `python scripts/comsect1_ai_tooling.py sync-repo` and `python scripts/Verify-ToolingConsistency.py` |
| `tooling/INSTALL.md` generated blocks | run `python scripts/comsect1_ai_tooling.py sync-repo` and `python scripts/Verify-ToolingConsistency.py` |
| `tooling/<tool>/` templates or install scripts | re-run that tool's install/bootstrap |
<!-- END GENERATED: tooling-install.update-policy -->

## Project Rule Policy

Downstream `CLAUDE.md` or `AGENTS.md` files should:

- point to the shared entrypoint first
- avoid restating canonical rules
- contain only project-local additions
