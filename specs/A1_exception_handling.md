# Appendix A. Exception Handling Decision Flow Template

> **Terminology:** This appendix is a reference for Section 6.4.

---

## A.0 Definition: Unrecoverable Fault

An unrecoverable fault means:

1. normal operation cannot continue safely
2. no valid business recovery path exists
3. continued execution can cause undefined behavior or hazard

Decision authority is at Idea level. PRX/POI and lower layers report conditions; Idea decides fatal transition.

---

## A.1 Exception Context Structure

```c
typedef struct {
    const char* pFile;
    uint16_t line;
    uint16_t errorCode;
    const char* pMsg;
} FatalContext_t;

const FatalContext_t* Cfg_Fatal_GetContext(void);
void Cfg_Fatal_Handle(const char* pFile, uint16_t line, uint16_t errorCode, const char* pMsg);
```

---

## A.2 Fatal Handler Implementation Sketch

```c
/* /infra/platform/bsp/bsp_fatal.c */
#include "cfg_core.h"

static FatalContext_t s_context;

void Cfg_Fatal_Handle(const char* pFile, uint16_t line, uint16_t errorCode, const char* pMsg)
{
    /* disable interrupts */
    s_context.pFile = pFile;
    s_context.line = line;
    s_context.errorCode = errorCode;
    s_context.pMsg = pMsg;

    while (1) {
        /* optional safe-state indication */
    }
}

const FatalContext_t* Cfg_Fatal_GetContext(void)
{
    return &s_context;
}
```

---

## A.3 Convenience Macro

```c
#define FATAL_ERROR(errorCode, message) \
    Cfg_Fatal_Handle(__FILE__, __LINE__, (errorCode), (message))
```

---

## A.4 Error Code Example

```c
#define ERROR_CODE_NULL_POINTER        (1001)
#define ERROR_CODE_INVALID_CONFIG      (1002)
#define ERROR_CODE_SENSOR_UNRESPONSIVE (2001)
#define ERROR_CODE_CRITICAL_TASK_FAIL  (3001)
```

---

## A.5 Architecture Notes

- Interface (`cfg_core.h`) is shared across all layers.
- Implementation belongs in platform (`bsp_`) because it controls interrupts and terminal state.
- Idea is the designated caller. PRX/POI must limit invocation to truly unrecoverable internal faults.

---

## A.6 Usage Example

```c
/* ida_motor.c */
#include "cfg_core.h"
#include "prx_motor.h"

void Ida_Motor_Init(void)
{
    const Cfg_Motor_t* cfg = Prx_Motor_GetConfig();
    if (cfg == NULL) {
        FATAL_ERROR(ERROR_CODE_INVALID_CONFIG, "Motor config is NULL");
    }
}
```

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
