# 9. Code Examples

> **Terminology:** This section uses terms defined in **Section 2.7 SSOT**.
> Examples are illustrative and non-normative.

---

## 9.0 Overview

These examples show how to apply the 3-layer feature model:

- `ida_`: intent, decision, policy, and orchestration (WHAT/WHEN/WHICH)
- `prx_`: externally-coupled interpretation
- `poi_`: mechanical execution

---

## 9.1 Basic Feature Flow (IDA -> PRX -> POI)

### 9.1.1 Idea

Idea owns the decision: whether to act, what level to apply, and when to
dispatch. It receives a domain-neutral translation from Praxis and drives
Poiesis for mechanical execution.

```c
/* ida_display.c */
#include "cfg_core.h"
#include "prx_display.h"
#include "poi_display.h"

/* ---- Policy: brightness limiting ---- */

static uint8_t Ida_Display_ClampLevel(uint8_t raw_level)
{
    if (raw_level > 10U) { return 10U; }
    return raw_level;
}

/* ---- Task entry ---- */

void Ida_Display_Main(void)
{
    DisplayCommand_t cmd;

    if (Prx_Display_DecodeFrame(&cmd) != RESULT_OK) {
        return;
    }

    if (!cmd.enable) {
        Poi_Display_WritePwm(0U);
        return;
    }

    uint8_t level = Ida_Display_ClampLevel(cmd.raw_level);
    Poi_Display_WritePwm(level);
}
```

### 9.1.2 Praxis

Praxis performs **translation only**: decode the external frame into a
domain-neutral struct. It does not decide what to do with the decoded data
(§4.1.3 PRX scope rule).

```c
/* prx_display.c */
#include "prx_display.h"
#include "stm_comm_rx.h"

Result_t Prx_Display_DecodeFrame(DisplayCommand_t* out)
{
    const CommFrame_t* frame = Stm_CommRx_Get();
    if ((frame == NULL) || (out == NULL)) {
        return RESULT_UNDEFINED;
    }

    /* External-type-coupled interpretation: frame bit semantics */
    out->enable    = ((frame->data[2] & 0x01U) != 0U);
    out->raw_level = (frame->data[3] & 0x0FU);
    return RESULT_OK;
}
```

### 9.1.3 Poiesis

Poiesis performs mechanical execution: write the PWM duty value through HAL.

```c
/* poi_display.c */
#include "poi_display.h"
#include "hal_pwm.h"
#include "cfg_display.h"

Result_t Poi_Display_WritePwm(uint8_t level)
{
    return Hal_Pwm_SetDuty(cfg_display_pwm_channel, level);
}
```

**Key observations:**
- `ida_display.c` owns the enable check, brightness clamping policy, and
  dispatch decision. A business requirement change (e.g., new clamping
  threshold) modifies `ida_` only.
- `prx_display.c` only decodes the communication frame. It does not look
  up `db_` tables or call `poi_`. It returns a domain-neutral struct.
- `poi_display.c` is a thin HAL wrapper with no domain logic.

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

### 9.3.3 Notification Model

```c
/* stm_alarm.h */
#include "cfg_core.h"

typedef void (*Stm_Alarm_Observer_t)(uint16_t alarm_code);

void Stm_Alarm_RegisterObserver(Stm_Alarm_Observer_t observer);
void Stm_Alarm_Set(uint16_t alarm_code);
```

```c
/* stm_alarm.c */
#include "stm_alarm.h"

#define STM_ALARM_MAX_OBSERVERS  4U

static Stm_Alarm_Observer_t s_observers[STM_ALARM_MAX_OBSERVERS];
static uint8_t              s_observer_count = 0U;

void Stm_Alarm_RegisterObserver(Stm_Alarm_Observer_t observer)
{
    if ((observer != NULL) && (s_observer_count < STM_ALARM_MAX_OBSERVERS)) {
        s_observers[s_observer_count] = observer;
        s_observer_count++;
    }
}

void Stm_Alarm_Set(uint16_t alarm_code)
{
    for (uint8_t i = 0U; i < s_observer_count; i++) {
        s_observers[i](alarm_code);
    }
}
```

**Key observations:**
- Observers are registered at init time (static allocation).
- Callbacks must be non-blocking — they execute in the producer's context.
- The datastream owns the observer list; no feature owns it.

### 9.3.4 Queue Model

```c
/* stm_cmd_queue.h */
#include "cfg_core.h"

#define STM_CMD_QUEUE_SIZE  8U

Result_t Stm_CmdQueue_Enqueue(const Command_t* cmd);
Result_t Stm_CmdQueue_Dequeue(Command_t* out);
```

