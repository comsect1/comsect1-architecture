# EG-08: Review Procedure

This guide defines the canonical review procedure for comsect1 architecture
compliance review. All AI tools that perform architecture review MUST follow
this procedure regardless of the tool or platform used.

For the analysis procedure (new design and refactoring), see **EG-07**.
For the analysis report format, see **EG-06**.

---

## Canonical sources

Before starting any review, read:

- `guides/00_AI_ENTRYPOINT.md`
- `specs/04_layer_roles.md`
- `specs/05_dependency_rules.md`
- `specs/07_folder_structure.md`
- `specs/11_checklist.md`
- `specs/A2_oop_adaptation.md` — for OOP projects

All rules you check MUST come from the canonical spec. Do NOT invent,
summarize, or reinterpret rules. If you are unsure about a rule, read the
spec again.

---

## Review checks

Perform each check in order.

### 0. Folder structure

- Verify the canonical comsect1 folder skeleton is present (`specs/07_folder_structure.md`
  §7.3, §7.5):
  - `/api` public membrane exists at the comsect1 root.
  - `/project` and `/project/features` exist.
  - `examples/` is NOT inside the `/comsect1` boundary.
- For standalone middleware repositories, apply the standalone layout rules (§7.10):
  - `/api` is at the comsect1 root, NOT under `deps/middleware/<name>/api/`.
- Flag any folder structure violation before proceeding to file content checks.

### 1. Idea layer purity (ida_ files)

- Apply the constraints from `specs/04_layer_roles.md`.
- Must NOT import or include external framework namespaces (UI, I/O, hardware,
  interop).
- Allowed dependencies: own prx_/poi_ and cfg_Core vocabulary only.

### 2. Reverse dependencies

- prx_ must NOT reference ida_.
- poi_ must NOT reference ida_ or prx_.

### 3. Cross-feature isolation

- ida_/prx_/poi_ of feature A must NOT reference ida_/prx_/poi_ of feature B.
- Cross-feature communication must use stm_ only.
- Shared resources (cfg_, db_, stm_, svc_, mdw_, hal_, bsp_) are not features
  and are accessible from prx_/poi_ by design.

### 4. Platform and resource boundary

- Platform (HAL/BSP) must NOT include feature headers (ida_/prx_/poi_).
- Resources (cfg_/db_/stm_) must NOT include any upper-layer header.
- Non-platform files must not directly include vendor/device/BSP/CMSIS headers or raw platform symbols.
- If platform evidence appears outside `/infra/platform/`, review it as misplaced platform responsibility.
- If one file mixes peripheral abstraction and board wiring, review it as "HAL/BSP mixed responsibility" advisory.

### 5. Praxis justification (advisory)

- If prx_ exists, apply the 3-question discriminator from `specs/02_overview.md`.
- If prx_ is just mechanical wrapping, it should be poi_.
- If prx_ is pure domain logic without external coupling, it should be ida_.

### 6. Layer balance (blocking)

For each feature that has both ida_ and poi_ (or prx_):

1. Count domain-semantic conditionals in each layer.
2. Flag a violation if ida_ has zero domain decisions while poi_ or prx_ carries
   them.
3. Flag a violation if ida_ only delegates and all domain logic lives below it.
4. Flag a violation if poi_ contains business-rule conditionals.
5. Apply the requirement test: if a business requirement change would modify
   poi_ instead of ida_, the layers are wrong.

### 7. Red Flag heuristics (advisory)

- **Empty Idea**: ida_ has no or minimal domain logic.
- **Fat Poiesis**: poi_ contains domain-meaningful conditionals.
- **Fat Praxis**: prx_ is mostly wrappers with no meaningful interpretation
  logic.

### 8. OOP-specific checks

Apply only when the target is an OOP codebase (`.cs`, `.vb`, `.java`):

- Apply A2.5.1 constraints for ida_ classes (immutability, referential
  transparency).
- Verify interface ownership: upper layer owns the interface, lower layer
  implements.
- Verify `svc_` placement under `/infra/service/`.

---

## Procedure

1. Read the canonical sources listed above.
2. Check folder structure first (check 0). Flag violations before continuing.
3. Scan the target directory for files with comsect1 prefixes.
4. Detect environment: C/embedded, OOP, or mixed.
5. Determine each file's role from the prefix.
6. Read the file and check it against the spec rules (checks 1–4 above).
7. Group ida_/prx_/poi_ by feature and perform the layer balance check
   (check 6).
8. Apply Red Flag heuristics as advisory findings (check 7).
9. Apply OOP-specific checks when applicable (check 8).
10. If gate scripts exist, run them when feasible:
   - Tooling drift: `Verify-ToolingConsistency.py`
   - C/embedded: `Verify-Comsect1Code.py`
   - OOP: `Verify-OOPCode.py`
   - Unified: `Verify-AIADGate.py`
11. Report all findings.

---

## Output format

Report each finding as:

```text
[VIOLATION] file:line - rule - description
[ADVISORY] file:line - rule - description
```

End with a summary:

- Total files checked
- Violations found (count by rule)
- Advisory notes
- Gate script result (if available)

---

## Constraints

- Do NOT suggest fixes. Only report violations.
- Do NOT modify any files.
- Do NOT make assumptions about intent — report what you see.
- Always cite the specific canonical spec section that was violated.
- NEVER invent rules. Every violation must trace to a specific section of the
  canonical spec.
- Shared resources (svc_, cfg_, db_, stm_, mdw_, hal_, bsp_) are accessible
  from prx_/poi_ by design. Do not flag these as violations.
