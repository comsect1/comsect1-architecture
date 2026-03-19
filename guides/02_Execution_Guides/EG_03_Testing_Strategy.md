# comsect1 Testing Strategy: Fractal Approach

## 1. Core Insight

comsect1 testing is fractal: the same role-based strategy repeats at every scale.

Architecture roles are now:
- Idea (`ida_`): intent logic
- Praxis (`prx_`): externally-coupled interpretation
- Poiesis (`poi_`): mechanical execution

---

## 2. Universal Testing Pattern

### 2.1 Testing Idea (Logic Unit Test)

- Target: `ida_*.c`
- Environment: host PC
- Method:
  1. compile Idea
  2. mock own `prx_`/`poi_` interfaces
  3. verify business decisions and state transitions

### 2.2 Testing Praxis (Interpretation Integration Test)

- Target: `prx_*.c`
- Environment: target hardware or high-fidelity simulator
- Method:
  1. feed external-type/protocol shaped inputs
  2. verify interpretation result and downstream calls (`poi_`, `mdw_`, `svc_`)

### 2.3 Testing Poiesis (Execution Integration Test)

- Target: `poi_*.c`
- Environment: target hardware or simulator
- Method:
  1. call POI interfaces directly
  2. verify HAL/OS/module side effects
  3. verify wrappers/bridges are deterministic and decision-free

---

## 3. Applying the Strategy

### 3.1 Feature Level

- Idea test: mock `prx_`/`poi_` and verify decision outputs.
- Praxis test: validate protocol/type interpretation and mapping.
- Poiesis test: validate hardware/API forwarding behavior.

### 3.2 Middleware/Internal Modules

For complex middleware, apply the same split internally (logic vs interpretation vs execution) where beneficial.

### 3.3 HAL/BSP

Keep logic-like behavior testable separately from direct pin/register manipulation.

---

## 4. Summary

| Component | Role | Environment | Dependency Style |
|-----------|------|-------------|------------------|
| Idea | business logic | host PC | mocked PRX/POI |
| Praxis | external interpretation | target/sim | real or simulated module inputs |
| Poiesis | execution bridge | target/sim | real HAL/OS/modules |

If it is intent logic, test it as Idea. If it is type-coupled interpretation, test it as Praxis. If it is mechanical forwarding, test it as Poiesis.

---

## 5. Concrete Test Patterns

### 5.1 Idea: Pure Decision Test (Host PC)

Idea files contain no external dependencies. Test them as pure functions with
mocked layer interfaces.

```c
/* test_ida_sensor.c — host PC unit test */

/* Stub: replace real poi_sensor with recording stub */
static int last_alarm_level = -1;
void Poi_Sensor_SetAlarm(int level) { last_alarm_level = level; }

/* Stub: replace real prx_sensor with controlled input */
static int fake_temperature = 25;
int Prx_Sensor_ReadTemperature(void) { return fake_temperature; }

void test_ida_sensor_triggers_alarm_above_threshold(void) {
    fake_temperature = 85;
    Ida_Sensor_Evaluate();          /* call the Idea entry point */
    assert(last_alarm_level == 2);  /* verify the business decision */
}

void test_ida_sensor_no_alarm_below_threshold(void) {
    fake_temperature = 40;
    Ida_Sensor_Evaluate();
    assert(last_alarm_level == 0);
}
```

Key properties:
- No HAL/BSP/OS headers included.
- Stubs implement only the function signatures that `ida_sensor.c` calls.
- Assertions target **decisions** (alarm level), not mechanism.

### 5.2 Praxis: Type-Translation Test (Target or Simulator)

Praxis tests verify that external protocol types are correctly translated
into domain-neutral values.

