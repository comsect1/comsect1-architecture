#!/usr/bin/env python3
"""Shared AI tooling generation, install, and verification helpers."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

from comsect1_gate_helpers import resolve_repo_root

PLACEHOLDER_REPO = "{{COMSECT1_ROOT}}"
PLACEHOLDER_PROJECT = "{{PROJECT_ROOT}}"
TEXT_FILE_SUFFIXES = {
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".ps1",
    ".sh",
}


@dataclass(frozen=True)
class GeneratedBlockFile:
    template: str
    blocks: dict[str, str]


@dataclass(frozen=True)
class InstallEntry:
    source_rel: str
    target_rel: str
    kind: str  # "file" or "dir"


@dataclass(frozen=True)
class InstallSpec:
    key: str
    display_name: str
    home_env: str | None
    default_home: str
    unit_label: str
    entries: tuple[InstallEntry, ...]
    prune_target_rels: tuple[str, ...] = ()


def _normalize(text: str) -> str:
    text = textwrap.dedent(text).lstrip("\n")
    if not text.endswith("\n"):
        text += "\n"
    return text


def _write_text_utf8(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _read_text_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _replace_placeholders(text: str, replacements: dict[str, str]) -> str:
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def _generated_block_begin(name: str) -> str:
    return f"<!-- BEGIN GENERATED: {name} -->"


def _generated_block_end(name: str) -> str:
    return f"<!-- END GENERATED: {name} -->"


def _render_generated_block(name: str, content: str) -> str:
    block_body = _normalize(content).rstrip("\n")
    return (
        f"{_generated_block_begin(name)}\n"
        f"{block_body}\n"
        f"{_generated_block_end(name)}\n"
    )


def _generated_block_span(document: str, name: str) -> tuple[int, int]:
    begin = _generated_block_begin(name)
    end = _generated_block_end(name)
    start = document.find(begin)
    if start < 0:
        raise ValueError(f"Missing generated block start marker: {name}")
    finish = document.find(end, start)
    if finish < 0:
        raise ValueError(f"Missing generated block end marker: {name}")
    finish += len(end)
    if finish < len(document) and document[finish] == "\n":
        finish += 1
    return start, finish


def _extract_generated_block(document: str, name: str) -> str:
    start, finish = _generated_block_span(document, name)
    return document[start:finish]


def _apply_generated_blocks(document: str, blocks: dict[str, str]) -> str:
    updated = document
    for name, content in blocks.items():
        start, finish = _generated_block_span(updated, name)
        updated = updated[:start] + _render_generated_block(name, content) + updated[finish:]
    return updated


def _render_repo_adapter(tool_name: str) -> str:
    return _normalize(
        f"""
        # Project Adapter for {tool_name}

        This file is intentionally thin.

        Before doing any work in this repository:

        1. Read `guides/00_AI_ENTRYPOINT.md`.
        2. Follow the canonical specs, guides, and gate scripts referenced there.
        3. Treat this file only as the {tool_name} adapter for the shared entrypoint.

        This repository is the canonical comsect1 specification repository, so spec,
        guide, script, and tooling changes must preserve the single-entrypoint model.
        """
    )


def _render_codex_project_adapter_template() -> str:
    return _normalize(
        f"""
        # comsect1 Project Adapter for Codex

        This file is intentionally thin.

        Read these sources before working on this project:

        1. `{PLACEHOLDER_REPO}/guides/00_AI_ENTRYPOINT.md`
        2. The relevant specs, guides, and gate scripts referenced there

        Project root: `{PLACEHOLDER_PROJECT}`

        Use the canonical comsect1 repository as SSOT. Run gate scripts from
        `{PLACEHOLDER_REPO}/scripts/` against this project's actual code root.

        Do not restate canonical architecture rules in this file. Add only project-local
        notes below.

        ## Project-Specific Working Rules

        <!-- Add project-local rules below this line. -->
        """
    )


def _render_claude_global_rule() -> str:
    return _normalize(
        f"""
        # comsect1 Architecture - Global Bootstrap

        This file is intentionally thin.

        Before writing, reviewing, or refactoring any comsect1 work:

        1. Read `{PLACEHOLDER_REPO}/guides/00_AI_ENTRYPOINT.md`.
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
        """
    )


def _render_run_gates_script() -> str:
    return _normalize(
        """
        #!/usr/bin/env bash
        # Run the unified AIAD gate against a target codebase.
        # Usage: run-gates.sh [code-root]
        #   code-root  Path to the comsect1 code directory (optional, skips code gate if omitted)

        set -euo pipefail

        SPEC_ROOT="{{COMSECT1_ROOT}}"
        SCRIPT_DIR="$SPEC_ROOT/scripts"
        REPORT_PATH=".aiad-gate-report.json"

        CODE_ROOT="${1:-}"

        if [[ -n "$CODE_ROOT" ]]; then
            python "$SCRIPT_DIR/Verify-AIADGate.py" \\
                -CodeRoot "$CODE_ROOT" \\
                -ReportPath "$REPORT_PATH"
        else
            python "$SCRIPT_DIR/Verify-AIADGate.py" \\
                -SkipCode \\
                -ReportPath "$REPORT_PATH"
        fi

        echo "--- Gate report: $REPORT_PATH ---"
        cat "$REPORT_PATH"
        """
    )


def _render_codex_review_skill() -> str:
    return _normalize(
        """
        ---
        name: comsect1-review
        description: Review code or specifications for comsect1 architecture compliance. Use when the user asks for a review, audit, dependency check, violation scan, or conformance assessment.
        ---

        # comsect1 Review

        ## Step 0: Load the Canonical Sources

        Before starting any review, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/specs/04_layer_roles.md`
        - `{{COMSECT1_ROOT}}/specs/05_dependency_rules.md`
        - `{{COMSECT1_ROOT}}/specs/07_folder_structure.md`
        - `{{COMSECT1_ROOT}}/specs/11_checklist.md`
        - `{{COMSECT1_ROOT}}/specs/A2_oop_adaptation.md` for OOP projects

        ## Review procedure and output format

        Follow the canonical review procedure defined in:
        `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_08_Review_Procedure.md`

        Read that guide before starting. Perform each check and step in order and
        report findings as you go.
        """
    )



def _render_codex_structure_skill() -> str:
    return _normalize(
        """
        ---
        name: comsect1-structure
        description: Structure & Migration Pack for comsect1. Use when inspecting folder skeleton, naming, misplaced files, and legacy-layout migration order.
        ---

        # comsect1 Structure

        ## Step 0: Load the Canonical Sources

        Before starting structural inspection, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
        - `{{COMSECT1_ROOT}}/specs/07_folder_structure.md`
        - `{{COMSECT1_ROOT}}/specs/08_naming_conventions.md`
        - `{{COMSECT1_ROOT}}/specs/11_checklist.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_02_Refactoring_Legacy.md`

        ## Pack Responsibility

        Focus only on physical structure and migration order.

        - inspect root skeleton and folder grouping
        - detect misplaced files and legacy layout leftovers
        - detect naming, path-placement, and build-path drift
        - produce structural migration order before semantic rebuilding starts
        """
    )


def _render_codex_layer_skill() -> str:
    return _normalize(
        """
        ---
        name: comsect1-layer
        description: Layer & Dependency Pack for comsect1. Use when applying the discriminator, correcting ida_/prx_/poi_ placement, and cleaning dependency direction.
        ---

        # comsect1 Layer

        ## Step 0: Load the Canonical Sources

        Before starting layer and dependency work, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
        - `{{COMSECT1_ROOT}}/specs/02_overview.md`
        - `{{COMSECT1_ROOT}}/specs/04_layer_roles.md`
        - `{{COMSECT1_ROOT}}/specs/05_dependency_rules.md`
        - `{{COMSECT1_ROOT}}/guides/01_Design_Principles/DP_03_Praxis_Justification.md`
        - `{{COMSECT1_ROOT}}/specs/A2_oop_adaptation.md` for OOP projects

        ## Pack Responsibility

        Focus only on semantic layer placement and dependency cleanup.

        - apply the 3-question discriminator
        - record discriminator results before modifying code
        - identify logic that must move, split, or be rebuilt across ida_/prx_/poi_
        - identify dependency cleanup targets, reverse dependencies, and layer-balance problems
        """
    )


def _render_codex_risk_skill() -> str:
    return _normalize(
        """
        ---
        name: comsect1-risk
        description: Risk & Exception Pack for comsect1. Use when scanning for anti-patterns, unreasonable logic placement, and recurring exception hazards.
        ---

        # comsect1 Risk

        ## Step 0: Load the Canonical Sources

        Before scanning for risks and exceptions, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
        - `{{COMSECT1_ROOT}}/specs/10_anti_patterns.md`
        - `{{COMSECT1_ROOT}}/specs/11_checklist.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_05_Application_Feedback.md`
        - `{{COMSECT1_ROOT}}/guides/04_Meta_Evaluation/ME_01_Upstream_Alignment.md`
        - `{{COMSECT1_ROOT}}/specs/A2_oop_adaptation.md` for OOP projects

        ## Pack Responsibility

        Focus only on recurring design hazards and escalation signals.

        - identify known anti-patterns
        - flag unreasonable logic placement, suspicious abstractions, and exception creep
        - distinguish blocking issues from advisory findings
        - note when a recurring pattern should enter the feedback loop instead of being treated as a one-off mistake
        """
    )


def _render_codex_verify_skill() -> str:
    return _normalize(
        """
        ---
        name: comsect1-verify
        description: Verification & Governance Pack for comsect1. Use when running checklists, gates, evidence capture, and escalation routing.
        ---

        # comsect1 Verify

        ## Step 0: Load the Canonical Sources

        Before verification or governance work, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
        - `{{COMSECT1_ROOT}}/guides/03_Verification/V_01_Post_Task_Checklist.md`
        - `{{COMSECT1_ROOT}}/guides/03_Verification/V_02_AIAD_Auto_Gate.md`
        - `{{COMSECT1_ROOT}}/guides/03_Verification/V_03_Multi_Project_Gate.md`
        - `{{COMSECT1_ROOT}}/guides/04_Meta_Evaluation/ME_01_Upstream_Alignment.md`

        ## Pack Responsibility

        Focus only on verification, evidence, and escalation.

        - run or coordinate checklists and gates
        - capture evidence paths and gate results
        - check tooling drift when this repository is edited
        - route ADR or upstream-alignment escalation when needed
        """
    )



def _render_codex_refactor_skill() -> str:
    return _normalize(
        """
        ---
        name: comsect1-refactor
        description: Single comsect1 entry point. Use for analysis, refactoring, or maintenance under the canonical pack taxonomy.
        ---

        # comsect1 Refactor

        ## Step 0: Load the Canonical Sources

        Before doing anything, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/guides/00_Process_Overview.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_07_Analysis_Procedure.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_06_Analysis_Report_Format.md`
        - `{{COMSECT1_ROOT}}/guides/03_Verification/V_01_Post_Task_Checklist.md`
        - `{{COMSECT1_ROOT}}/guides/03_Verification/V_02_AIAD_Auto_Gate.md`

        ## Procedure

        This is the single entry point for all comsect1 work.

        Start with the analysis phase using the canonical 8-step procedure from
        `EG_07`. Do not skip analysis. Write the analysis report to
        **`.comsect1-analysis-report.md`** at the target root (format defined in
        `EG_06`).

        Then follow the canonical pack order:

        1. Director — classify task, choose required packs, order them
        2. Structure & Migration
        3. Layer & Dependency
        4. Risk & Exception
        5. Execution — apply the approved plan, preserve discriminator records
        6. Verification & Governance

        Produce one coherent end-to-end result and do not redefine pack meanings.

        ## Gate Execution

        After the Verification pack completes, run the bundled gate script:

        ```bash
        bash scripts/run-gates.sh [code-root-if-applicable]
        ```

        This executes `Verify-AIADGate.py` (spec + tooling + code gates) and
        writes `.aiad-gate-report.json`. If the gate fails, fix findings before
        reporting the task as complete.
        """
    )


def _render_claude_new_project_skill() -> str:
    return _normalize(
        """
        ---
        name: comsect1-new-project
        description: Create a new comsect1 IAR embedded C project with unit-qualified files, CMake, and VSCode config.
        argument-hint: "<unit> <mcu> [features]"
        ---

        # comsect1 New Project

        Create a new comsect1 project with full IAR embedded C setup.

        ## Arguments

        Parse `$ARGUMENTS` as: `<unit> <mcu> [comma-separated features]`

        Example: `demo STM32F407 sensor,display`

        ## Canonical references

        Before generating, review:

        - `{{COMSECT1_ROOT}}/specs/07_folder_structure.md` — folder layout (§7.5)
        - `{{COMSECT1_ROOT}}/specs/08_naming_conventions.md` — unit-qualified naming (§8.6)
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_01_New_Project_Setup.md` — setup guide
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_04_Build_System.md` — build system guide

        ## Execution

        Run the scaffold script:

        ```bash
        python {{COMSECT1_ROOT}}/scripts/New-Comsect1Scaffold.py \\
            -Path {{PROJECT_ROOT}}/codes/comsect1 \\
            -Unit <unit> -MCU <mcu> \\
            -Features <features> -FullProject
        ```

        If `{{PROJECT_ROOT}}` is not set, ask the user for the target project directory.

        ## Generated structure

        ```text
        <project-root>/
          CMakeLists.txt
          cmake/iar-toolchain.cmake
          .vscode/tasks.json
          .vscode/launch.json
          .vscode/settings.json
          codes/
            main.c
            comsect1/
              api/app_<unit>.h
              project/config/cfg_project_<unit>.h
              project/features/<feat>/ida_<feat>_<unit>.c/h
              project/features/<feat>/poi_<feat>_<unit>.c/h
              infra/bootstrap/cfg_core_<unit>.h
              infra/bootstrap/ida_core_<unit>.c/h
              infra/bootstrap/poi_core_<unit>.c/h
              infra/service/
              infra/platform/hal/
              infra/platform/bsp/
              deps/extern/
              deps/middleware/
        ```

        Note: `prx_` files are NOT generated — create them only after applying the
        3-question discriminator (spec §5).

        ## Post-generation customization

        After running the script, guide the user through:

        1. **IAR path** — update `cmake/iar-toolchain.cmake` with actual IAR installation path
        2. **Linker script** — set `LINKER_SCRIPT` to the project `.icf` file
        3. **cfg_core** — add project-specific contract types to `cfg_core_<unit>.h`
        4. **cfg_project** — add MCU-specific defines to `cfg_project_<unit>.h`
        5. **Feature logic** — implement business logic in `ida_<feat>_<unit>.c`
        6. **Discriminator** — apply §5 discriminator to decide if `prx_` is needed per feature
        """
    )


def _render_claude_refactor_skill() -> str:
    return _normalize(
        """
        ---
        name: comsect1-refactor
        description: Single comsect1 entry point. Use for analysis, refactoring, or maintenance under the canonical pack taxonomy.
        argument-hint: "[target-path or task]"
        disable-model-invocation: true
        ---

        # comsect1 Refactor

        Before doing anything, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/guides/00_Process_Overview.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_07_Analysis_Procedure.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_06_Analysis_Report_Format.md`
        - `{{COMSECT1_ROOT}}/guides/03_Verification/V_01_Post_Task_Checklist.md`
        - `{{COMSECT1_ROOT}}/guides/03_Verification/V_02_AIAD_Auto_Gate.md`

        ## Target

        Analyze / refactor: `$ARGUMENTS`

        ## Project context

        Current branch: !`git branch --show-current 2>/dev/null`
        Recent commits: !`git log --oneline -5 2>/dev/null`
        Current files: !`git ls-files --others --cached --exclude-standard 2>/dev/null | head -80`

        ## Procedure

        This is the single entry point for all comsect1 work.

        Start with the analysis phase using the canonical 8-step procedure from
        `EG_07`. Do not skip analysis. Write the analysis report to
        **`.comsect1-analysis-report.md`** at the target root (format defined in
        `EG_06`).

        Then follow the canonical pack order:

        1. Director — classify task, choose required packs, order them
        2. Structure & Migration
        3. Layer & Dependency
        4. Risk & Exception
        5. Execution — apply the approved plan, preserve discriminator records
        6. Verification & Governance

        Produce one coherent end-to-end result and do not redefine pack meanings.

        ## Gate execution

        After the Verification pack completes, run the bundled gate script:

        ```bash
        bash scripts/run-gates.sh [code-root-if-applicable]
        ```

        This executes `Verify-AIADGate.py` (spec + tooling + code gates) and
        writes `.aiad-gate-report.json`. If the gate fails, fix findings before
        reporting the task as complete.
        """
    )


def _render_claude_reviewer_agent() -> str:
    return _normalize(
        """
        ---
        name: comsect1-reviewer
        description: Reviews code for comsect1 architecture compliance. Checks dependency direction, layer classification, cross-feature isolation, and forbidden imports. Use for parallel architecture verification without polluting main context.
        tools: Read, Grep, Glob, Bash
        model: sonnet
        maxTurns: 15
        ---

        # comsect1 Architecture Reviewer

        You are a comsect1 architecture compliance reviewer. Your job is to find
        violations, not to fix them.

        ## Step 0: Read the Canonical Sources

        Before starting any review, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/specs/04_layer_roles.md`
        - `{{COMSECT1_ROOT}}/specs/05_dependency_rules.md`
        - `{{COMSECT1_ROOT}}/specs/07_folder_structure.md`
        - `{{COMSECT1_ROOT}}/specs/11_checklist.md`
        - `{{COMSECT1_ROOT}}/specs/A2_oop_adaptation.md` for OOP projects

        ## Review procedure and output format

        Follow the canonical review procedure defined in:
        `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_08_Review_Procedure.md`

        Read that guide before starting. Perform each check and step in order and
        report findings as you go.
        """
    )


def _render_claude_structure_agent() -> str:
    return _normalize(
        """
        ---
        name: comsect1-structure
        description: Structure & Migration Pack for comsect1. Inspects folder structure, naming, placement, and legacy-layout migration order.
        tools: Read, Grep, Glob, Bash
        model: sonnet
        maxTurns: 15
        ---

        # comsect1 Structure

        Before starting structural inspection, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
        - `{{COMSECT1_ROOT}}/specs/07_folder_structure.md`
        - `{{COMSECT1_ROOT}}/specs/08_naming_conventions.md`
        - `{{COMSECT1_ROOT}}/specs/11_checklist.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_02_Refactoring_Legacy.md`

        Pack responsibility:

        - inspect folder skeleton and grouping
        - detect misplaced files and legacy leftovers
        - detect naming, path-placement, and build-path drift
        - report structural migration order only
        """
    )


def _render_claude_layer_agent() -> str:
    return _normalize(
        """
        ---
        name: comsect1-layer
        description: Layer & Dependency Pack for comsect1. Rebuilds layer boundaries by applying the discriminator and identifying dependency cleanup targets.
        tools: Read, Grep, Glob, Bash
        model: sonnet
        maxTurns: 15
        ---

        # comsect1 Layer

        Before starting layer rebuild work, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
        - `{{COMSECT1_ROOT}}/specs/02_overview.md`
        - `{{COMSECT1_ROOT}}/specs/04_layer_roles.md`
        - `{{COMSECT1_ROOT}}/specs/05_dependency_rules.md`
        - `{{COMSECT1_ROOT}}/guides/01_Design_Principles/DP_03_Praxis_Justification.md`
        - `{{COMSECT1_ROOT}}/specs/A2_oop_adaptation.md` for OOP projects

        Pack responsibility:

        - apply the 3-question discriminator
        - record discriminator results before code movement
        - identify logic that must move, split, or be rebuilt across layers
        - identify dependency cleanup targets and layer-balance problems
        """
    )


def _render_claude_risk_agent() -> str:
    return _normalize(
        """
        ---
        name: comsect1-risk
        description: Risk & Exception Pack for comsect1. Scans for anti-patterns, unreasonable logic placement, and recurring exception hazards.
        tools: Read, Grep, Glob, Bash
        model: sonnet
        maxTurns: 15
        ---

        # comsect1 Risk

        Before scanning for anti-patterns, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
        - `{{COMSECT1_ROOT}}/specs/10_anti_patterns.md`
        - `{{COMSECT1_ROOT}}/specs/11_checklist.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_05_Application_Feedback.md`
        - `{{COMSECT1_ROOT}}/guides/04_Meta_Evaluation/ME_01_Upstream_Alignment.md`
        - `{{COMSECT1_ROOT}}/specs/A2_oop_adaptation.md` for OOP projects

        Pack responsibility:

        - identify known anti-patterns
        - flag unreasonable logic placement and suspicious abstraction growth
        - separate blocking issues from advisory signals
        - note feedback-loop hotspots when a pattern looks systemic rather than local
        """
    )


def _render_claude_verify_agent() -> str:
    return _normalize(
        """
        ---
        name: comsect1-verify
        description: Verification & Governance Pack for comsect1. Runs checklists, gates, evidence capture, and escalation routing.
        tools: Read, Grep, Glob, Bash
        model: sonnet
        maxTurns: 15
        ---

        # comsect1 Verify

        Before verification or governance work, read:

        - `{{COMSECT1_ROOT}}/guides/00_AI_ENTRYPOINT.md`
        - `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_09_AI_Subagent_Operation.md`
        - `{{COMSECT1_ROOT}}/guides/03_Verification/V_01_Post_Task_Checklist.md`
        - `{{COMSECT1_ROOT}}/guides/03_Verification/V_02_AIAD_Auto_Gate.md`
        - `{{COMSECT1_ROOT}}/guides/03_Verification/V_03_Multi_Project_Gate.md`
        - `{{COMSECT1_ROOT}}/guides/04_Meta_Evaluation/ME_01_Upstream_Alignment.md`

        Pack responsibility:

        - run or coordinate checklists and gates
        - capture evidence paths and gate results
        - check tooling drift when this repository is edited
        - route ADR or upstream-alignment escalation when needed
        """
    )



def _render_codex_review_openai_yaml() -> str:
    return _normalize(
        """
        interface:
          display_name: "comsect1 Review"
          short_description: "Review code and specs for comsect1 compliance"
          default_prompt: "Use $comsect1-review to review this change for comsect1 compliance, findings first, and cite the governing rules."
        """
    )



def _render_codex_structure_openai_yaml() -> str:
    return _normalize(
        """
        interface:
          display_name: "comsect1 Structure"
          short_description: "Inspect comsect1 layout, naming, and migration drift"
          default_prompt: "Use $comsect1-structure to inspect folder structure, naming, misplaced files, and legacy-layout migration order."
        """
    )


def _render_codex_layer_openai_yaml() -> str:
    return _normalize(
        """
        interface:
          display_name: "comsect1 Layer"
          short_description: "Rebuild comsect1 layer and dependency boundaries"
          default_prompt: "Use $comsect1-layer to apply the discriminator, correct ida_/prx_/poi_ placement, and clean dependency direction."
        """
    )


def _render_codex_risk_openai_yaml() -> str:
    return _normalize(
        """
        interface:
          display_name: "comsect1 Risk"
          short_description: "Scan for comsect1 anti-patterns and exception hazards"
          default_prompt: "Use $comsect1-risk to scan for anti-patterns, unreasonable logic placement, and recurring exception hazards."
        """
    )


def _render_codex_verify_openai_yaml() -> str:
    return _normalize(
        """
        interface:
          display_name: "comsect1 Verify"
          short_description: "Run comsect1 verification and governance checks"
          default_prompt: "Use $comsect1-verify to run the relevant checklists, gates, and escalation routing for this task."
        """
    )



def _render_codex_refactor_openai_yaml() -> str:
    return _normalize(
        """
        interface:
          display_name: "comsect1 Refactor"
          short_description: "Run one-command end-to-end comsect1 refactoring"
          default_prompt: "Use $comsect1-refactor to perform end-to-end comsect1 refactoring or maintenance using the canonical pack sequence."
        """
    )


def _render_codex_install_doc() -> str:
    return _normalize(
        """
        # comsect1 Codex Package

        This package is the Codex adapter for the shared comsect1 AI entrypoint.

        See [`../INSTALL.md`](../INSTALL.md) for the common packaging model and update
        policy.

        Generated surface:
        - synchronized by `python scripts/comsect1_ai_tooling.py sync-repo`
        - verified by `python scripts/Verify-ToolingConsistency.py`

        ## Installs

        ```text
        $CODEX_HOME/skills/
          comsect1-refactor/
          comsect1-review/

        <target-project>/
          AGENTS.md
        ```

        If `CODEX_HOME` is not set, the scripts default to `~/.codex/`.

        ## Install Skills

        ```bash
        git clone <comsect1-architecture-repo>
        cd comsect1-architecture
        bash tooling/codex/install.sh
        ```

        PowerShell (Windows):

        ```powershell
        powershell -ExecutionPolicy Bypass -File tooling\\codex\\install.ps1
        ```

        The shell and PowerShell wrappers are thin entrypoints over:

        ```text
        python scripts/comsect1_ai_tooling.py install --tool codex
        ```

        ## Bootstrap a Project

        ```bash
        bash tooling/codex/bootstrap-project.sh /path/to/project
        ```

        PowerShell (Windows):

        ```powershell
        powershell -ExecutionPolicy Bypass -File tooling\\codex\\bootstrap-project.ps1 -ProjectRoot C:\\path\\to\\project
        ```

        Both wrappers delegate to:

        ```text
        python scripts/comsect1_ai_tooling.py bootstrap --tool codex --project-root /path/to/project
        ```

        ## Verify

        Confirm:

        1. Codex lists `comsect1-refactor`
        2. Codex lists `comsect1-review`
        3. the target project has a thin `AGENTS.md`