```c
/* stm_cmd_queue.c */
#include "stm_cmd_queue.h"

static Command_t s_buffer[STM_CMD_QUEUE_SIZE];
static uint8_t   s_head  = 0U;
static uint8_t   s_tail  = 0U;
static uint8_t   s_count = 0U;

Result_t Stm_CmdQueue_Enqueue(const Command_t* cmd)
{
    if ((cmd == NULL) || (s_count >= STM_CMD_QUEUE_SIZE)) {
        return RESULT_FAIL;
    }
    s_buffer[s_tail] = *cmd;
    s_tail = (s_tail + 1U) % STM_CMD_QUEUE_SIZE;
    s_count++;
    return RESULT_OK;
}

Result_t Stm_CmdQueue_Dequeue(Command_t* out)
{
    if ((out == NULL) || (s_count == 0U)) {
        return RESULT_FAIL;
    }
    *out = s_buffer[s_head];
    s_head = (s_head + 1U) % STM_CMD_QUEUE_SIZE;
    s_count--;
    return RESULT_OK;
}
```

**Key observations:**
- Buffer is statically allocated with compile-time size.
- This example uses reject-on-full overflow policy; drop-oldest is equally valid.
- FIFO ordering is preserved. Every enqueued value must be dequeued.

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

## 9.6 Substantive Idea Pattern (State Machine + Policy + Orchestration)

This example demonstrates that Idea is typically the heaviest logic layer.
The safety monitor evaluates thresholds with hysteresis, applies policy
decisions, and orchestrates downstream actions -- all without external
dependency context.

### 9.6.1 Idea (Safety Monitor)

```c
/* ida_safety.c */
#include "cfg_core.h"
#include "poi_safety.h"

/* ---- Guard Logic ---- */

static bool Ida_Safety_IsReady(void)
{
    return (Poi_Safety_GetAdcCycleCount() >= 75U);
}

/* ---- Policy: Threshold Evaluation with Hysteresis ---- */

static uint16_t s_err_flags = 0U;

static void Ida_Safety_EvaluateTemperature(int16_t temperature)
{
    if (temperature >= 120) {
        s_err_flags |= ERR_OVERTEMP;
    }
    if (temperature <= (120 - 10)) {
        s_err_flags &= ~ERR_OVERTEMP;
    }
}

static void Ida_Safety_EvaluateVoltage(uint16_t voltage)
{
    if (voltage > 1800U) {
        s_err_flags |= ERR_OVERVOLT;
    } else if (voltage < 1700U) {
        s_err_flags &= ~ERR_OVERVOLT;
    }
}

/* ---- Orchestration ---- */

static void Ida_Safety_Run_Impl(void)
{
    int16_t temperature = Poi_Safety_ReadTemperature();
    uint16_t voltage    = Poi_Safety_ReadVoltage();

    Ida_Safety_EvaluateTemperature(temperature);
    Ida_Safety_EvaluateVoltage(voltage);

    if ((s_err_flags & ERR_OVERVOLT) != 0U) {
        Poi_Safety_DisableOutput();
    } else {
        Poi_Safety_EnableOutput();
    }

    Poi_Safety_PublishErrorFlags(s_err_flags);
}

/* ---- Task Entry ---- */

void Ida_Safety_Init(void) { s_err_flags = 0U; }

void Ida_Safety_Main(void)
{
    if (!Ida_Safety_IsReady()) { return; }
    Ida_Safety_Run_Impl();
}
```

### 9.6.2 Poiesis (Safety Accessors)

```c
/* poi_safety.c */
#include "poi_safety.h"
#include "stm_measure.h"
#include "hal_gpio.h"

uint32_t Poi_Safety_GetAdcCycleCount(void)
{
    return *Stm_Measure_GetCycleCount();
}

int16_t Poi_Safety_ReadTemperature(void)
{
    return *Stm_Measure_GetTemperature();
}

uint16_t Poi_Safety_ReadVoltage(void)
{
    return *Stm_Measure_GetVoltage();
}

void Poi_Safety_DisableOutput(void) { Hal_Gpio_SetPin(PIN_LED_EN, 0U); }
void Poi_Safety_EnableOutput(void)  { Hal_Gpio_SetPin(PIN_LED_EN, 1U); }

void Poi_Safety_PublishErrorFlags(uint16_t flags)
{
    *Stm_Safety_GetErrorFlags() = flags;
}
```

**Key observations:**
- `ida_safety.c` (~65 lines) contains all domain decisions: threshold
  values, hysteresis logic, guard conditions, orchestration order.
- `poi_safety.c` (~25 lines) contains only mechanical accessors: reading
  datastreams, toggling GPIO, publishing results.
- The Idea file is **larger** than the Poiesis file. This is the expected
  proportion in a well-structured feature.

---

## 9.7 Communication Protocol Feature (Justified PRX)

This example demonstrates a feature where Praxis is genuinely required:
the frame byte layout IS the domain model. Praxis translates the external
frame; Idea owns all post-translation decisions.

### 9.7.1 Idea

```c
/* ida_comm.c */
#include "cfg_core.h"
#include "prx_comm.h"
#include "poi_comm.h"

static uint8_t s_retry_count = 0U;

void Ida_Comm_Main(void)
{
    CommCommand_t cmd;
    Result_t result = Prx_Comm_DecodeFrame(&cmd);

    if (result != RESULT_OK) {
        s_retry_count++;
        if (s_retry_count >= 3U) {
            Poi_Comm_ReportError(result);
            s_retry_count = 0U;
        }
        return;
    }

    s_retry_count = 0U;

    /* Policy: command routing */
    switch (cmd.type) {
        case CMD_SET_MODE:
            Poi_Comm_ApplyMode(cmd.payload);
            break;
        case CMD_REQUEST_STATUS:
            Poi_Comm_SendStatus();
            break;
        default:
            break;
    }
}
```

