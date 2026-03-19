# comsect1 Build System Guidelines

## 1. Philosophy: Build Follows Architecture

The build system should reflect the architecture's feature-centric structure and infra-integrated capability layout.

---

## 2. Include Path Strategy

Headers are distributed across feature folders and infra capability folders.

Recommended approach for production:
- explicitly list include roots (predictable dependency surface)
- explicitly list feature folders (or generate from a controlled feature list)

---

## 3. CMake Example

```cmake
cmake_minimum_required(VERSION 3.16)
project(MyComsect1Project C)

set(CMAKE_C_STANDARD 11)

# Core policy + contract
include_directories(
    codes/comsect1/project/config
    codes/comsect1/project/datastreams
    codes/comsect1/infra/bootstrap
    codes/comsect1/infra/service
    codes/comsect1/infra/platform/hal
    codes/comsect1/infra/platform/bsp
    codes/comsect1/deps/middleware
    codes/comsect1/deps/extern
)

# Feature selection
set(FEATURES heater button display)
set(PROJECT_SRCS)

foreach(feat ${FEATURES})
    include_directories(codes/comsect1/project/features/${feat})
    file(GLOB FEAT_SRCS "codes/comsect1/project/features/${feat}/*.c")
    list(APPEND PROJECT_SRCS ${FEAT_SRCS})
endforeach()

file(GLOB BOOTSTRAP_SRCS "codes/comsect1/infra/bootstrap/*.c")
file(GLOB INFRA_SRCS "codes/comsect1/infra/**/*.c")
file(GLOB EXTERN_SRCS "codes/comsect1/deps/extern/**/*.c")
file(GLOB MIDDLEWARE_SRCS "codes/comsect1/deps/middleware/**/*.c")

add_executable(${PROJECT_NAME}
    codes/main.c
    ${BOOTSTRAP_SRCS}
    ${PROJECT_SRCS}
    ${INFRA_SRCS}
    ${MIDDLEWARE_SRCS}
    ${EXTERN_SRCS}
)
```

Unit-qualified naming (Section 8.6) changes file names, not include roots.
The build still points at directories such as `/infra/bootstrap/` and `/project/config/`.

---

## 4. Unit Identity Wiring

Before compiling the first internal source file:
- define one unit token and keep it stable
- ensure `app_<unit>.h` and `cfg_project_<unit>.h` use the same `<unit>`
- update source lists, generated-code references, and include statements to the qualified file names in the same change set
- if a build file still references `cfg_project.h` or unqualified `ida_`/`prx_`/`poi_`/`cfg_`/`db_` file names, the migration is incomplete

Repo-root build files should also be reviewed for platform evidence:
- MCU/BSP macro branches
- BSP target links
- BSP/platform include paths
- dummy or fallback platform selection

---

## 5. Configuration Management

- **Core contract:** `/infra/bootstrap/cfg_core_<unit>.h`
- **Project target config:** `/project/config/cfg_project_<unit>.h`
- **Feature config/data:** `/project/features/<f>/cfg_<f>_<unit>.h`, `/project/features/<f>/db_<f>_<unit>.h`
- **Build variants:** use CMake options (for example `-DMCU_STM32=ON`) to select target-specific implementations.

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