Restart Codex after installing skills so new skills are picked up.
In Codex, these are skills invoked with `$...`, not slash commands.
Check the `$` skill picker after a full Codex restart.

The installer removes older skills such as `comsect1-analyze`,
`comsect1-director`, and `comsect1-layer` so the visible top-level command set
stays minimal. Analysis is now built into `comsect1-refactor`.

Default use:

- use `comsect1-refactor` for normal end-to-end work (includes analysis)
- use `comsect1-review` only when you want findings-only review

        Explicit invocation examples:

        ```text
        $comsect1-refactor refactor codes/comsect1 end-to-end.
        $comsect1-review review this change for comsect1 compliance.
        ```

Pack taxonomy remains canonical, but Codex does not expose each pack as a
top-level user-visible skill. Use `comsect1-refactor` as the normal command.

        ## Project-local Rule

        Keep the downstream `AGENTS.md` thin:

        - point to `guides/00_AI_ENTRYPOINT.md`
        - add only project-local notes
        - do not restate canonical rules
        """
    )


def _render_claude_install_doc() -> str:
    return _normalize(
        """
        # comsect1 Claude Code Package

        This package is the Claude Code adapter for the shared comsect1 AI entrypoint.

        See [`../INSTALL.md`](../INSTALL.md) for the common packaging model and update
        policy.

        Generated surface:
        - synchronized by `python scripts/comsect1_ai_tooling.py sync-repo`
        - verified by `python scripts/Verify-ToolingConsistency.py`

        ## Installs

        ```text
        ~/.claude/
          rules/comsect1.md
          skills/comsect1-refactor/SKILL.md
          skills/comsect1-refactor/scripts/run-gates.sh
          skills/comsect1-new-project/SKILL.md
          agents/comsect1-structure/AGENT.md
          agents/comsect1-layer/AGENT.md
          agents/comsect1-risk/AGENT.md
          agents/comsect1-verify/AGENT.md
          agents/comsect1-reviewer/AGENT.md
        ```

        ## Install

        ```bash
        git clone <comsect1-architecture-repo>
        cd comsect1-architecture
        bash tooling/claude-code/install.sh
        ```

        PowerShell (Windows):

        ```powershell
        powershell -ExecutionPolicy Bypass -File tooling\\claude-code\\install.ps1
        ```

