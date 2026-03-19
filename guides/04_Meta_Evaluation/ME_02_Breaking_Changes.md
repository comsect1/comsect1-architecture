# ME-02: Breaking Change Policy

> **Purpose**: Define when a spec change is breaking, how to deprecate old
> patterns, and how downstream projects migrate safely.

---

## 1. Change Classification

Every spec or gate change falls into exactly one category:

| Category | Definition | Examples |
|----------|-----------|----------|
| **Additive** | New rule, prefix, or guide that does not invalidate existing compliant code. | New anti-pattern advisory, new `stm_` communication model, new guide document. |
| **Narrowing** | Existing rule becomes stricter. Code that was compliant may become non-compliant. | Raising gate severity from advisory to error, reducing allowed dependency set. |
| **Breaking** | Structural change that requires code reorganisation. | Renaming a role prefix, changing folder skeleton, altering the discriminator logic. |

**Rule**: Narrowing and Breaking changes must be explicitly tagged in
`specs/12_version_history.md` with `[NARROWING]` or `[BREAKING]` labels.

---

## 2. Deprecation Protocol

### 2.1 Deprecation Window

When a pattern is deprecated:

1. **Announce** — Add a deprecation note in the relevant spec section and in
   `specs/12_version_history.md` under the target release.
2. **Gate advisory** — Gate scripts emit an advisory (not error) for the
   deprecated pattern. The advisory message must include the replacement
   pattern and the removal target version.
3. **Migration period** — The deprecated pattern remains valid for at least
   one minor version cycle (e.g., deprecated in v1.1.0, removed no earlier
   than v1.2.0).
4. **Removal** — After the migration period, promote the advisory to an error
   and remove the deprecated pattern from normative text.

### 2.2 Exception: Security or Correctness

If a deprecated pattern causes architectural unsoundness (e.g., a dependency
rule that permits circular references), the migration period may be shortened
or skipped. Document the rationale in `specs/12_version_history.md`.

---

## 3. Downstream Migration Strategy

### 3.1 Version Pinning

Downstream projects pin the spec version they target:

```markdown
<!-- in project CLAUDE.md or README -->
comsect1-spec-version: v1.0.0
```

Gate scripts read this pin and apply the rule set for that version. When no
pin is declared, the latest spec version applies.

### 3.2 Migration Checklist

When upgrading from version N to version N+1:

1. Read `specs/12_version_history.md` entries between the two versions.
2. Filter for `[NARROWING]` and `[BREAKING]` labels.
3. For each narrowing change:
   - Run the updated gate against the project code.
   - Fix all new errors. Advisories may be deferred.
4. For each breaking change:
   - Follow the migration steps documented in the version history entry.
   - If no migration steps are provided, consult the relevant spec section.
5. Run the full gate suite (`Verify-Comsect1Code.py` or `Verify-OOPCode.py`)
   and confirm zero errors before updating the version pin.

### 3.3 Incremental Migration

For projects with large codebases:

- Migrate one feature at a time. The gate supports `-Root` scoping to check
  a subtree.
- Use feature branches for migration work. Merge only after gate passes.
- Do not mix migration commits with feature development commits.

---

## 4. Spec Author Obligations

When authoring a narrowing or breaking change:

| Obligation | Detail |
|-----------|--------|
| **Version history entry** | Must include `[NARROWING]` or `[BREAKING]` label, affected section references, and migration steps. |
| **Gate update** | Gate scripts must be updated in the same commit as the spec change. A spec rule without gate enforcement is incomplete. |
| **Example update** | If `specs/09_code_examples.md` shows the old pattern, update it to the new pattern. |
| **Tooling sync** | Run `python scripts/comsect1_ai_tooling.py sync-repo` to regenerate tooling surfaces. |

---

## 5. Version Numbering Convention

```text
v<major>.<minor>.<patch>

major  — Breaking changes to core architectural model (layer model,
         discriminator, dependency invariants).
minor  — Narrowing changes, new normative rules, new spec sections.
patch  — Additive changes, guide additions, gate bug fixes, advisory
         additions.
```

A version bump in `specs/12_version_history.md` is the single source of truth
for the current spec version.

---

## License

This document is part of the **comsect1 Architecture Specification**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

You are free to:
- **Share** - copy and redistribute the material in any medium or format for non-commercial purposes only.

Under the following terms:
- **Attribution** - You must give appropriate credit to the author (Kim Hyeongjeong), provide a reference to the license, and indicate if changes were made.
- **NonCommercial** - You may not use the material for commercial purposes.
- **NoDerivatives** - If you remix, transform, or build upon the material, you may not distribute the modified material.

No additional restrictions - You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
