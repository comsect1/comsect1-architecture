# comsect1 Claude Code Package

This package is the Claude Code adapter for the shared comsect1 AI entrypoint.

See [`../INSTALL.md`](../INSTALL.md) for the common packaging model and update
policy.

Generated surface:
- synchronized by `python scripts/comsect1_ai_tooling.py sync-repo`
- verified by `python scripts/Verify-ToolingConsistency.py`

## Installs

```text
~/.claude/
  rules/comsect1.md
  agents/comsect1-reviewer/AGENT.md
  skills/comsect1-analyze/SKILL.md
```

## Install

```bash
git clone <comsect1-architecture-repo>
cd comsect1-architecture
bash tooling/claude-code/install.sh
```

PowerShell (Windows):

```powershell
powershell -ExecutionPolicy Bypass -File tooling\claude-code\install.ps1
```

The shell and PowerShell wrappers are thin entrypoints over:

```text
python scripts/comsect1_ai_tooling.py install --tool claude-code
```

## Verify

In Claude Code, confirm:

1. `comsect1.md` is loaded
2. `comsect1-reviewer` is available
3. `/comsect1-analyze` is available

## Project-local Rule

If a downstream project also uses `CLAUDE.md`, keep it thin:

- point to `guides/00_AI_ENTRYPOINT.md`
- add only project-local notes
- do not restate canonical rules