The shell and PowerShell wrappers are thin entrypoints over:

        ```text
python scripts/comsect1_ai_tooling.py install --tool claude-code
```

Default use:

- use `comsect1-refactor` for normal end-to-end work (includes analysis)
- use `comsect1-new-project` to scaffold a new IAR embedded C project
- use `comsect1-reviewer` only when you want findings-only review

The installer removes older skills (`comsect1-analyze`, `comsect1-director`,
`comsect1-execute`) as analysis is now built into `comsect1-refactor`.

        ## Verify

        In Claude Code, confirm the primary user-facing surfaces:

        1. `comsect1.md` is loaded
        2. `/comsect1-refactor` is available
        3. `comsect1-reviewer` is available

        Internal pack files may exist as provider implementation detail and do
        not need to appear as separate user-facing commands.

        ## Project-local Rule

        If a downstream project also uses `CLAUDE.md`, keep it thin:

        - point to `guides/00_AI_ENTRYPOINT.md`
        - add only project-local notes
        - do not restate canonical rules
        """
    )


def _render_common_tooling_model_block() -> str:
    return _normalize(
        """
        Generated AI tooling surfaces are synchronized by:

        ```text
        python scripts/comsect1_ai_tooling.py sync-repo
        ```

        Verify them with:

        ```text
        python scripts/Verify-ToolingConsistency.py
        ```

        The managed surface includes:

        - root adapters such as `AGENTS.md` and `CLAUDE.md`
        - minimal user-facing surfaces such as `refactor`, `analyze`, and `review`
        - provider-internal pack-aligned files that preserve the canonical taxonomy
        - install/bootstrap wrapper scripts under `tooling/`
        - tool-specific package docs under `tooling/<tool>/INSTALL.md`
        - generated blocks inside this shared packaging guide
        """
    )


def _render_common_tooling_matrix_block() -> str:
    return _normalize(
        """
        | Tool | Package doc | Installs | Project-local adapter |
        |------|-------------|----------|-----------------------|
        | Claude Code | `tooling/claude-code/INSTALL.md` | user-facing refactor/analyze/review surfaces plus internal pack-aligned files | optional thin `CLAUDE.md` |
        | Codex | `tooling/codex/INSTALL.md` | user-facing refactor/analyze/review skills | required thin `AGENTS.md` via bootstrap |
        """
    )


def _render_common_tooling_update_policy_block() -> str:
    return _normalize(
        """
        | What changed | Action needed |
        |-------------|---------------|
        | `specs/` | `git pull` only |
        | `guides/00_AI_ENTRYPOINT.md` | `git pull` only |
        | `scripts/` | `git pull` only |
        | `scripts/comsect1_ai_tooling.py` or generated AI tooling surfaces | run `python scripts/comsect1_ai_tooling.py sync-repo` and `python scripts/Verify-ToolingConsistency.py` |
        | `tooling/INSTALL.md` generated blocks | run `python scripts/comsect1_ai_tooling.py sync-repo` and `python scripts/Verify-ToolingConsistency.py` |
        | `tooling/<tool>/` templates or install scripts | re-run that tool's install/bootstrap |
        """
    )


def _render_common_tooling_install_doc() -> str:
    common_block = _render_generated_block(
        "tooling-install.common-model",
        _render_common_tooling_model_block(),
    ).rstrip("\n")
    matrix_block = _render_generated_block(
        "tooling-install.tool-matrix",
        _render_common_tooling_matrix_block(),
    ).rstrip("\n")
    update_block = _render_generated_block(
        "tooling-install.update-policy",
        _render_common_tooling_update_policy_block(),
    ).rstrip("\n")
    return _normalize(
        f"""# comsect1 AI Tooling Setup

