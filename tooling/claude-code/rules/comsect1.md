# comsect1 Architecture - Global Bootstrap

This file is intentionally thin.

Before writing, reviewing, or refactoring any comsect1 work:

1. Read `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`.
2. Follow the canonical specs, guides, and gate scripts referenced there.
3. Treat this file only as Claude's global adapter into the shared entrypoint.

Do not maintain duplicated architecture rules here. Update the shared
entrypoint or canonical spec instead.

## Project-Specific Working Rules

<!-- Add project-specific rules below this line.                    -->
<!-- These rules should NOT restate canonical spec content.         -->
<!-- Example entries:                                               -->
<!--   - No new direct access to mutable globals from Form_*.      -->
<!--   - New state mutation must go through IColorStateStore.       -->
<!--   - Host adapters (Form_*.vb) live outside the comsect1/ boundary. -->
