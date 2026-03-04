---
name: comsect1-analyze
description: Analyze and design code according to comsect1 architecture. Use when starting refactoring or new design work on any codebase.
argument-hint: "[target-path or feature-name]"
disable-model-invocation: true
---

# comsect1 Architecture Analysis

You are performing an architectural analysis of the target codebase according to the comsect1 architecture specification.

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
  - C/embedded (`.c`/`.h` files) → apply standard spec rules (stateless Idea)
  - OOP (`.cs`/`.vb`/`.java` files) → apply A2 appendix rules (immutable + referentially transparent Idea)
  - Mixed → note both variants and apply per-file

### Step 2: Existing comsect1 status

Scan for files with comsect1 prefixes:
- Architecture layers: `ida_`, `prx_`, `poi_`
- Resources: `cfg_`, `db_`, `stm_`
- Capabilities: `svc_`, `mdw_`, `hal_`, `bsp_`
- Check for project-level CLAUDE.md with comsect1 rules
- Check for gate scripts:
  - Verify-Spec.py (specification consistency)
  - Verify-Comsect1Code.py (C/embedded code architecture)
  - Verify-OOPCode.py (OOP-specific architecture, per A2 appendix — only for OOP projects)
  - Verify-AIADGate.py (unified runner)

### Step 3: Layer classification

For each significant code unit (file/class/module) in the target scope, apply the **3-Question Discriminator**:

1. Does this code require external dependency context? No → **ida_**. Yes → Q2.
2. Is there separable domain judgment without external types? Yes → split **ida_** + **poi_**. No → Q3.
3. Is there inseparable domain judgment coupled to external types? Yes → **prx_**. No → **poi_**.

**OOP-specific considerations** (if detected in Step 1):
- Idea constraints = two orthogonal axes (A2.5.1):
  - Self-containment (dependency): no external imports, no feature resources, no infra capability
  - Purity (behavioral): immutable + referentially transparent (OOP equivalent of C's stateless, §2.7.9)
- Prefer static utility class (form a) as default; value type with readonly fields (form b) only when decision context must be carried
- Praxis is optional with high justification bar; ida_ <-> poi_ via interface is often sufficient
- Upper layer owns interface, lower layer implements (Interface-Owned Layer Boundaries)
- svc_ placement: /infra/service/ only (A2.1 #11)
- See A2_oop_adaptation.md for detailed rules

Produce a classification table:

| Current file/class | Proposed layer | Discriminator path | Rationale |
|---|---|---|---|

### Step 4: Shared domain utilities

Identify code that is reused across features:
- **Contract vocabulary** (trivial types/conversions) → belongs in `cfg_Core`
- **Shared domain computation** (substantial reusable logic) → belongs as `svc_` service
- **Feature-internal** → stays in the feature

### Step 5: Dependency analysis

Map current dependencies and identify violations:
- ida_ accessing external APIs/frameworks → violation
- prx_/poi_ referencing another feature's ida_/prx_/poi_ → violation
- Cross-feature communication not through stm_ → violation

### Step 6: Design direction

Propose:
- Feature boundaries (what constitutes a "feature" in this project)
- Layer split for each feature (ida_ required, prx_ only if justified, poi_ for external wrapping)
- Interface boundaries (OOP: which interfaces should the feature own?)
- Dependency graph showing allowed flow

### Step 7: Gate execution

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
