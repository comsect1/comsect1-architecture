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

---

## 4. Configuration Management

- **Core contract:** `/infra/bootstrap/cfg_core.h`
- **Project target config:** `/project/config/cfg_project.h`
- **Feature config/data:** `/project/features/<f>/cfg_<f>.h`, `/project/features/<f>/db_<f>.h`
- **Build variants:** use CMake options (for example `-DMCU_STM32=ON`) to select target-specific implementations.

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.0**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

You are free to:
- **Share** - copy and redistribute the material in any medium or format for non-commercial purposes only.

Under the following terms:
- **Attribution** - You must give appropriate credit to the author (Kim Hyeongjeong), provide a reference to the license, and indicate if changes were made.
- **NonCommercial** - You may not use the material for commercial purposes.
- **NoDerivatives** - If you remix, transform, or build upon the material, you may not distribute the modified material.

No additional restrictions - You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
