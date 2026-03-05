# comsect1 Global Rules — Claude Code Configuration

> comsect1 is tool-agnostic. This directory contains the Claude Code-specific
> materialization of comsect1 architecture rules for AI-assisted development.

Setup guide for configuring comsect1 architecture rules on a new PC with Claude Code.

## Prerequisites

- Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code` or equivalent)
- Git available in PATH

## Directory Structure

Claude Code reads global configuration from `~/.claude/`. The install script
copies template files and substitutes `{{COMSECT1_ROOT}}` with your clone path.

```
~/.claude/
  rules/
    comsect1.md          # Global architecture rules (always loaded)
  agents/
    comsect1-reviewer/
      AGENT.md            # Architecture compliance reviewer agent
  skills/
    comsect1-analyze/
      SKILL.md            # Architecture analysis skill (/comsect1-analyze)
```

### Platform paths

| OS | `~/.claude/` resolves to |
|----|--------------------------|
| Windows | `%USERPROFILE%\.claude\` (e.g. `C:\Users\<name>\.claude\`) |
| macOS | `~/.claude/` |
| Linux | `~/.claude/` |

## Installation

### Automated (recommended)

```bash
# Clone the architecture repository
git clone <comsect1-architecture-repo>
cd comsect1-architecture

# Bash / Git Bash on Windows / macOS / Linux
bash tooling/claude-code/install.sh
```

PowerShell (Windows):

```powershell
powershell -ExecutionPolicy Bypass -File tooling\claude-code\install.ps1
```

The script:
1. Detects the repo root automatically
2. Replaces `{{COMSECT1_ROOT}}` with the absolute path to your clone
3. Copies files to `~/.claude/` (existing files are backed up as `.bak`)

### Manual

```bash
mkdir -p ~/.claude/rules
mkdir -p ~/.claude/agents/comsect1-reviewer
mkdir -p ~/.claude/skills/comsect1-analyze

SRC="<your-clone-path>/tooling/claude-code"

# Copy and substitute {{COMSECT1_ROOT}} with your clone path
for f in rules/comsect1.md agents/comsect1-reviewer/AGENT.md skills/comsect1-analyze/SKILL.md; do
  sed "s|{{COMSECT1_ROOT}}|<your-clone-path>|g" "$SRC/$f" > ~/.claude/$f
done
```

### Verify

Launch Claude Code in any project and check:

1. **Global rules loaded** — comsect1.md appears in system context automatically
2. **Reviewer agent available** — `comsect1-reviewer` appears as a subagent type
3. **Analyze skill available** — `/comsect1-analyze` is listed as an invocable skill

## Design Principle: Reference, Not Embed

All installed files **reference** the cloned repo path via `{{COMSECT1_ROOT}}` —
they contain no embedded architecture rules. When the spec is updated:

- `git pull` updates the canonical spec files
- Installed rules, agent, and skill read the spec at runtime
- **No reinstall needed** for spec content changes

Reinstall is only needed when the template files themselves change
(new checks, new procedure steps, structural changes to the config files).

## File Descriptions

### rules/comsect1.md

Global architecture rules loaded into every Claude Code session. Contains:

- Canonical spec SSOT pointer with file index
- AIAD Gate script references
- Rule Application Meta-Principle (how to reason about rules)
- Agent Output Verification (subagent report reliability rules)
- Project-specific working rules section (user-customizable)
- User preferences (conversation language, artifact language)

### agents/comsect1-reviewer/AGENT.md

Specialized subagent for architecture compliance review. Read-only — reports
violations without modifying files. Reads the canonical spec at runtime and checks:

- Idea layer purity
- Reverse dependency violations
- Cross-feature isolation
- Platform and resource boundary compliance
- Praxis justification (advisory)
- Red Flag heuristics (Empty Idea, Fat Praxis, Fat Poiesis)
- OOP-specific checks (A2 rules)
- svc_ placement invariant

### skills/comsect1-analyze/SKILL.md

User-invocable skill (`/comsect1-analyze [target]`) for architectural analysis.
Reads the canonical spec at runtime and performs:

1. Environment identification (language, framework, architecture variant)
2. Existing comsect1 status scan
3. Layer classification via 3-Question Discriminator
4. Shared domain utility identification
5. Dependency analysis and violation detection
6. Design direction proposal
7. Gate script execution

## Per-Project Configuration

Global rules apply to all projects. For project-specific settings:

- **CLAUDE.md** — Place in project root for project-specific instructions, gate commands, and file layout
- **Project memory** — Stored at `~/.claude/projects/<project-path-hash>/memory/MEMORY.md`, created automatically

### Gate scripts

Gate scripts live in this repository under `scripts/`. Each project's CLAUDE.md should reference the appropriate gate:

```markdown
## Gate Command
python Verify-OOPCode.py -Root comsect1/    # OOP projects
python Verify-Comsect1Code.py               # C/embedded projects
python Verify-AIADGate.py                   # Unified runner
```

## Updating

| What changed | Action needed |
|-------------|---------------|
| Spec content (`specs/`) | `git pull` only — installed files read spec at runtime |
| Template files (`tooling/claude-code/`) | `git pull` then re-run install script |
| Gate scripts (`scripts/`) | `git pull` only — scripts run from repo directly |

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Rules not loaded | File not at correct path | Verify `~/.claude/rules/comsect1.md` exists |
| Agent not available | AGENT.md missing or malformed | Check frontmatter YAML in AGENT.md |
| Skill not listed | SKILL.md missing or malformed | Check frontmatter YAML in SKILL.md |
| Spec not found at runtime | `{{COMSECT1_ROOT}}` not substituted | Re-run install script |
| Korean conversation but English artifacts | Working as intended | User preference in comsect1.md |
