# EG-06: Analysis Report Format

This guide defines the canonical output format for the comsect1 architecture
analysis. All AI tools that perform architecture analysis MUST follow this
format regardless of the tool or platform used.

The format is a **hybrid**: fixed skeleton for structure and objectivity,
free-form zones for interpretive analysis.

---

## Report output

Write the complete report to **`.comsect1-analysis-report.md`** at the root of the
analyzed target directory. This file enables cross-session continuity — a
different AI session can read the report and proceed with implementation.

**Display in conversation**: Show only the **Verdict Block (Section A)** and
the **Closing Summary (Section C)**. Do NOT display the full per-step sections
(B.1–B.8) in conversation — they are available in the file.

Rationale: The file captures full detail for cross-session continuity. The
Verdict Block and Closing Summary are sufficient for immediate review and
action. Displaying the full report in conversation significantly increases
output token consumption without adding information value.

If `.comsect1-analysis-report.md` already exists, overwrite it. The file captures
the latest analysis state, not a history.

---

## Tag vocabulary

Use angle-bracket tags for design analysis findings. These are NOT compliance
verdicts — they describe position on an alignment continuum.

| Tag | Meaning |
|-----|---------|
| `<ALIGNED>` | Structure matches comsect1 intent at current level of understanding |
| `<PARTIAL>` | Right direction, incomplete execution |
| `<MISALIGNED>` | Structure exists but contradicts comsect1 rules |
| `<ABSENT>` | Expected structure does not exist yet |
| `<NOTED>` | Interpretive observation, trade-off, or recommendation |

Do not use `[FAIL]`, `[WARN]`, `[VIOLATION]`, or `[ADVISORY]` in the report
body. Those belong to gate scripts and the reviewer agent respectively.

---

## Alignment Level

Three-tier verdict expressing position on the alignment continuum. None claim
arrival — consistent with asymptotic awareness.

- **Converging** — Most structures in place; remaining work is refinement.
- **Approaching** — Active directional alignment with significant remaining work.
- **Divergent** — Fundamental structural misalignment requiring rearchitecting.

Heuristic:
- Any `<MISALIGNED>` on a core structural dimension (layer direction, feature
  isolation, layer balance) → at most **Approaching**.
- Multiple `<MISALIGNED>` on core dimensions → **Divergent**.
- Majority `<ALIGNED>` with remaining `<PARTIAL>`/`<ABSENT>` → **Converging**.

---

## Report skeleton

### A. Verdict Block (FIXED — must appear first)

```text
## comsect1 Analysis Verdict

| Dimension        | Value                                            |
|------------------|--------------------------------------------------|
| Analyzed by      | <AI model name and version>                      |
| Target           | <path or feature name>                           |
| Environment      | <language / framework / architecture variant>    |
| Alignment Level  | Converging | Approaching | Divergent             |
| Features Found   | <count>                                          |
| Layers Present   | ida_: <N>  prx_: <N>  poi_: <N>                 |
| Shared Resources | cfg_: <N>  svc_: <N>  stm_: <N> ...             |
| Gate Available   | Yes (<script name>) | No                         |

**Verdict**: <one or two sentences — must reference the Alignment Level and
state the primary structural factor that determined it.>
```

### B. Section Reports (FIXED skeleton per step)

Each analysis step produces a section following this pattern:

```text
### Step N: <Title>

**Findings**: <total count> (<ALIGNED>: N, <PARTIAL>: N, <MISALIGNED>: N, <ABSENT>: N, <NOTED>: N)

<required table or list — format defined per step below>

**Interpretation**:
<free-form analytical prose — explain why findings have their tags, reference
spec sections, discuss design implications>
```

**Per-step required elements:**

**Step 1 — Environment Identification**: Language(s), framework(s), build
system, architecture variant. One tag for environment clarity.

**Step 2 — Existing comsect1 Status**:

| Prefix category | Files found | Status tag |
|-----------------|-------------|------------|
| ida_            |             |            |
| prx_            |             |            |
| poi_            |             |            |
| cfg_ / db_      |             |            |
| svc_ / mdw_     |             |            |
| hal_ / bsp_     |             |            |
| stm_            |             |            |
| Gate scripts    |             |            |
| AI adapter      |             |            |

**Step 3 — Layer Classification**:

| Current file/class | Proposed layer | Discriminator path | Tag | Rationale |
|--------------------|----------------|--------------------|-----|-----------|

**Step 4 — Shared Domain Utilities**: List candidates grouped by scope
(cfg_Core / svc_ / feature-internal), each tagged.

**Step 5 — Dependency Analysis**:

| Source file | Depends on | Direction | Tag | Spec section |
|------------|------------|-----------|-----|--------------|

Direction: `allowed` or `prohibited`. Only prohibited or noteworthy
dependencies need rows. If all clean, state so and tag `<ALIGNED>`.

**Step 6 — Layer Balance Analysis**:

| Feature | ida_ decisions | poi_ decisions | prx_ decisions | Balance tag |
|---------|----------------|----------------|----------------|-------------|

Apply the requirement test and state result per feature.

**Step 7 — Design Direction**: Feature boundary list, proposed layer split,
interface boundaries (OOP), dependency graph. Each proposal tagged.

**Step 8 — Gate Execution**: Report gate results **verbatim** in the gate's
own format. Do not re-tag `[FAIL]`/`[WARN]` findings with analyze tags.
If no gate available, state reason and recommend the appropriate script.

### C. Closing Summary (FIXED — must appear last)

```text
## Summary

### Alignment Profile

| Tag           | Count | Percentage |
|---------------|-------|------------|
| <ALIGNED>     |       |            |
| <PARTIAL>     |       |            |
| <MISALIGNED>  |       |            |
| <ABSENT>      |       |            |
| <NOTED>       |       |            |
| **Total**     |       | 100%       |

### Feature Alignment Table

| Feature | ida_ | prx_ (justified?) | poi_ | Resources | Alignment |
|---------|------|--------------------|------|-----------|-----------|

### Verdict Restatement

<Restate the verdict from Section A. Must be consistent with the opening
verdict. If detailed analysis changed the assessment, update both.>

### Recommended Next Steps

<Ordered list of concrete actions. Reference the specific finding tag and
step that motivates each action. Prioritize: <MISALIGNED> first, then
<ABSENT>, then <PARTIAL>.>
```

---

## Conventions

1. Tag counts in the Closing Summary MUST match actual tags used in
   Sections B.1–B.8.
2. The Verdict Block (A) and Verdict Restatement (C) MUST be consistent.
3. Gate output (Step 8) retains its own format — do not translate.
4. Free-form interpretation should be proportional to finding complexity.
5. Alignment Level is a holistic judgment, not a mechanical threshold.

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.1**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

You are free to:
- **Share** - copy and redistribute the material in any medium or format for non-commercial purposes only.

Under the following terms:
- **Attribution** - You must give appropriate credit to the author (Kim Hyeongjeong), provide a reference to the license, and indicate if changes were made.
- **NonCommercial** - You may not use the material for commercial purposes.
- **NoDerivatives** - If you remix, transform, or build upon the material, you may not distribute the modified material.

No additional restrictions - You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
