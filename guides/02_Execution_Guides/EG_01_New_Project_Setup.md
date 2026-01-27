# comsect1 New Project Guide

Step-by-step guide for creating a new project with the 3-layer model (`ida_`/`prx_`/`poi_`).

---

## 1. Introduction

### 1.1 When to Use comsect1

Use comsect1 when you need:
- long-term maintainability
- clear responsibility boundaries
- strict dependency control
- reusable modules with isolated adaptation code

### 1.2 Core Premise

- Idea defines contract intent.
- Praxis interprets externally-coupled meaning.
- Poiesis executes mechanically.

### 1.3 Hardware Independence (Correct Scope)

Idea is independent from implementation details (HAL/BSP), not from realizable hardware structure.

---

## 2. Project Setup

### 2.1 Folder Structure

```text
/MyProject
  /codes/comsect1
    /project
      /config
        cfg_project.h
      /datastreams
        stm_project_state.h
      /features
        /heater
          ida_heater.c/h
          prx_heater.c/h
          poi_heater.c/h
          cfg_heater.h
          db_heater.h
        /button
          ida_button.c/h
          poi_button.c/h
    /infra
      /bootstrap
        ida_core.c/h
        poi_core.c/h
        cfg_core.h
      /service
      /platform
        /hal
        /bsp
    /deps
      /extern
      /middleware
  main.c
```

### 2.2 Naming Rules

- Idea: `ida_<feature>.c/h`
- Praxis: `prx_<feature>.c/h` (only when discriminator says PRX)
- Poiesis: `poi_<feature>.c/h`
- Datastream: `stm_<name>.h`
- Resources: `cfg_*.h`, `db_*.h`

### 2.3 Core Contract (`cfg_core.h`)

Define shared contract vocabulary here:
- `Result_t`
- `Ida_Interface_t`
- project contract enums (e.g., `Ida_Id_t`)

Do not put target hardware config here.

### 2.4 Build System

CMake skeleton:

```cmake
cmake_minimum_required(VERSION 3.16)
project(MyComsect1Project C)

set(CMAKE_C_STANDARD 11)

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

set(FEATURES heater button)
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

## 3. Layer-by-Layer Implementation Guide

### 3.1 Step 1: Write Idea First

Idea file should answer WHAT/WHEN only.

Checklist:
- business decision is visible
- no direct module/resource/platform include
- only own `prx_`/`poi_` + `cfg_core.h`

### 3.2 Step 2: Apply 3-Question Discriminator

For each external interaction:
1. external dependency needed?
2. separable judgment exists?
3. inseparable external-type-coupled judgment exists?

Placement outcome:
- separable decision -> Idea
- inseparable interpretation -> Praxis
- otherwise -> Poiesis

### 3.3 Step 3: Implement Praxis (if needed)

Praxis responsibilities:
- protocol/frame/type interpretation with domain meaning
- map interpreted meaning into POI calls or module calls

### 3.4 Step 4: Implement Poiesis

Poiesis responsibilities:
- OS/HAL wrappers
- mechanical bridging
- deterministic forwarding

No domain decisions in POI.

### 3.5 Step 5: Wire Core

`ida_core`:
- select features
- order init/register/start

`poi_core`:
- run scheduler/OS integration
- register interface objects

---

## 4. Practical Example: Button Controls Heater

### 4.1 Idea

```c
/* ida_heater.c */
void Ida_Heater_Control(void)
{
    if (Ida_Heater_ShouldEnable()) {
        Poi_Heater_SetOutput(true);
    } else {
        Poi_Heater_SetOutput(false);
    }
}
```

### 4.2 Praxis (when protocol interpretation exists)

```c
/* prx_button.c */
ButtonEvent_t Prx_Button_ParseFrame(const uint8_t* frame)
{
    if ((frame[2] & 0x03U) == 0x01U) {
        return BUTTON_EVENT_CLICK;
    }
    return BUTTON_EVENT_NONE;
}
```

### 4.3 Poiesis

```c
/* poi_heater.c */
Result_t Poi_Heater_SetOutput(bool on)
{
    return Hal_Gpio_Write(HEATER_PIN, on ? GPIO_HIGH : GPIO_LOW);
}
```

---

## 5. Common Pitfalls and Solutions

### 5.1 Empty Idea

Symptom:
- Idea is only thin pass-through

Fix:
- move decision logic back to `ida_`

### 5.2 Fat Praxis

Symptom:
- PRX files are mostly wrappers

Fix:
- move mechanical wrappers to `poi_`

### 5.3 Fat Poiesis

Symptom:
- POI contains protocol/domain interpretation

Fix:
- split interpretation into `prx_` or `ida_`

### 5.4 Cross-feature Includes

Symptom:
- feature includes other feature headers

Fix:
- publish/read via `stm_`

---

## 6. Completion Checklist

- [ ] Feature has `ida_` and `poi_`; `prx_` only when discriminator requires
- [ ] `ida_` has no direct module/resource/platform include
- [ ] `prx_`/`poi_` do not include other feature headers
- [ ] cross-feature communication uses `stm_`
- [ ] `ida_core` is only file including feature `ida_*.h`
- [ ] build and architecture verification pass

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