```c
/* test_prx_comm.c — target/simulator integration test */
#include "prx_comm.h"
#include <string.h>

void test_prx_comm_decodes_valid_frame(void) {
    /* Arrange: build a raw protocol frame (external type) */
    uint8_t raw_frame[] = { 0xAA, 0x03, 0x01, 0x02, 0x03, 0x55 };

    /* Act: Praxis translates to domain struct */
    CommPayload_t payload;
    bool ok = Prx_Comm_Decode(raw_frame, sizeof(raw_frame), &payload);

    /* Assert: domain-neutral output, no protocol types leak */
    assert(ok == true);
    assert(payload.command == 1);
    assert(payload.data_len == 2);
}

void test_prx_comm_rejects_bad_checksum(void) {
    uint8_t bad_frame[] = { 0xAA, 0x03, 0x01, 0x02, 0xFF, 0x55 };
    CommPayload_t payload;
    bool ok = Prx_Comm_Decode(bad_frame, sizeof(bad_frame), &payload);
    assert(ok == false);
}
```

Key properties:
- Input is shaped like the external protocol (raw bytes, vendor structs).
- Output is the domain-neutral struct that Idea will consume.
- No Idea logic tested here — only translation correctness.

### 5.3 Poiesis: Forwarding Verification Test (Target or Simulator)

Poiesis tests confirm that mechanical forwarding is deterministic and
decision-free.

```c
/* test_poi_storage.c — target integration test */
#include "poi_storage.h"

void test_poi_storage_write_forwards_to_hal(void) {
    uint8_t data[] = { 0x10, 0x20 };

    /* Act: Poiesis forwards to HAL */
    Poi_Storage_Write(0x1000, data, sizeof(data));

    /* Assert: HAL received exact parameters (via HAL test spy) */
    assert(hal_flash_spy_last_addr == 0x1000);
    assert(hal_flash_spy_last_len  == 2);
    assert(memcmp(hal_flash_spy_last_data, data, 2) == 0);
}
```

Key properties:
- No conditionals in the test target (if poi_ has conditionals, it is a
  red flag — see §10 Fat Poiesis).
- Assertions verify pass-through fidelity, not business outcomes.

### 5.4 Datastream: Producer/Consumer Integration Test

Datastream tests verify cross-feature data flow without direct feature
coupling.

```c
/* test_stm_temperature.c — integration test */
#include "stm_temperature.h"

void test_datastream_producer_consumer_roundtrip(void) {
    /* Producer side (typically in poi_sensor or prx_sensor) */
    Stm_Temperature_t temp = { .celsius = 72, .valid = true };
    Stm_Temperature_Set(&temp);

    /* Consumer side (typically in poi_display or prx_display) */
    const Stm_Temperature_t* read = Stm_Temperature_Get();
    assert(read->celsius == 72);
    assert(read->valid   == true);
}

void test_datastream_notification_fires_on_set(void) {
    static bool callback_fired = false;
    static Stm_Temperature_t received;

    Stm_Temperature_RegisterObserver(
        &(StmObserver_t){ .callback = on_temp_change }
    );

    Stm_Temperature_t temp = { .celsius = 55, .valid = true };
    Stm_Temperature_Set(&temp);

    assert(callback_fired == true);
    assert(received.celsius == 55);
}
```

Key properties:
- Producer and consumer are tested through the `stm_` interface only.
- No direct feature-to-feature include.
- Notification model tests verify observer registration and callback
  invocation.

---

## 6. Gate Integration in CI/CD

### 6.1 Pipeline Placement

```text
Build -> Unit Tests (Idea) -> Gate -> Integration Tests (PRX/POI) -> Deploy
                                 |
                          Verify-Comsect1Code.py
                          Verify-Spec.py
```

Gate runs **after** Idea unit tests and **before** integration tests. This
ensures architectural compliance before investing in hardware-coupled test
execution.

### 6.2 CI Configuration Example

```yaml
# .github/workflows/comsect1-gate.yml (or equivalent)
gate:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: python scripts/Verify-Spec.py
    - run: python scripts/Verify-Comsect1Code.py -Root codes/comsect1
    - run: |
        # Fail the pipeline on any gate error
        python scripts/Verify-AIADGate.py \
          -CodeRoot codes/comsect1 \
          -ReportPath .aiad-gate-report.json
```

### 6.3 Gate Failure Policy

- **Error findings**: Pipeline must fail. No merge permitted.
- **Advisory findings**: Pipeline passes. Advisories are logged for review
  but do not block merges.
- Gate report (`.aiad-gate-report.json`) is archived as a build artifact for
  traceability.

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
