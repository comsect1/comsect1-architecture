# 9. Code Examples

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.
> Examples are illustrative and non-normative.

---

## 9.0 Overview

These examples show how to apply the 3-layer feature model:

- `ida_`: intent and decision (WHAT/WHEN)
- `prx_`: externally-coupled interpretation
- `poi_`: mechanical execution

---

## 9.1 Basic Feature Flow (IDA -> PRX -> POI)

### 9.1.1 Idea

```c
/* ida_display.c */
#include "cfg_core.h"
#include "prx_display.h"

void Ida_Display_Main(void)
{
    DisplayCommand_t cmd;

    if (Prx_Display_GetPendingCommand(&cmd) != RESULT_OK) {
        return;
    }

    if (cmd.enable) {
        Prx_Display_ApplyCommand(&cmd);
    }
}
```

### 9.1.2 Praxis

```c
/* prx_display.c */
#include "prx_display.h"
#include "poi_display.h"
#include "db_display.h"
#include "stm_lin_rx.h"

Result_t Prx_Display_GetPendingCommand(DisplayCommand_t* out)
{
    const LinFrame_t* frame = Stm_LinRx_Get();
    if ((frame == NULL) || (out == NULL)) {
        return RESULT_UNDEFINED;
    }

    /* External-type-coupled interpretation: frame bit semantics */
    out->enable = ((frame->data[2] & 0x01U) != 0U);
    out->level = db_display_level_map[frame->data[3] & 0x0FU];
    return RESULT_OK;
}

Result_t Prx_Display_ApplyCommand(const DisplayCommand_t* cmd)
{
    return Poi_Display_WritePwm(cmd->level);
}
```

### 9.1.3 Poiesis

```c
/* poi_display.c */
#include "poi_display.h"
#include "hal_pwm.h"
#include "cfg_display.h"

Result_t Poi_Display_WritePwm(uint16_t level)
{
    return Hal_Pwm_SetDuty(cfg_display_pwm_channel, level);
}
```

---

## 9.2 IDA -> POI Direct Pattern (No PRX Needed)

When no external-type-coupled interpretation exists, Idea may call Poiesis directly.

```c
/* ida_buzzer.c */
#include "poi_buzzer.h"

void Ida_Buzzer_Notify(void)
{
    Poi_Buzzer_PlayTone(1000U, 120U);
}
```

```c
/* poi_buzzer.c */
#include "poi_buzzer.h"
#include "hal_timer.h"

void Poi_Buzzer_PlayTone(uint16_t freq_hz, uint16_t duration_ms)
{
    Hal_Timer_StartTone(freq_hz, duration_ms);
}
```

---

## 9.3 Inter-Feature Communication via Datastream (`stm_`)

### 9.3.1 Producer Feature

```c
/* poi_sensor.c */
#include "stm_temp.h"

void Poi_Sensor_PublishTemp(uint16_t value)
{
    *Stm_Temp_Stream(NULL) = value;
}
```

### 9.3.2 Consumer Feature

```c
/* prx_heater.c */
#include "stm_temp.h"

uint16_t Prx_Heater_ReadExternalTemp(void)
{
    return *Stm_Temp_Stream(NULL);
}
```

No direct include of another feature's `ida_`/`prx_`/`poi_` is allowed.

---

## 9.4 Core Registration Pattern (`ida_core` + `poi_core`)

```c
/* ida_core.c */
#include "cfg_core.h"
#include "poi_core.h"
#include "ida_display.h"
#include "ida_heater.h"

void Ida_Core_Entry(void)
{
    Poi_Core_Init();
    Poi_Core_Register(Ida_Display_GetInterface());
    Poi_Core_Register(Ida_Heater_GetInterface());
    Poi_Core_Start();
}
```

```c
/* poi_core.c */
#include "poi_core.h"
#include "mdw_scheduler.h"

void Poi_Core_Register(const Ida_Interface_t* idea)
{
    Mdw_Scheduler_CreateTask(idea->name, idea->main);
}
```

---

## 9.5 Error Propagation Pattern

```c
/* poi_storage.c */
Result_t Poi_Storage_Read(uint16_t id, uint8_t* out)
{
    return Hal_Eeprom_Read(id, out);
}

/* ida_storage.c */
void Ida_Storage_Load(void)
{
    uint8_t data;
    if (Poi_Storage_Read(BOOT_CONFIG_ID, &data) != RESULT_OK) {
        FATAL_ERROR(ERROR_CODE_INVALID_CONFIG, "Boot config read failed");
    }
}
```

---

## 9.6 Anti-example Quick Check

- `ida_` including `hal_*.h`: forbidden
- `poi_` decoding protocol bits into business meaning: wrong role (move to `prx_`)
- `prx_` only forwarding a call unchanged: likely POI candidate

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
