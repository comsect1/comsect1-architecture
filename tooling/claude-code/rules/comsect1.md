# comsect1 Architecture — Global Rules

This user applies comsect1 architecture across all programming projects.
These rules are always active regardless of project context.

## Philosophical Stance

- **The Order** is the unreachable ideal. Architecture is continuous alignment toward it.
- **NEVER** claim architecture, specification, or any work is "complete" or "finished."
- comsect1 operates in the **asymptotic awareness** stance: knowing the direction, acknowledging the unbridgeable distance, persisting in the approach.
- Claiming completion is the **Delusion** stance — the second of three stances (Ignorance, Delusion, Asymptotic Awareness).
- Quality is judged by **continuity of alignment**, not static completion (Great Alignment).

## 3-Layer Feature Model

| Layer | Prefix | Role | Question |
|-------|--------|------|----------|
| **Idea** | `ida_` | Pure intent and domain decisions | WHAT/WHEN |
| **Praxis** | `prx_` | Domain interpretation coupled to external types | WHAT-in-HOW (inseparable) |
| **Poiesis** | `poi_` | Mechanical production / wrapping | HOW (no domain judgment) |

## 3-Question Discriminator (Mandatory)

1. External dependency required? No → `ida_`. Yes → Q2.
2. Separable domain judgment? Yes → split `ida_` + `poi_`. No → Q3.
3. Inseparable domain judgment coupled to external types? Yes → `prx_`. No → `poi_`.

## Dependency Direction (Invariant)

```
IDA → { own PRX, own POI }
PRX → { own POI, mdw_, svc_, hal_, cfg_, db_, stm_ }
POI → { mdw_, svc_, hal_, cfg_, db_, stm_ }
Feature ↔ Feature: stm_ only
Platform: HAL → BSP
```

- ida_ must NOT access cfg_/db_/stm_/mdw_/svc_/hal_/bsp_ directly (only cfg_core equivalent).
- prx_/poi_ must NOT reference another feature's ida_/prx_/poi_.

## Key OOP Adaptations (A2)

> These rules apply to OOP languages (C#, Java, etc.) only. For C/embedded, Idea remains stateless per specs/02_overview.md.

- **Idea constraints** (OOP) — two orthogonal axes, both mandatory:
  1. **Self-containment** (dependency): no external imports, no feature resources, no infra capability.
  2. **Purity** (behavioral): immutable + referentially transparent (OOP equivalent of C's stateless, §2.7.9).
  - Static utility class (form a, preferred default) OR value type with readonly fields (form b, OOP accommodation).
- **Praxis is optional** with high justification bar. ida_ ↔ poi_ via interface is often sufficient in OOP.
- **Interface-Owned Layer Boundaries**: upper layer owns interface, lower layer implements.
- **Shared Domain Utilities**: cfg_Core (contract vocabulary) / svc_ (shared computation) / feature-internal.
- `svc_` placement: `/infra/service/` only (A2.1 #11).
- No `inf_` role prefix: folder grouping does not change prefix semantics (A2.1 #12).

## Resource Prefixes

| Prefix | Meaning |
|--------|---------|
| `cfg_` | Compile-time configuration |
| `db_`  | Compile-time static data tables |
| `stm_` | Runtime datastreams (cross-feature data plane) |
| `svc_` | Shared domain service (capability plane) |
| `mdw_` | Middleware (capability plane) |
| `hal_` | Hardware Abstraction Layer |
| `bsp_` | Board Support Package |

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

## User Preferences

- Conversation language: Korean (match user)
- All artifacts (code, docs, commits): English only
- Preserve philosophical precision — do not flatten comsect1 concepts into shallow summaries
- Internalize corrections permanently — do not repeat previously corrected mistakes
