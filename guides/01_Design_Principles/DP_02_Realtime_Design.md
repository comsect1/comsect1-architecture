# comsect1 Real-time Design Guidelines

## 1. Overview

This document provides design guidelines for implementing the comsect1 architecture in an RTOS (Real-Time Operating System) environment to ensure system stability and responsiveness.

While the core specifications of comsect1 are OS-independent, most actual embedded systems operate on top of an RTOS. Therefore, understanding the best practices for how each element of the architecture interacts with the runtime environment is crucial.

This document serves as a 'practical implementation guide' rather than the 'essence' of comsect1, complementing the core specifications (`specs/`).

---

## 2. Idea (Task) Priority Guidelines

When multiple asynchronously executing Ideas (corresponding to 'Tasks' in an RTOS) exist, setting the priority for each Idea is a key design decision that determines the overall system performance.

The following are the recommended priority settings in the comsect1 architecture.

*   **Recommendation 1: Assign `Low Priority` to Ideas that run frequently or have predictable periodicity.**
    *   Examples: An Idea refreshing the display every 50ms, an Idea logging sensor data every 100ms.

*   **Recommendation 2: Assign `High Priority` to event-driven Ideas that occur unpredictably and sporadically.**
    *   Examples: An Idea handling user button input, an Idea handling CAN/UART message reception from external devices, an Idea handling system errors (Faults).

---

## 3. Rationale

The goal of these recommendations is not simply to process 'important things' first, but **"to guarantee that all Ideas in the system complete their missions within their given Deadlines, thereby maximizing the responsiveness and stability of the entire system."**

### 3.1 Why place periodic tasks at low priority?

Periodic Ideas have relatively lenient and predictable deadlines, needing only to complete "before the next cycle begins."

If high priority is assigned to these tasks, they will almost always be in a ready-to-run state, constantly preempting the processing of more urgent but rarely occurring events. This results in a system that appears busy but reacts late to critical external stimuli.

By assigning low priority, these tasks utilize the 'idle time' when no other urgent tasks are present. Even if they yield the CPU to higher-priority tasks for a moment, their long periods allow them to complete their work comfortably without missing deadlines. This is an efficient way to use system resources.

### 3.2 Why place event-driven tasks at high priority?

Event-driven Ideas are unpredictable in occurrence but have short deadlines requiring 'immediate' processing once they happen.

Assigning high priority to these tasks allows them to immediately interrupt currently running low-priority periodic tasks and execute first. This **minimizes the Latency from event occurrence to actual processing**. For example, when a user presses an emergency stop button, the system should not wait for a display refresh task to finish.

Since event-driven tasks mostly execute briefly and return to a dormant state, their temporary CPU usage places little burden on the overall system scheduling. It is a very small cost paid for the large gain of 'fast responsiveness'.

### 3.3 Core Principle

This guideline is based on the scheduling principle of real-time systems (e.g., Deadline-Monotonic Scheduling): **"Assign higher priority to tasks with shorter deadlines."**

*   **Event-driven tasks:** Very short deadline -> **High Priority**
*   **Periodic tasks:** Relatively long deadline -> **Low Priority**

Following this guideline improves the overall 'Schedulability' of the system, allowing the construction of a stable system where all Ideas perform their duties without issues.

---

## 4. Caution: Priority Inversion

When applying these guidelines, one must be aware of the **Priority Inversion** phenomenon.

*   **Phenomenon:** A situation where a low-priority task holds a shared resource (such as a Mutex), preventing a high-priority task from executing, while a medium-priority task preempts the low-priority task, effectively blocking the high-priority task.
*   **Countermeasure:**
    *   Avoid resource sharing between tasks whenever possible, and recommend asynchronous communication via message queues (utilizing the Praxis pattern).
    *   If resource sharing is unavoidable, the **Priority Inheritance** feature provided by the RTOS must be enabled.

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
