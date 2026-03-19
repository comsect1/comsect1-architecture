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
        powershell -ExecutionPolicy Bypass -File tooling\codex\install.ps1
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
        powershell -ExecutionPolicy Bypass -File tooling\codex\bootstrap-project.ps1 -ProjectRoot C:\path\to\project
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
