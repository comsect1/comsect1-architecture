# EG-07: Analysis Procedure

This guide defines the canonical analysis procedure for the comsect1
architecture analysis. All AI tools that perform architecture analysis MUST
follow this procedure regardless of the tool or platform used.

For the report format, see **EG-06: Analysis Report Format**.

---

## Two-phase model

The analysis proceeds in two phases gated by the gate script result.

**Phase 1 — Structural gate** (always runs): lightweight, deterministic.
**Phase 2 — Qualitative analysis** (runs only when Phase 1 passes): full
layer classification, dependency interpretation, design direction.

```
Phase 1: env identification → gate execution
              ↓
       gate has ERRORS?
       YES → report violations + spec context → STOP (fix first)
       NO  →
              ↓
Phase 2: layer classification → shared utilities → dependency analysis
         → layer balance → design direction → full report
```

**Rationale**: Qualitative analysis on structurally broken code produces
unreliable conclusions. The gate enforces objective invariants. When gate
passes, the structural foundation is sound — qualitative analysis then adds
genuine interpretive value.

When gate passes with only warnings (advisory `red-flag-*`): proceed to
Phase 2. Warnings are informational, not blockers.

---

## Spec section lookup (Phase 1 use)

When the gate reports errors, read only the spec section(s) needed to explain
each violation. Do not read unrelated sections.

| Gate rule prefix | Spec section to read |
|------------------|----------------------|
| `layout.*`, `layout.api-misplaced`, `layout.examples_misplaced` | `specs/07_folder_structure.md` |
| `include.*`, `ida.include`, `prx.include`, `poi.include`, `*_core.include` | `specs/05_dependency_rules.md` |
| `path.*` | `specs/07_folder_structure.md` + `specs/08_naming_conventions.md` |
| `layer-balance` | `specs/04_layer_roles.md` |
| `service.*` | `specs/04_layer_roles.md` + `specs/02_overview.md` |
| `red-flag-*` | `specs/11_checklist.md` (advisory, proceed to Phase 2) |
| `naming.*` | `specs/08_naming_conventions.md` |
| `module.include`, `module.resource`, `platform.*` | `specs/04_layer_roles.md` + `specs/05_dependency_rules.md` + `specs/07_folder_structure.md` |
| OOP: `ida-no-*`, `reverse-dep`, `cross-feature` | `specs/A2_oop_adaptation.md` |

---

## Procedure

### Step 0: Read entry point

Read `guides/00_AI_ENTRYPOINT.md` only.
Do NOT read spec files yet.

### Step 1: Environment identification

- Identify programming language(s) and framework(s) from file extensions and
  project structure.
- Identify build system (CMake, MSBuild, npm, etc.).
- Note whether this is embedded/firmware, desktop, backend, or mobile.
- Note whether repo-root build files contain MCU/BSP/platform routing evidence.
- Determine architecture variant:
  - C/embedded (`.c`/`.h`) — standard spec rules
  - OOP (`.cs`/`.vb`/`.java`) — A2 appendix rules
  - Mixed — apply both as appropriate

Do not read spec files for this step.

### Step 2: Gate execution (Phase 1)

Run the appropriate gate script:

- C/embedded → `Verify-Comsect1Code.py -Root <comsect1_root> -RepoRoot <repo_root>`
- OOP → `Verify-OOPCode.py -Root <comsect1_root>`
- Spec repository → `Verify-Spec.py` + `Verify-ToolingConsistency.py`
- Unified runner → `Verify-AIADGate.py`

Collect gate output verbatim.

**If gate reports errors** (exit code 2): enter Phase 1 report mode.
- For each violation, read only the spec section from the lookup table above.
- Report findings with spec context.
- State: "Structural violations must be resolved before qualitative analysis.
  Re-run analysis after fixing these issues."
- Skip Steps 3–7.
- Proceed directly to Step 8 (report).

**If gate reports 0 errors** (warnings OK): proceed to Step 3 (Phase 2).

Also note from the file listing (no reading required):
- Which comsect1 prefix files exist (`ida_`, `prx_`, `poi_`, etc.)
- Whether the canonical folder skeleton is present (§7.3, §7.5)

### Step 3: Layer classification (Phase 2)

For each significant code unit, apply the 3-question discriminator.

Read `specs/02_overview.md` Section 2.3 for the discriminator.
For OOP projects: also read `specs/A2_oop_adaptation.md`.

If the project has 0 `ida_`/`prx_`/`poi_` files: tag `<ABSENT>`, proceed.
If platform-coupled evidence exists outside `/infra/platform/`, do not use
`<ABSENT>` for missing `hal_`/`bsp_`; tag the situation `<MISALIGNED>` and
describe it as misplaced platform responsibility.

| Current file/class | Proposed layer | Discriminator path | Tag | Rationale |
|--------------------|----------------|--------------------|-----|-----------|

### Step 4: Shared domain utilities (Phase 2)

Identify code reused across features:

- Contract vocabulary — `cfg_Core`
- Shared domain computation — `svc_`
- Feature-internal logic — stays in the feature

For each `svc_` module, verify role authenticity:

- Does it wrap an infrastructure mechanism (`mdw_`, `hal_`)?
- Does it provide reusable computation?
- Or is it merely a cross-feature data/dispatch channel?

A `svc_` module that stores and retrieves runtime data (including function
pointer tables) for consumption by another feature is a datastream (`stm_`)
pattern, not a service pattern. The gate flags this as
`service.infra-orphan`; Phase 2 analysis confirms or dismisses such flags
using semantic judgment.

### Step 5: Dependency analysis (Phase 2)

Map current dependencies and flag every violation with the specific spec
section it violates.

Read `specs/05_dependency_rules.md` as needed.

| Source file | Depends on | Direction | Tag | Spec section |
|-------------|------------|-----------|-----|--------------|

Direction: `allowed` or `prohibited`. Only prohibited or noteworthy
dependencies need rows. If all clean, state so and tag `<ALIGNED>`.

### Step 6: Layer balance analysis (Phase 2)

For each feature:

1. Read `ida_`, `poi_`, and `prx_` side by side.
2. Count domain-semantic conditionals in each layer.
3. Produce a balance table:

| Feature | ida_ decisions | poi_ decisions | prx_ decisions | Balance tag |
|---------|----------------|----------------|----------------|-------------|

4. Apply the requirement test:
   - If a business requirement change would modify `poi_`, the design is wrong.
   - If it would modify `ida_`, the design is aligned.

5. Flag anti-patterns by name:
   - **Empty Idea** — `ida_` has no or minimal domain logic.
   - **Fat Poiesis** — `poi_` contains domain-meaningful conditionals.
   - **Fat Praxis** — `prx_` exists but has no domain interpretation.

Read `specs/04_layer_roles.md` as needed.

### Step 7: Design direction (Phase 2)

Propose:

- Feature boundaries
- Layer split for each feature
- Shared domain utilities (`cfg_Core` / `svc_` / feature-internal)
- Interface boundaries for OOP projects
- A dependency graph showing allowed flow

Read `specs/04_layer_roles.md` (if not already read) for design proposals.

### Step 8: Report

Write the full report to `.comsect1-analysis.md`.
Display only the Verdict Block and Closing Summary in conversation (per EG-06).

For Phase 1 reports (gate failed): the report covers Steps 1–2 only.
For Phase 2 reports (gate passed): the report covers all Steps 1–8.
Gate results in Step 2 are reported verbatim in the gate's own format.