### 9.7.2 Praxis (Translation Only)

```c
/* prx_comm.c */
#include "prx_comm.h"
#include "stm_comm_rx.h"

Result_t Prx_Comm_DecodeFrame(CommCommand_t* out)
{
    const CommFrame_t* frame = Stm_CommRx_Get();
    if (frame == NULL || out == NULL) { return RESULT_UNDEFINED; }

    /* External-type-coupled: byte layout is the protocol definition */
    if ((frame->data[0] & 0x80U) == 0U) { return RESULT_FAIL; }

    out->type    = (CommCmdType_t)(frame->data[1] & 0x0FU);
    out->payload = frame->data[2];
    return RESULT_OK;
}
```

### 9.7.3 Poiesis

```c
/* poi_comm.c */
#include "poi_comm.h"
#include "hal_uart.h"
#include "stm_comm_tx.h"

void Poi_Comm_ApplyMode(uint8_t mode)   { Hal_Uart_Send(&mode, 1U); }
void Poi_Comm_SendStatus(void)          { Hal_Uart_Send(Stm_CommTx_Get(), 4U); }
void Poi_Comm_ReportError(Result_t err) { Hal_Uart_Send((uint8_t*)&err, 1U); }
```

**Key observations:**
- `ida_comm.c` (~35 lines) owns retry policy, command routing, error
  escalation — all domain decisions.
- `prx_comm.c` (~15 lines) only decodes the frame. It does NOT dispatch
  or decide what to do with the decoded command.
- `poi_comm.c` (~5 lines) is a thin UART wrapper.
- Praxis is justified: the frame bit layout is inseparable from the
  protocol interpretation (Q3=Yes in the discriminator).

---

## 9.8 Timer Feature (IDA + POI Only, No PRX)

When no external-type-coupled interpretation exists, Idea and Poiesis
suffice. This is the most common pattern.

### 9.8.1 Idea

```c
/* ida_heartbeat.c */
#include "cfg_core.h"
#include "poi_heartbeat.h"

static uint32_t s_tick_count = 0U;
static bool     s_led_on     = false;

void Ida_Heartbeat_Main(void)
{
    uint32_t elapsed = Poi_Heartbeat_GetElapsedMs();
    s_tick_count += elapsed;

    if (s_tick_count >= 500U) {
        s_led_on = !s_led_on;
        Poi_Heartbeat_SetLed(s_led_on);
        s_tick_count = 0U;
    }
}
```

### 9.8.2 Poiesis

```c
/* poi_heartbeat.c */
#include "poi_heartbeat.h"
#include "hal_gpio.h"
#include "mdw_timer.h"

uint32_t Poi_Heartbeat_GetElapsedMs(void) { return Mdw_Timer_GetElapsed(); }
void     Poi_Heartbeat_SetLed(bool on)    { Hal_Gpio_SetPin(PIN_LED, on ? 1U : 0U); }
```

**Key observations:**
- No Praxis needed: the timer value is a plain integer (Q1=Yes, Q2=Yes →
  judgment to Idea, wrapping to Poiesis).
- `ida_` owns the 500ms toggle policy. Changing the interval modifies
  `ida_` only.
- `poi_` is two lines of mechanical wrapping.

---

## 9.9 OOP Example: Static Utility Idea (C#)

OOP Idea as a static utility class (A2.5.1 form a), the preferred default.

```csharp
/* ida_ColorConversion.cs */
public static class ida_ColorConversion
{
    public static string ClassifyMood(int r, int g, int b)
    {
        double saturation = ComputeSaturation(r, g, b);
        if (saturation < 0.20) return "neutral";
        if (r > g && r > b)    return "warm";
        return "cool";
    }

    private static double ComputeSaturation(int r, int g, int b)
    {
        int max = Math.Max(r, Math.Max(g, b));
        int min = Math.Min(r, Math.Min(g, b));
        return max == 0 ? 0.0 : (double)(max - min) / max;
    }
}

/* poi_ColorSensor.cs */
public class poi_ColorSensor
{
    private readonly IColorDevice _device;
    public poi_ColorSensor(IColorDevice device) { _device = device; }

    public (int R, int G, int B) ReadColor()
    {
        return _device.GetRGB();
    }
}
```

**Key observations:**
- `ida_ColorConversion` is a static class with no mutable state (A2.5.1).
- All domain logic (saturation computation, mood classification) is in Idea.
- `poi_ColorSensor` wraps the external device — pure mechanical access.
- No `prx_` needed: the color values are primitives that Idea can consume
  directly (Q1=Yes, Q2=Yes).

---

## 9.10 Anti-example Quick Check

- `ida_` including `hal_*.h`: forbidden
- `poi_` decoding protocol bits into business meaning: wrong role (move to `prx_`)
- `prx_` only forwarding a call unchanged: likely POI candidate

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
