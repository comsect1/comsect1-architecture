# DP-03: When to Use Praxis (prx_)

> **Purpose**: Clarify the justification bar for the Praxis layer. Praxis is the most frequently misused layer because its definition — "inseparable domain judgment coupled to external types" — is abstract. This guide provides concrete decision criteria.

---

## 1. The Default: ida_ + poi_

In most features, two layers suffice:

- **ida_**: Pure domain decisions (WHAT/WHEN)
- **poi_**: Mechanical wrapping of external APIs (HOW, no domain judgment)

The boundary between them is an interface owned by ida_ and implemented by poi_.

**Praxis is the exception, not the rule.** It exists only when a domain judgment cannot be separated from the external type it operates on.

---

## 2. The 3-Question Discriminator (Review)

From §4.3:

1. **External dependency required?** No → `ida_`. Yes → Q2.
2. **Separable domain judgment?** Yes → split `ida_` (judgment) + `poi_` (wrapping). No → Q3.
3. **Inseparable domain judgment coupled to external types?** Yes → `prx_`. No → `poi_`.

The critical question is Q2: "Can the domain judgment be expressed without referencing external types?"

---

## 3. Decision Examples

### Example 1: Color Conversion (ida_ + poi_)

**Scenario**: Feature converts RGB to HSV for mood lamp color selection.

- **Domain judgment**: "If saturation < 20%, classify as 'neutral' mood" → this is pure domain logic
- **External dependency**: A graphics library provides `Color` struct

**Decision**: The mood classification can be expressed with primitive values (R, G, B as integers). The `Color` struct is not needed for the judgment itself.

```
ida_moodlamp.c  →  "classify_mood(uint8_t r, uint8_t g, uint8_t b)"
poi_moodlamp.c  →  "extract RGB from Color struct, call ida_ classify"
```

**Discriminator path**: Q1=Yes → Q2=Yes (separable) → ida_ + poi_

---

### Example 2: LIN Protocol Interpretation (prx_)

**Scenario**: Feature interprets LIN bus frames where the protocol byte layout IS the domain model.

- **Domain judgment**: "If frame ID 0x3A byte[2] bit 5 is set, ambient light mode is active"
- **External dependency**: LIN middleware provides `Lin_Frame_t` with byte array

**Decision**: The domain meaning is embedded in the bit-level structure of the external frame type. Separating the judgment from the frame type would require duplicating the frame structure in ida_, which defeats the purpose.

```
prx_lin_ambient.c  →  "interpret Lin_Frame_t byte[2] bit 5 as ambient mode"
```

**Discriminator path**: Q1=Yes → Q2=No (bit-level coupling) → Q3=Yes → prx_

---

### Example 3: Database Parameter Storage (poi_)

**Scenario**: Feature stores calibration parameters to NVM via middleware.

- **Domain judgment**: None — storage is purely mechanical
- **External dependency**: Storage middleware provides `Mdw_Storage_Write()`

**Decision**: No domain interpretation happens during storage. This is pure wrapping.

```
poi_calibration.c  →  "call Mdw_Storage_Write with address and data"
```

**Discriminator path**: Q1=Yes → Q2=No judgment at all → Q3=No → poi_

---

### Example 4: Serial Port Communication (prx_ in C/embedded, ida_+poi_ in OOP)

**Scenario**: Feature parses sensor data from a serial port.

**C/embedded context**: The parse logic operates directly on byte buffers from the serial HAL. The domain judgment (interpreting byte sequences as sensor values) is inseparable from the buffer type.

```
prx_sensor.c  →  "parse HAL byte buffer into sensor values with domain validation"
```

**OOP context**: In C#/Java, the parse logic can be encapsulated in an immutable domain object. The serial port provides a byte array, which poi_ converts to a domain-neutral input type, and ida_ interprets it.

```
ida_SensorParser.cs  →  "pure domain parsing: byte[] → SensorReading (immutable)"
poi_SerialSensor.cs  →  "read from SerialPort, pass bytes to ida_"
```

**Key insight**: The same logical operation may be prx_ in C/embedded (where type coupling is unavoidable) but ida_+poi_ in OOP (where interfaces and immutable types allow separation).

---

### Example 5: Timer-Based State Machine (ida_ + poi_)

**Scenario**: Feature implements a timeout-based state machine.

- **Domain judgment**: "If state is ACTIVE and 500ms elapsed, transition to IDLE"
- **External dependency**: Timer middleware provides `Mdw_Timer_GetElapsed()`

**Decision**: The state machine logic (transitions, conditions) is pure domain. The timer value can be passed as a plain integer.

```
ida_feature.c  →  "state machine: check elapsed_ms, decide transitions"
poi_feature.c  →  "call Mdw_Timer_GetElapsed(), pass result to ida_"
```

**Discriminator path**: Q1=Yes → Q2=Yes → ida_ + poi_

---

## 4. Anti-Patterns

### Anti-Pattern: "Convenient Middle Ground"

**Wrong reasoning**: "This code is too complex for poi_ but too implementation-specific for ida_, so let's put it in prx_."

Complexity is not the criterion. The only valid criterion is: "Does the domain judgment require the external type to be expressed?"

### Anti-Pattern: "Everything External Goes to prx_"

**Wrong reasoning**: "This function uses an external API, so it must be prx_."

Most external API usage is mechanical wrapping (poi_). Praxis is only for cases where the domain meaning is encoded in the external type itself.

### Anti-Pattern: "Fat Praxis"

**Symptom**: prx_ file is mostly `get()`/`set()`/`read()`/`write()` wrapper functions with no conditional logic.

**Fix**: These are poi_ functions. Move them to poi_ and reserve prx_ for genuine interpretation logic.

---

## 5. Quick Decision Checklist

Before creating a prx_ file:

- [ ] Does the code contain `if`/`switch` with domain-meaningful conditions?
- [ ] Do those conditions reference external types directly?
- [ ] Would extracting the judgment to ida_ require duplicating the external type definition?
- [ ] Is the judgment inseparable from the external type's internal structure?

If all four are "Yes" → prx_ is justified.
If any is "No" → reconsider: ida_ + poi_ split may be possible.

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.0**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
