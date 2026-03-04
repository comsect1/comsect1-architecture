# comsect1 Global Rules — Claude Code Configuration

> comsect1 is tool-agnostic. This directory contains the Claude Code-specific
> materialization of comsect1 architecture rules for AI-assisted development.

Setup guide for configuring comsect1 architecture rules on a new PC with Claude Code.

## Prerequisites

- Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code` or equivalent)
- Git available in PATH

## Directory Structure

Claude Code reads global configuration from `~/.claude/`. Copy the following files:

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

### Step 1: Clone the architecture repository

```bash
git clone <comsect1-architecture-repo> /tmp/comsect1-arch
```

### Step 2: Create directories and copy files

```bash
mkdir -p ~/.claude/rules
mkdir -p ~/.claude/agents/comsect1-reviewer
mkdir -p ~/.claude/skills/comsect1-analyze

SRC="/tmp/comsect1-arch/tooling/claude-code"

cp "$SRC/rules/comsect1.md"                   ~/.claude/rules/
cp "$SRC/agents/comsect1-reviewer/AGENT.md"    ~/.claude/agents/comsect1-reviewer/
cp "$SRC/skills/comsect1-analyze/SKILL.md"     ~/.claude/skills/comsect1-analyze/
```

### Step 3: Verify

Launch Claude Code in any project and check:

1. **Global rules loaded** — comsect1.md appears in system context automatically
2. **Reviewer agent available** — `comsect1-reviewer` appears as a subagent type in Task tool
3. **Analyze skill available** — `/comsect1-analyze` is listed as an invocable skill

## File Descriptions

### rules/comsect1.md

Global architecture rules loaded into every Claude Code session. Contains:

- Philosophical stance (asymptotic awareness)
- 3-Layer Feature Model (ida_ / prx_ / poi_)
- 3-Question Discriminator
- Dependency direction invariant
- OOP Adaptations (A2)
- Resource prefix definitions (cfg_ / db_ / stm_ / svc_ / mdw_ / hal_ / bsp_)
- AIAD Gate script references
- Rule Application Meta-Principle
- Agent Output Verification (subagent report reliability rules)
- User preferences (conversation language, artifact language)

### agents/comsect1-reviewer/AGENT.md

Specialized subagent for architecture compliance review. Read-only — reports violations without modifying files. Checks:

- Idea layer purity (self-containment + behavioral purity)
- Reverse dependency violations
- Cross-feature isolation
- Platform and resource boundary compliance
- Praxis justification (advisory)
- Red Flag heuristics (Empty Idea, Fat Praxis, Fat Poiesis)
- OOP-specific checks (A2 rules)
- svc_ placement invariant

### skills/comsect1-analyze/SKILL.md

User-invocable skill (`/comsect1-analyze [target]`) for architectural analysis of a codebase. Performs:

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

## Updating Rules

When global rules change:

1. Update the source files in this repository (`tooling/claude-code/`)
2. Push to remote
3. On each target machine: `git pull` and re-copy files to `~/.claude/`

Rules take effect on the next Claude Code session.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Rules not loaded | File not at correct path | Verify `~/.claude/rules/comsect1.md` exists |
| Agent not available | AGENT.md missing or malformed | Check frontmatter YAML in AGENT.md |
| Skill not listed | SKILL.md missing or malformed | Check frontmatter YAML in SKILL.md |
| Korean conversation but English artifacts | Working as intended | User preference in comsect1.md |