This document is the shared packaging guide for AI-specific integrations in this
repository.

This guide is hybrid:

- manual prose explains the packaging model and project-local policy
- generated blocks below carry drift-sensitive commands, tool matrix data,
  and update rules

## Common Model

All AI packages in this repository follow the same structure:

- Shared operational entrypoint: `guides/00_AI_ENTRYPOINT.md`
- Canonical law: `specs/`
- Machine gate: `scripts/`
- Python tooling SSOT: `scripts/comsect1_ai_tooling.py`
- Root adapters stay thin
- Tool packages reference the cloned repo path and do not embed architecture
  rules

When adding or updating an AI package, change the common instruction body once
and keep tool-specific files focused on installation and invocation only.

{common_block}

## Tool Matrix

{matrix_block}

## Update Policy

{update_block}

## Project Rule Policy

Downstream `CLAUDE.md` or `AGENTS.md` files should:

- point to the shared entrypoint first
- avoid restating canonical rules
- contain only project-local additions
"""
    )


def _render_bash_python_exec(tool: str, command: str) -> str:
    return _normalize(
        f"""
        #!/usr/bin/env bash
        set -euo pipefail

        SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
        REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

        if [[ -n "${{PYTHON_BIN:-}}" ]]; then
          PYTHON_CMD=("$PYTHON_BIN")
        elif command -v python3 >/dev/null 2>&1; then
          PYTHON_CMD=("python3")
        elif command -v python >/dev/null 2>&1; then
          PYTHON_CMD=("python")
        else
          echo "Python 3 is required to run comsect1 AI tooling." >&2
          exit 2
        fi

        exec "${{PYTHON_CMD[@]}}" "$REPO_ROOT/scripts/comsect1_ai_tooling.py" {command}
        """
    )


def _render_ps_python_exec(command: str, *, include_project_root: bool = False) -> str:
    if include_project_root:
        return _normalize(
            f"""
            param(
                [string]$ProjectRoot = "."
            )

            $ErrorActionPreference = "Stop"

            $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
            $RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\\..")).Path
            $ScriptPath = Join-Path $RepoRoot "scripts\\comsect1_ai_tooling.py"

            if ($env:PYTHON_BIN) {{
                & $env:PYTHON_BIN $ScriptPath {command} --project-root $ProjectRoot
            }} elseif (Get-Command py -ErrorAction SilentlyContinue) {{
                & py -3 $ScriptPath {command} --project-root $ProjectRoot
            }} elseif (Get-Command python -ErrorAction SilentlyContinue) {{
                & python $ScriptPath {command} --project-root $ProjectRoot
            }} else {{
                throw "Python 3 is required to run comsect1 AI tooling."
            }}

            exit $LASTEXITCODE
            """
        )

    return _normalize(
        f"""
        $ErrorActionPreference = "Stop"

        $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        $RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\\..")).Path
        $ScriptPath = Join-Path $RepoRoot "scripts\\comsect1_ai_tooling.py"

        if ($env:PYTHON_BIN) {{
            & $env:PYTHON_BIN $ScriptPath {command} @args
        }} elseif (Get-Command py -ErrorAction SilentlyContinue) {{
            & py -3 $ScriptPath {command} @args
        }} elseif (Get-Command python -ErrorAction SilentlyContinue) {{
            & python $ScriptPath {command} @args
        }} else {{
            throw "Python 3 is required to run comsect1 AI tooling."
        }}

        exit $LASTEXITCODE
        """
    )


def _generated_repo_files() -> dict[str, str]:
    return {
        "AGENTS.md": _render_repo_adapter("Codex"),
        "CLAUDE.md": _render_repo_adapter("Claude"),
        "tooling/codex/templates/AGENTS.md": _render_codex_project_adapter_template(),
        "tooling/claude-code/rules/comsect1.md": _render_claude_global_rule(),
        "tooling/codex/skills/comsect1-refactor/SKILL.md": _render_codex_refactor_skill(),
        "tooling/codex/skills/comsect1-refactor/scripts/run-gates.sh": _render_run_gates_script(),
        "tooling/codex/skills/comsect1-structure/SKILL.md": _render_codex_structure_skill(),
        "tooling/codex/skills/comsect1-layer/SKILL.md": _render_codex_layer_skill(),
        "tooling/codex/skills/comsect1-risk/SKILL.md": _render_codex_risk_skill(),
        "tooling/codex/skills/comsect1-verify/SKILL.md": _render_codex_verify_skill(),
        "tooling/claude-code/skills/comsect1-refactor/SKILL.md": _render_claude_refactor_skill(),
        "tooling/claude-code/skills/comsect1-refactor/scripts/run-gates.sh": _render_run_gates_script(),
        "tooling/claude-code/skills/comsect1-new-project/SKILL.md": _render_claude_new_project_skill(),
        "tooling/codex/skills/comsect1-review/SKILL.md": _render_codex_review_skill(),
        "tooling/claude-code/agents/comsect1-reviewer/AGENT.md": _render_claude_reviewer_agent(),
        "tooling/claude-code/agents/comsect1-structure/AGENT.md": _render_claude_structure_agent(),
        "tooling/claude-code/agents/comsect1-layer/AGENT.md": _render_claude_layer_agent(),
        "tooling/claude-code/agents/comsect1-risk/AGENT.md": _render_claude_risk_agent(),
        "tooling/claude-code/agents/comsect1-verify/AGENT.md": _render_claude_verify_agent(),
        "tooling/codex/skills/comsect1-refactor/agents/openai.yaml": _render_codex_refactor_openai_yaml(),
        "tooling/codex/skills/comsect1-structure/agents/openai.yaml": _render_codex_structure_openai_yaml(),
        "tooling/codex/skills/comsect1-layer/agents/openai.yaml": _render_codex_layer_openai_yaml(),
        "tooling/codex/skills/comsect1-risk/agents/openai.yaml": _render_codex_risk_openai_yaml(),
        "tooling/codex/skills/comsect1-verify/agents/openai.yaml": _render_codex_verify_openai_yaml(),
        "tooling/codex/skills/comsect1-review/agents/openai.yaml": _render_codex_review_openai_yaml(),
        "tooling/codex/INSTALL.md": _render_codex_install_doc(),
        "tooling/claude-code/INSTALL.md": _render_claude_install_doc(),
        "tooling/codex/install.sh": _render_bash_python_exec("codex", "install --tool codex \"$@\""),
        "tooling/codex/install.ps1": _render_ps_python_exec("install --tool codex"),
        "tooling/codex/bootstrap-project.sh": _render_bash_python_exec(
            "codex",
            "bootstrap --tool codex --project-root \"${1:-.}\"",
        ),
        "tooling/codex/bootstrap-project.ps1": _render_ps_python_exec(
            "bootstrap --tool codex",
            include_project_root=True,
        ),
        "tooling/claude-code/install.sh": _render_bash_python_exec("claude-code", "install --tool claude-code \"$@\""),
        "tooling/claude-code/install.ps1": _render_ps_python_exec("install --tool claude-code"),
    }


def _generated_repo_block_files() -> dict[str, GeneratedBlockFile]:
    return {
        "tooling/INSTALL.md": GeneratedBlockFile(
            template=_render_common_tooling_install_doc(),
            blocks={
                "tooling-install.common-model": _render_common_tooling_model_block(),
                "tooling-install.tool-matrix": _render_common_tooling_matrix_block(),
                "tooling-install.update-policy": _render_common_tooling_update_policy_block(),
            },
        ),
    }


INSTALL_SPECS: dict[str, InstallSpec] = {
    "codex": InstallSpec(
        key="codex",
        display_name="Codex",
        home_env="CODEX_HOME",
        default_home=".codex",
        unit_label="skill(s)",
        entries=(
            InstallEntry(
                source_rel="tooling/codex/skills/comsect1-refactor",
                target_rel="skills/comsect1-refactor",
                kind="dir",
            ),
            InstallEntry(
                source_rel="tooling/codex/skills/comsect1-review",
                target_rel="skills/comsect1-review",
                kind="dir",
            ),
        ),
        prune_target_rels=(
            "skills/comsect1-analyze",
            "skills/comsect1-director",
            "skills/comsect1-structure",
            "skills/comsect1-layer",
            "skills/comsect1-risk",
            "skills/comsect1-verify",
            "skills/comsect1-execute",
        ),
    ),
    "claude-code": InstallSpec(
        key="claude-code",
        display_name="Claude Code",
        home_env=None,
        default_home=".claude",
        unit_label="file(s)",
        entries=(
            InstallEntry(
                source_rel="tooling/claude-code/rules/comsect1.md",
                target_rel="rules/comsect1.md",
                kind="file",
            ),
            InstallEntry(
                source_rel="tooling/claude-code/skills/comsect1-refactor/SKILL.md",
                target_rel="skills/comsect1-refactor/SKILL.md",
                kind="file",
            ),
            InstallEntry(
                source_rel="tooling/claude-code/skills/comsect1-refactor/scripts/run-gates.sh",
                target_rel="skills/comsect1-refactor/scripts/run-gates.sh",
                kind="file",
            ),
            InstallEntry(
                source_rel="tooling/claude-code/skills/comsect1-new-project/SKILL.md",
                target_rel="skills/comsect1-new-project/SKILL.md",
                kind="file",
            ),
            InstallEntry(
                source_rel="tooling/claude-code/agents/comsect1-structure/AGENT.md",
                target_rel="agents/comsect1-structure/AGENT.md",
                kind="file",
            ),
            InstallEntry(
                source_rel="tooling/claude-code/agents/comsect1-layer/AGENT.md",
                target_rel="agents/comsect1-layer/AGENT.md",
                kind="file",
            ),
            InstallEntry(
                source_rel="tooling/claude-code/agents/comsect1-risk/AGENT.md",
                target_rel="agents/comsect1-risk/AGENT.md",
                kind="file",
            ),
            InstallEntry(
                source_rel="tooling/claude-code/agents/comsect1-verify/AGENT.md",
                target_rel="agents/comsect1-verify/AGENT.md",
                kind="file",
            ),
            InstallEntry(
                source_rel="tooling/claude-code/agents/comsect1-reviewer/AGENT.md",
                target_rel="agents/comsect1-reviewer/AGENT.md",
                kind="file",
            ),
        ),
        prune_target_rels=(
            "skills/comsect1-analyze",
            "skills/comsect1-director",
            "skills/comsect1-execute",
        ),
    ),
}


def _default_home(spec: InstallSpec) -> Path:
    if spec.home_env and os.environ.get(spec.home_env):
        return Path(os.environ[spec.home_env]).expanduser().resolve()
    return (Path.home() / spec.default_home).resolve()


def _remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _backup_path(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup = path.with_name(path.name + ".bak")
    _remove_path(backup)
    if path.is_dir():
        shutil.copytree(path, backup)
        shutil.rmtree(path)
    else:
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        path.unlink()
    return backup


def _copy_file_with_replacements(source: Path, target: Path, replacements: dict[str, str]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() in TEXT_FILE_SUFFIXES:
        content = _replace_placeholders(_read_text_utf8(source), replacements)
        _write_text_utf8(target, content)
        return
    shutil.copy2(source, target)


def _copy_dir_with_replacements(source: Path, target: Path, replacements: dict[str, str]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for item in source.rglob("*"):
        relative = item.relative_to(source)
        destination = target / relative
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        _copy_file_with_replacements(item, destination, replacements)


def install_tool(tool: str, repo_root: Path, target_home: Path | None = None) -> int:
    if tool not in INSTALL_SPECS:
        raise ValueError(f"Unknown tool: {tool}")

    spec = INSTALL_SPECS[tool]
    home = target_home.resolve() if target_home else _default_home(spec)
    replacements = {PLACEHOLDER_REPO: str(repo_root)}
    installed = 0
    backed_up = 0
    pruned = 0

    print(f"comsect1 Architecture - {spec.display_name} Setup")
    print("=" * (len(spec.display_name) + 30))
    print("")
    print(f"  Repo root:  {repo_root}")
    print(f"  Target:     {home}")
    print("")

    home.mkdir(parents=True, exist_ok=True)

    for target_rel in spec.prune_target_rels:
        target = home / target_rel
        if not target.exists():
            continue
        backup = _backup_path(target)
        if backup is not None:
            print(f"  [backup]  {target} -> {backup}")
            backed_up += 1
            _remove_path(backup)
        print(f"  [remove]  {target}")
        pruned += 1

    for entry in spec.entries:
        source = repo_root / entry.source_rel
        target = home / entry.target_rel
        if not source.exists():
            raise RuntimeError(f"Missing tooling source: {source}")

        backup = _backup_path(target)
        if backup is not None:
            print(f"  [backup]  {target} -> {backup}")
            backed_up += 1

        if entry.kind == "dir":
            _copy_dir_with_replacements(source, target, replacements)
        else:
            _copy_file_with_replacements(source, target, replacements)

        print(f"  [install] {target}")
        installed += 1

        if backup is not None:
            _remove_path(backup)

    print("")
    print("Done.")
    print(f"  Installed: {installed} {spec.unit_label}")
    print(f"  Pruned:    {pruned} obsolete item(s)")
    print(f"  Backed up: {backed_up} item(s)")
    if tool == "codex":
        print("")
        print("Next steps:")
        print("  1. Restart Codex to pick up new skills.")
        print("  2. Bootstrap a target project:")
        print("     python scripts/comsect1_ai_tooling.py bootstrap --tool codex --project-root /path/to/project")
    else:
        print("")
        print(f"The installed files reference: {repo_root / 'specs'}")
        print("Run 'git pull' in the spec repo to get updates - no reinstall needed.")
    return 0


def bootstrap_codex_project(repo_root: Path, project_root: Path) -> int:
    target = project_root.resolve() / "AGENTS.md"
    replacements = {
        PLACEHOLDER_REPO: str(repo_root),
        PLACEHOLDER_PROJECT: str(project_root.resolve()),
    }
    content = _replace_placeholders(_render_codex_project_adapter_template(), replacements)

    print("comsect1 Architecture - Codex Project Bootstrap")
    print("================================================")
    print("")
    print(f"  Repo root:     {repo_root}")
    print(f"  Project root:  {project_root.resolve()}")
    print("")

    backup = _backup_path(target)
    if backup is not None:
        print(f"  [backup]  {target} -> {backup}")

    _write_text_utf8(target, content)
    print(f"  [write]   {target}")
    print("")
    print("Done.")
    print("Project AGENTS.md now points to the shared comsect1 AI entrypoint.")

    if backup is not None:
        _remove_path(backup)
    return 0


def sync_repo(repo_root: Path) -> int:
    updated = 0
    for relative_path, expected in _generated_repo_files().items():
        target = repo_root / relative_path
        current = _read_text_utf8(target) if target.exists() else None
        if current == expected:
            print(f"  [ok]     {relative_path}")
            continue
        _write_text_utf8(target, expected)
        print(f"  [write]  {relative_path}")
        updated += 1
    for relative_path, block_file in _generated_repo_block_files().items():
        target = repo_root / relative_path
        if target.exists():
            current = _read_text_utf8(target)
            try:
                expected = _apply_generated_blocks(current, block_file.blocks)
            except ValueError:
                expected = block_file.template
        else:
            current = None
            expected = block_file.template
        if current == expected:
            print(f"  [ok]     {relative_path}")
            continue
        _write_text_utf8(target, expected)
        print(f"  [write]  {relative_path}")
        updated += 1
    print("")
    print(f"Repo sync complete. Updated: {updated}")
    return 0


def verify_repo_tooling(repo_root: Path) -> list[str]:
    issues: list[str] = []
    for relative_path, expected in _generated_repo_files().items():
        target = repo_root / relative_path
        if not target.is_file():
            issues.append(f"Missing generated tooling surface: {relative_path}")
            continue
        current = _read_text_utf8(target)
        if current != expected:
            issues.append(
                f"Generated tooling drift: {relative_path} does not match "
                "scripts/comsect1_ai_tooling.py output. Run "
                "'python scripts/comsect1_ai_tooling.py sync-repo'."
            )
    for relative_path, block_file in _generated_repo_block_files().items():
        target = repo_root / relative_path
        if not target.is_file():
            issues.append(f"Missing hybrid tooling guide: {relative_path}")
            continue
        current = _read_text_utf8(target)
        for block_name, block_content in block_file.blocks.items():
            try:
                current_block = _extract_generated_block(current, block_name)
            except ValueError as exc:
                issues.append(f"{relative_path}: {exc}")
                continue
            expected_block = _render_generated_block(block_name, block_content)
            if current_block != expected_block:
                issues.append(
                    f"Generated tooling drift: {relative_path} block '{block_name}' "
                    "does not match scripts/comsect1_ai_tooling.py output. Run "
                    "'python scripts/comsect1_ai_tooling.py sync-repo'."
                )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage comsect1 AI tooling surfaces.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install a tool package to the local home directory.")
    install_parser.add_argument("--tool", required=True, choices=sorted(INSTALL_SPECS))
    install_parser.add_argument("-RepoRoot", dest="repo_root", default=None)
    install_parser.add_argument("-TargetHome", dest="target_home", default=None)

    bootstrap_parser = subparsers.add_parser("bootstrap", help="Bootstrap a downstream project adapter.")
    bootstrap_parser.add_argument("--tool", required=True, choices=("codex",))
    bootstrap_parser.add_argument("-RepoRoot", dest="repo_root", default=None)
    bootstrap_parser.add_argument("--project-root", dest="project_root", required=True)

    sync_parser = subparsers.add_parser("sync-repo", help="Rewrite generated AI tooling files in this repository.")
    sync_parser.add_argument("-RepoRoot", dest="repo_root", default=None)

    verify_parser = subparsers.add_parser("verify", help="Verify generated AI tooling files in this repository.")
    verify_parser.add_argument("-RepoRoot", dest="repo_root", default=None)

    args = parser.parse_args()
    script_path = Path(__file__).resolve()
    repo_root = resolve_repo_root(script_path, getattr(args, "repo_root", None))

    if args.command == "install":
        target_home = Path(args.target_home).expanduser() if args.target_home else None
        return install_tool(args.tool, repo_root, target_home=target_home)
    if args.command == "bootstrap":
        project_root = Path(args.project_root).expanduser().resolve()
        return bootstrap_codex_project(repo_root, project_root)
    if args.command == "sync-repo":
        return sync_repo(repo_root)
    if args.command == "verify":
        issues = verify_repo_tooling(repo_root)
        print(f"Tooling consistency verification complete.\nIssues: {len(issues)}")
        for issue in issues:
            print(f"- {issue}")
        if issues:
            print(f"\nGate FAILED -- {len(issues)} issue(s) must be resolved.")
            return 2
        print("\nGate passed -- no issues found.")
        return 0
    raise RuntimeError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
