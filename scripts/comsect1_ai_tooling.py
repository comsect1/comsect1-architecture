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


def _render_codex_analyze_skill() -> str:
    return _normalize(
        """
        ---
        name: comsect1-analyze
        description: Analyze and design code or specifications according to comsect1 architecture. Use when starting new design work, refactoring legacy code, classifying files into ida_/prx_/poi_, or planning a comsect1 migration.
        ---

        # comsect1 Analyze

        ## Step 0: Load the Canonical Workflow

        Read the canonical source list defined in:
        `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_07_Analysis_Procedure.md`

        Do not restate rules from memory. Cite the file that governs each conclusion.

        ## Procedure

        Follow the canonical 8-step procedure defined in:
        `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_07_Analysis_Procedure.md`

        Read that guide before starting the analysis. Perform each step in order and
        report findings as you go.

        ## Report format

        Read the canonical report format guide before generating the report:
        `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_06_Analysis_Report_Format.md`

        Write the report to **`.comsect1-analysis.md`** at the target root AND display
        in conversation. The guide defines the exact format. Do not improvise.
        """
    )


def _render_claude_analyze_skill() -> str:
    return _normalize(
        """
        ---
        name: comsect1-analyze
        description: Analyze and design code according to comsect1 architecture. Use when starting refactoring or new design work on any codebase.
        argument-hint: "[target-path or feature-name]"
        disable-model-invocation: true
        ---

        # comsect1 Architecture Analysis

        You are performing an architectural analysis of the target codebase according to
        the comsect1 architecture specification.

        ## Step 0: Read the Canonical Sources

        Before doing anything, read the canonical source list defined in:
        `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_07_Analysis_Procedure.md`

        All prefix definitions, layer roles, discriminator logic, and dependency rules
        come from the canonical specs. Do NOT use hardcoded rules. Read the spec every
        time.

        ## Target

        Analyze: `$ARGUMENTS`

        ## Project context

        Current files: !`git ls-files --others --cached --exclude-standard 2>/dev/null | head -80`

        ## Analysis procedure

        Follow the canonical 8-step procedure defined in:
        `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_07_Analysis_Procedure.md`

        Read that guide before starting the analysis. Perform each step in order and
        report findings as you go.

        ## Report format

        Read the canonical report format guide before generating the report:
        `{{COMSECT1_ROOT}}/guides/02_Execution_Guides/EG_06_Analysis_Report_Format.md`

        Write the report to **`.comsect1-analysis.md`** at the target root AND display
        in conversation. The guide defines the exact format. Do not improvise.
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


def _render_codex_analyze_openai_yaml() -> str:
    return _normalize(
        """
        interface:
          display_name: "comsect1 Analyze"
          short_description: "Analyze codebases for comsect1 architecture"
          default_prompt: "Use $comsect1-analyze to analyze this codebase for comsect1 layer placement, dependency rules, and gate readiness."
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
          comsect1-analyze/
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

        1. Codex lists `comsect1-analyze`
        2. Codex lists `comsect1-review`
        3. the target project has a thin `AGENTS.md`

        Restart Codex after installing skills so new skills are picked up.
        In Codex, these are skills invoked with `$...`, not slash commands.
        Check the `$` skill picker after a full Codex restart.

        Explicit invocation examples:

        ```text
        $comsect1-analyze analyze codes/comsect1 against the comsect1 architecture rules.
        $comsect1-review review this change for comsect1 compliance.
        ```

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
          agents/comsect1-reviewer/AGENT.md
          skills/comsect1-analyze/SKILL.md
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

        ## Verify

        In Claude Code, confirm:

        1. `comsect1.md` is loaded
        2. `comsect1-reviewer` is available
        3. `/comsect1-analyze` is available

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
        - tool-specific skills, reviewers, and rules files
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
        | Claude Code | `tooling/claude-code/INSTALL.md` | global rule + reviewer + analyze skill | optional thin `CLAUDE.md` |
        | Codex | `tooling/codex/INSTALL.md` | analyze skill + review skill | required thin `AGENTS.md` via bootstrap |
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
        "tooling/codex/skills/comsect1-analyze/SKILL.md": _render_codex_analyze_skill(),
        "tooling/claude-code/skills/comsect1-analyze/SKILL.md": _render_claude_analyze_skill(),
        "tooling/codex/skills/comsect1-review/SKILL.md": _render_codex_review_skill(),
        "tooling/claude-code/agents/comsect1-reviewer/AGENT.md": _render_claude_reviewer_agent(),
        "tooling/codex/skills/comsect1-analyze/agents/openai.yaml": _render_codex_analyze_openai_yaml(),
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
                source_rel="tooling/codex/skills/comsect1-analyze",
                target_rel="skills/comsect1-analyze",
                kind="dir",
            ),
            InstallEntry(
                source_rel="tooling/codex/skills/comsect1-review",
                target_rel="skills/comsect1-review",
                kind="dir",
            ),
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
                source_rel="tooling/claude-code/agents/comsect1-reviewer/AGENT.md",
                target_rel="agents/comsect1-reviewer/AGENT.md",
                kind="file",
            ),
            InstallEntry(
                source_rel="tooling/claude-code/skills/comsect1-analyze/SKILL.md",
                target_rel="skills/comsect1-analyze/SKILL.md",
                kind="file",
            ),
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

    print(f"comsect1 Architecture - {spec.display_name} Setup")
    print("=" * (len(spec.display_name) + 30))
    print("")
    print(f"  Repo root:  {repo_root}")
    print(f"  Target:     {home}")
    print("")

    home.mkdir(parents=True, exist_ok=True)

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
