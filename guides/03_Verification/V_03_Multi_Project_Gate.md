# V-03: Multi-Project Gate Adaptation

> **Purpose**: Guide configuration of comsect1 gate scripts across different project types and explain how AIAD infrastructure (global Rules + project CLAUDE.md) interact when multiple projects coexist.

---

## 1. Project Type Detection

comsect1 supports three project archetypes. The gate infrastructure adapts based on which files are present.

| Archetype | Source Files | Primary Gate | Spec Gate |
|-----------|-------------|--------------|-----------|
| C/embedded | `.c`, `.h` | Verify-Comsect1Code.py | Verify-Spec.py (if spec repo) |
| OOP | `.cs`, `.vb`, `.java` | Verify-OOPCode.py | Verify-Spec.py (if spec repo) |
| Mixed | Both C and OOP files | Both code + OOP gates | Verify-Spec.py (if spec repo) |
| Spec-only | No source; only `specs/*.md` | None | Verify-Spec.py |

The unified runner `Verify-AIADGate.py` auto-detects the project type and activates the appropriate stages.

---

## 2. Gate Script Configuration

### 2.1 Spec-Only Project (e.g., comsect1-architecture repo)

```bash
# Spec verification only (code/OOP stages auto-skip)
python scripts/Verify-AIADGate.py
```

No `-CodeRoot` or `-OOPRoot` needed. The gate detects no `codes/comsect1` directory and skips code stages.

### 2.2 C/Embedded Project

```bash
# Typical invocation
python scripts/Verify-AIADGate.py -CodeRoot codes/comsect1

# Skip spec if this project has no specs/ directory
python scripts/Verify-AIADGate.py -CodeRoot codes/comsect1 -SkipSpec
```

### 2.3 OOP Project

```bash
# OOP root auto-detected from CodeRoot
python scripts/Verify-AIADGate.py -CodeRoot src/

# Or specify OOP root explicitly
python scripts/Verify-AIADGate.py -OOPRoot src/ -SkipCode
```

### 2.4 Mixed Project

```bash
# Both C and OOP code exist under the same tree
python scripts/Verify-AIADGate.py -CodeRoot codes/comsect1

# Or separate roots
python scripts/Verify-AIADGate.py -CodeRoot codes/comsect1/embedded -OOPRoot codes/comsect1/dotnet
```

### 2.5 Flags Summary

| Flag | Effect |
|------|--------|
| `-RepoRoot <path>` | Override repository root (default: parent of scripts/) |
| `-CodeRoot <path>` | Root directory for C/embedded code verification |
| `-OOPRoot <path>` | Root directory for OOP code verification (falls back to CodeRoot) |
| `-ReportPath <path>` | JSON report output path (default: `.aiad-gate-report.json`) |
| `-SkipSpec` | Skip specification verification stage |
| `-SkipCode` | Skip C/embedded code architecture stage |
| `-SkipOOP` | Skip OOP architecture verification stage |

---

## 3. Project CLAUDE.md Templates

Each project should have a `CLAUDE.md` at its root. Below are minimal templates per project type.

### 3.1 C/Embedded Project CLAUDE.md

```markdown
# Project Guidelines for Claude

## comsect1 Architecture

This project follows the comsect1 architecture specification.

- Spec reference: [comsect1-architecture repo path or URL]
- Architecture variant: C/embedded
- Idea layer purity: stateless (no mutable static state in ida_)

## Gate Commands

\```bash
python scripts/Verify-Comsect1Code.py -Root codes/comsect1
python scripts/Verify-AIADGate.py -CodeRoot codes/comsect1
\```

## Project-Specific Rules

[Add project-specific constraints here]
```

### 3.2 OOP Project CLAUDE.md

```markdown
# Project Guidelines for Claude

## comsect1 Architecture

This project follows the comsect1 architecture specification with OOP adaptation (Appendix A2).

- Spec reference: [comsect1-architecture repo path or URL]
- Architecture variant: OOP (C#)
- Idea layer purity: immutable + referentially transparent
- Praxis: optional, high justification bar

## Gate Commands

\```bash
python scripts/Verify-OOPCode.py -Root src/
python scripts/Verify-AIADGate.py -OOPRoot src/ -SkipCode
\```

## Project-Specific Rules

[Add project-specific constraints here]
```

### 3.3 Mixed Project CLAUDE.md

```markdown
# Project Guidelines for Claude

## comsect1 Architecture

This project contains both C/embedded and OOP components.

- Architecture variant: Mixed
- C/embedded root: codes/comsect1/embedded/
- OOP root: codes/comsect1/dotnet/

## Gate Commands

\```bash
python scripts/Verify-AIADGate.py -CodeRoot codes/comsect1/embedded -OOPRoot codes/comsect1/dotnet
\```
```

---

## 4. AIAD Infrastructure Layering

When Claude Code operates across multiple projects, the AIAD infrastructure layers as follows:

```
Global Rules (~/.claude/rules/)
    |
    +--> comsect1.md rules (apply to all comsect1 projects)
    |
Project CLAUDE.md (per-project)
    |
    +--> Project-specific overrides and gate configuration
    |
Session context
    |
    +--> /comsect1-analyze Skill → architectural analysis
    +--> comsect1-reviewer Agent → compliance review
    +--> PostToolUse Hook → gate reminder after edits
```

### Precedence

1. **Global Rules** set the baseline comsect1 constraints (dependency rules, naming, 3-Question Discriminator).
2. **Project CLAUDE.md** can add project-specific constraints but cannot relax global rules.
3. **Session tools** (Skill, Agent) reference both layers and adapt behavior based on detected project type.

### Cross-Project Considerations

- Gate scripts live in the spec repo (`comsect1-architecture/scripts/`), not in each project.
- Projects reference gate scripts by path: `python <spec-repo>/scripts/Verify-AIADGate.py -CodeRoot <project-root>`
- If a project copies gate scripts locally, it must keep them in sync with the spec repo version.
- The PostToolUse hook fires based on file patterns in the current working directory — it adapts per project.

---

## 5. Adding Gate Scripts to a New Project

1. Ensure the comsect1-architecture spec repo is accessible from the project.
2. Create a `CLAUDE.md` using the appropriate template above.
3. Run the unified gate once to generate the initial report:
   ```bash
   python <spec-repo>/scripts/Verify-AIADGate.py -CodeRoot <your-code-root>
   ```
4. If the gate finds violations, resolve them before starting new work.
5. Configure the PostToolUse hook (if not already global) to remind about gate runs after code edits.

---

## 6. CI/CD Integration

For projects with continuous integration:

```yaml
# Example GitHub Actions step
- name: comsect1 Architecture Gate
  run: |
    python scripts/Verify-AIADGate.py \
      -CodeRoot src/ \
      -ReportPath .aiad-gate-report.json
  env:
    PYTHONIOENCODING: utf-8
```

The gate returns exit code 0 on pass, 2 on failure. Use this in CI pipelines to block merges with architecture violations.

The JSON report at `-ReportPath` can be archived as a build artifact for traceability.

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.0**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
