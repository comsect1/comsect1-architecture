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
python {{COMSECT1_ROOT}}/scripts/New-Comsect1Scaffold.py \
    -Path {{PROJECT_ROOT}}/codes/comsect1 \
    -Unit <unit> -MCU <mcu> \
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
