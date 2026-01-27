# 6. Error Handling and Return Types

> **Terminology:** This section uses terms from **Section 2.7 SSOT**.

---

## 6.0 Philosophy

Error handling is architectural, not optional implementation detail.

- every fallible operation returns explicit status
- lower layers report; upper layers decide recovery
- no silent swallow of failures

---

## 6.1 Standard Return Type

Use a common result enum in `cfg_core.h`:

```c
typedef enum {
    RESULT_OK = 0,
    RESULT_FAIL,
    RESULT_UNSUPPORTED,
    RESULT_UNDEFINED,
} Result_t;
```

---

## 6.2 Data Return Pattern

Return status via `Result_t`; return payload through output pointers.

```c
Result_t Poi_Sensor_ReadValue(uint16_t* pValue)
{
    if (pValue == NULL) {
        return RESULT_UNDEFINED;
    }

    uint8_t raw = Hal_I2c_ReadRegister(SENSOR_I2C_ADDR, 0x1A);
    if (raw == 0xFF) {
        return RESULT_FAIL;
    }

    *pValue = (uint16_t)raw;
    return RESULT_OK;
}
```

---

## 6.3 Error Propagation

Errors propagate upward by role:

```
HAL/BSP: detects low-level fault
PRX/POI: translate to architectural error
IDA: decide retry/fallback/safe-state
```

This preserves role boundaries:
- PRX/POI interpret and execute
- IDA decides business response

---

## 6.4 Fatal Handling

Unrecoverable faults transition to terminal safe state through a fatal handler.

Recommended policy:
- recoverable: return `Result_t` and propagate
- unrecoverable: trigger `FATAL_ERROR(...)` through contract-defined mechanism

Fatal handling must:
- disable interrupts
- record context (file, line, code, message)
- enter non-returning safe loop

See `specs/A1_exception_handling.md` for reference template.

---

## 6.5 Completeness Requirement

A complete module:
- validates inputs
- handles edge cases internally
- returns structured status to caller
- does not leak internal state management burden

Incomplete modules force callers to patch hidden failure paths and break architecture completeness.

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
