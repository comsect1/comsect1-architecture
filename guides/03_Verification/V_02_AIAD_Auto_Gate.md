# V_02 AIAD Auto Gate Verification

This guide defines the machine-verifiable gate for AI-assisted development (AIAD).

---

## 1. Purpose

Human checklist verification is necessary but not sufficient for scalable AIAD.
The auto gate provides:

- deterministic pass/fail result
- machine-readable evidence
- repeatable enforcement in CI and agent workflows

---

## 2. Gate Components

### 2.1 Spec Gate

Script:
- `scripts/Verify-Spec.py`

Checks:
- spec file naming/numbering consistency
- basic section hygiene and UTF-8 without BOM encoding checks

### 2.2 Code Architecture Gate

**C/embedded projects:**

Script:
- `scripts/Verify-Comsect1Code.py`

**OOP projects (C#, VB.NET, Java):**

Script:
- `scripts/Verify-OOPCode.py`

The unified runner (`Verify-AIADGate.py`) auto-detects the project type and activates the appropriate gate.

Checks (3-layer aware):
- dedicated `/comsect1` root boundary (Section 7.2 Root Folder Convention)
- unit identity anchors and unit-qualified naming consistency
- include/dependency direction
- IDA/PRX/POI role boundary rules
- module/platform reverse dependency violations
- semantic misplaced detection for platform-coupled code outside `/infra/platform/`
- repo-root build evidence scan (MCU/BSP branches, BSP include paths, BSP target links, dummy fallbacks)
- HAL/BSP mixed responsibility advisory
- infra-layout invariant (folder grouping does not relax dependency rules)
- unlisted role prefix detection (only §8.5 prefixes valid)

Conformance enforcement:
- All normative rules are enforced without relaxation profiles.
- Legacy folder layouts are detected and reported as errors.

### 2.3 Tooling Consistency Gate

Script:
- `scripts/Verify-ToolingConsistency.py`

Checks:
- generated AI tooling surfaces still match `scripts/comsect1_ai_tooling.py`
- generated blocks inside `tooling/INSTALL.md` still match `scripts/comsect1_ai_tooling.py`
- thin adapters, skills, and install/bootstrap wrappers have not drifted

Use this gate when changing:
- `AGENTS.md`, `CLAUDE.md`
- tool-specific skills, reviewers, and rules files
- install/bootstrap wrapper scripts under `tooling/`
- generated sections inside `tooling/INSTALL.md`

### 2.4 Unified Runner

Script:
- `scripts/Verify-AIADGate.py`

Behavior:
- runs spec gate, tooling consistency gate, and code/OOP gates as applicable
- aggregates stage status
- writes JSON report
- exits non-zero on failure

---

## 3. Usage

### 3.1 Full Gate

```powershell
python scripts/Verify-AIADGate.py -CodeRoot codes/comsect1 -ReportPath .aiad-gate-report.json
```

### 3.2 Spec + Tooling Only

```powershell
python scripts/Verify-AIADGate.py -SkipCode -ReportPath .aiad-gate-report.json
```

---

## 4. Report Contract (JSON)

Top-level fields:
- `generatedAtUtc`
- `repoRoot`
- `stages[]` (name/status/exitCode/note/outputPath)
- `gatePassed`

Code stage may additionally emit:
- `aiad-code-verify.json` with detailed findings.

---

## 5. Decision Rule

- `gatePassed = true` -> task can proceed
- `gatePassed = false` -> task is incomplete and must be fixed

---

## 6. Recommended Pipeline Order

1. Human post-task checklist (`V_01_Post_Task_Checklist.md`)
2. Auto gate (`Verify-AIADGate.py`)
3. Archive report with task artifacts

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.0**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

You are free to:
- **Share** - copy and redistribute the material in any medium or format for non-commercial purposes only.

Under the following terms:
- **Attribution** - You must give appropriate credit to the author (Kim Hyeongjeong), provide a reference to the license, and indicate if changes were made.
- **NonCommercial** - You may not use the material for commercial purposes.
- **NoDerivatives** - If you remix, transform, or build upon the material, you may not distribute the modified material.

No additional restrictions - You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*

