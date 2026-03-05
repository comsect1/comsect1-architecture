# comsect1 Architecture — Global Rules

This user applies comsect1 architecture across all programming projects.
These rules are always active regardless of project context.

## Canonical Specification (SSOT)

**Location**: `{{COMSECT1_ROOT}}/specs/`

Before writing, reviewing, or refactoring any comsect1 code, you MUST read the
relevant canonical specification files. Do NOT rely on summaries, memory, or
rules in this file — the canonical spec is the single source of truth.

### Spec index (read as needed)

| File | Covers |
|------|--------|
| `01_philosophy.md` | The Order, asymptotic awareness, philosophical stance |
| `02_overview.md` | 3-layer model, 3-question discriminator, SSOT (§2.7) |
| `04_layer_roles.md` | ida_/prx_/poi_ role constraints |
| `05_dependency_rules.md` | Dependency direction invariant, access rules |
| `07_folder_structure.md` | Canonical folder layout and placement |
| `08_naming_conventions.md` | Prefix definitions (cfg_/db_/stm_/svc_/mdw_/hal_/bsp_) |
| `10_anti_patterns.md` | Common violations and why they're harmful |
| `11_checklist.md` | Post-task verification checklist |
| `A2_oop_adaptation.md` | OOP layer mapping, discriminator, ida_ purity (A2.5.1) |

This file does NOT restate, summarize, or interpret the canonical spec.
If something is defined in the canonical spec, read the spec — do not look here.

## AIAD Gate

- Architecture verification gate is the acceptance criterion for any output.
- A task that fails the gate is not complete.
- Gate scripts are project-specific; check each project's CLAUDE.md for commands.

### Gate Scripts

| Script | Scope |
|--------|-------|
| `Verify-Spec.py` | Specification hygiene, cross-references, SSOT terms |
| `Verify-Comsect1Code.py` | C/embedded code architecture + Red Flag heuristics |
| `Verify-OOPCode.py` | OOP code architecture (A2 rules) + Red Flag heuristics |
| `Verify-AIADGate.py` | Unified runner (all stages + Stage 0 meta-advisory) |

- **Stage 0 (meta-advisory)**: Detects spec file modifications and reminds about upstream alignment.
- **Red Flag heuristics**: Empty Idea, Fat Praxis, Fat Poiesis — advisory warnings, not blocking errors.

## Pre-Generation Discriminator (Mandatory)

Before writing or refactoring ANY ida_/prx_/poi_ code, you MUST:

1. **Explicitly answer the 3-question discriminator** for each code unit.
   Document your answers — do not apply the discriminator silently.

2. **Produce a layer assignment** before generating code:
   ```
   Feature: [name]
   Q1 (external dep?): [Yes/No] → [result]
   Q2 (separable judgment?): [Yes/No] → [split ida_ + poi_ / go Q3]
   Q3 (inseparable coupling?): [Yes/No] → [prx_ / poi_]
   ```

3. **Verify layer balance BEFORE submitting**:
   - ida_ MUST contain domain decisions (conditionals with business meaning).
     A one-line forwarding call is NOT a domain decision.
   - poi_ MUST NOT contain domain-semantic conditionals.
     If poi_ has `if/switch/case` based on business rules, those belong in ida_.
   - If a requirement change would only touch poi_ (not ida_), the domain
     decision is in the wrong layer.

**The test:** Can you read ida_ alone and understand WHAT the feature decides
and WHEN it acts? If ida_ reads as a forwarding table, it is empty.

## Layer Balance Invariant

For each feature, compare the "decision weight" across layers:

| Check | Condition | Verdict |
|-------|-----------|---------|
| ida_ has zero conditionals | poi_ or prx_ has conditionals with business meaning | **VIOLATION: Empty Idea + Fat Poiesis** |
| ida_ only delegates | All domain logic resides in prx_/poi_ | **VIOLATION: Inverted layers** |
| ida_ has domain decisions | poi_ is pure wrapping/forwarding | **Correct** |

This is NOT advisory. This is a structural invariant equal in severity to
dependency direction violations. Treat it as an error.

## Rule Application Meta-Principle

- When applying any rule, first ask: **"Why does this rule exist?"**
- Process: Load rule → Identify rule's PURPOSE → Judge current situation against that purpose → Conclude
- Never pattern-match rule TEXT against surface characteristics
- Distinguish implementation detail (how) from essence (what)
- Example: `db_` = "compile-time static data" — the essential discriminator is "static" (immutable), not "compile-time" (source)
- Automated gates verify structural compliance; classification JUDGMENT requires architectural reasoning about intent

## Agent Output Verification

- Agent (subagent) reports are for **navigation and discovery only**
- Any factual claim from an agent ("file X contains Y") → **verify with direct `Read` before using in analysis or conclusions**
- Agents can mix content across multiple sources when synthesizing reports — **source attribution is not trustworthy**
- File listing, directory structure, and pattern search results are relatively reliable
- **Never derive conclusions from agent reports without primary source verification**

## Project-Specific Working Rules

<!-- Add project-specific rules below this line.                    -->
<!-- These rules should NOT restate canonical spec content.         -->
<!-- Example entries:                                               -->
<!--   - No new direct access to mutable globals from Form_*.      -->
<!--   - New state mutation must go through IColorStateStore.       -->
<!--   - Host adapters (Form_*.vb) live outside the comsect1/ boundary. -->

## User Preferences

- Conversation language: Korean (match user)
- All artifacts (code, docs, commits): English only
- Preserve philosophical precision — do not flatten comsect1 concepts into shallow summaries
- Internalize corrections permanently — do not repeat previously corrected mistakes
