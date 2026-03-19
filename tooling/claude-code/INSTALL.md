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
        powershell -ExecutionPolicy Bypass -File tooling\claude-code\install.ps1
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
