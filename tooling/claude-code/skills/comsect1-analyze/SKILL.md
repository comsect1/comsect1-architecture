---
name: comsect1-analyze
description: Analyze and design code according to comsect1 architecture. Use when starting refactoring or new design work on any codebase.
argument-hint: "[target-path or feature-name]"
disable-model-invocation: true
---

# comsect1 Architecture Analysis

You are performing an architectural analysis of the target codebase according to the comsect1 architecture specification.

## Step 0: Read the Canonical Specification

**Location**: `{{COMSECT1_ROOT}}/specs/`

Before doing ANYTHING, read these files from the canonical spec:
- `02_overview.md` — 3-layer model, 3-question discriminator, SSOT (§2.7)
- `A2_oop_adaptation.md` — OOP prefix conventions, discriminator, ida_ purity (A2.5.1)
- `05_dependency_rules.md` — Dependency direction rules
- `07_folder_structure.md` — Canonical folder layout

All prefix definitions, layer roles, discriminator logic, and dependency rules
come from these files. Do NOT use hardcoded rules. Read the spec every time.

## Target

Analyze: `$ARGUMENTS`

## Project context

Current files: !`git ls-files --others --cached --exclude-standard 2>/dev/null | head -80`

## Analysis procedure

Perform each step in order. Report findings as you go.

### Step 1: Environment identification

- Identify programming language(s) and framework(s) from file extensions and project structure
- Identify build system (CMake, MSBuild, npm, etc.)
- Note whether this is embedded/firmware, desktop, web backend, or mobile
- **Determine architecture variant**:
  - C/embedded (`.c`/`.h` files) → apply standard spec rules (stateless Idea per §2.7.9)
  - OOP (`.cs`/`.vb`/`.java` files) → apply A2 appendix rules (read A2.5.1 for exact Idea constraints)
  - Mixed → note both variants and apply per-file

### Step 2: Existing comsect1 status

Scan for files with comsect1 prefixes (read `08_naming_conventions.md` for complete prefix list):
- Architecture layers: `ida_`, `prx_`, `poi_`
- Resources: `cfg_`, `db_`, `stm_`
- Capabilities: `svc_`, `mdw_`, `hal_`, `bsp_`
- Check for project-level CLAUDE.md with comsect1 rules
- Check for gate scripts:
  - Verify-Spec.py (specification consistency)
  - Verify-Comsect1Code.py (C/embedded code architecture)
  - Verify-OOPCode.py (OOP-specific architecture, per A2 appendix)
  - Verify-AIADGate.py (unified runner)

### Step 3: Layer classification

For each significant code unit (file/class/module) in the target scope, apply the
**3-Question Discriminator** from the spec (read `02_overview.md` for exact formulation):

1. External dependency required? No → ida_. Yes → Q2.
2. Separable domain judgment? Yes → split ida_ + poi_. No → Q3.
3. Inseparable domain judgment coupled to external types? Yes → prx_. No → poi_.

For OOP projects, also read `A2_oop_adaptation.md` for OOP-specific discriminator application (A2.4.2).

Produce a classification table:

| Current file/class | Proposed layer | Discriminator path | Rationale |
|---|---|---|---|

### Step 4: Shared domain utilities

Identify code that is reused across features (read A2.5.2 for classification):
- **Contract vocabulary** (trivial types/conversions) → belongs in `cfg_Core`
- **Shared domain computation** (substantial reusable logic) → belongs as `svc_` service
- **Feature-internal** → stays in the feature

### Step 5: Dependency analysis

Map current dependencies and check against `05_dependency_rules.md`.
Flag every violation with the specific spec section it violates.

### Step 6: Layer Balance Analysis

For each feature, perform a **mandatory balance check**:

1. **Read ida_ and poi_ (and prx_ if it exists) side by side**
2. **Count domain-semantic conditionals** in each layer:
   - Domain-semantic: `if/switch/case` based on business rules, policies, limits, states, modes
   - Technical: null checks, error return codes, resource availability — do NOT count these
3. **Produce a balance table**:

| Feature | ida_ decisions | poi_ decisions | prx_ decisions | Balance |
|---------|---------------|---------------|----------------|---------|
| motor | 3 (speed limit, torque check, mode select) | 0 | - | OK |
| sensor | 0 | 4 (threshold, filter, calibration, range) | - | VIOLATION |

4. **Apply the requirement test**: If a business requirement changes, which file would you modify?
   - If the answer is poi_ → domain logic is in the wrong layer
   - If the answer is ida_ → correct

Any feature with `ida_ decisions = 0` AND `poi_ decisions > 0` is a **VIOLATION**.

### Step 7: Design direction

Propose:
- Feature boundaries (what constitutes a "feature" in this project)
- Layer split for each feature (ida_ required, prx_ only if justified, poi_ for external wrapping)
- Interface boundaries (OOP: which interfaces should the feature own?)
- Dependency graph showing allowed flow

### Step 8: Gate execution

If gate scripts exist in the project, run them and report results.
If no gate scripts exist, note this and recommend the appropriate gate script:
- C/embedded projects → `Verify-Comsect1Code.py`
- OOP projects → `Verify-OOPCode.py`
- Spec-only projects → `Verify-Spec.py`
- All projects → `Verify-AIADGate.py` (unified runner, auto-detects applicable stages)

## Output format

End with a summary table:

| Feature | ida_ | prx_ (justified?) | poi_ | Resources | Violations |
|---|---|---|---|---|---|
