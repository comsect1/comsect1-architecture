# comsect1 Standard Development Process Overview

This document defines the standard procedure that all development and refactoring tasks based on the comsect1 architecture must follow. The purpose of this procedure is to ensure development consistency, maintain architectural integrity, and guarantee the quality of the final deliverables.

All developers and AI agents must familiarize themselves with and adhere to this standard procedure before and during their work.

---

## Standard Development Workflow

All work on a comsect1 project follows the four-stage workflow below.

### **Stage 1: Learn the Principles (Design Principles)**

> **"Before you consider how to build it, you must understand what you are building and why."**

*   **Objective:** To clearly understand the core architectural principles and design philosophy relevant to the task at hand (e.g., new development, refactoring, bug fixing).
*   **Action:** Read and internalize the relevant documents in the `/guides/01_Design_Principles/` directory.
    *   All work begins with **[DP_01_Core_Architecture.md](./01_Design_Principles/DP_01_Core_Architecture.md)**.
    *   For tasks related to real-time systems, additionally study **[DP_02_Realtime_Design.md](./01_Design_Principles/DP_02_Realtime_Design.md)**.

### **Stage 2: Execute with Guides (Execution Guides)**

> **"Follow a proven procedure to minimize trial-and-error and produce predictable results."**

*   **Objective:** To systematically carry out development by following the most appropriate execution guide for the given task.
*   **Action:** Select and follow the step-by-step procedures in the relevant guide from the `/guides/02_Execution_Guides/` directory.
    *   For new projects, follow **[EG_01_New_Project_Setup.md](./02_Execution_Guides/EG_01_New_Project_Setup.md)**.
    *   When refactoring legacy code, follow **[EG_02_Refactoring_Legacy.md](./02_Execution_Guides/EG_02_Refactoring_Legacy.md)**.

### **Stage 3: Verify After Task (Post-Task Verification)**

> **"Do not trust your own work. Prove it with rules."**

*   **Objective:** To objectively verify that your output perfectly adheres to the architectural rules after **every meaningful step** in the Stage 2 execution guide.
*   **Action:** Use the checklists in the `/guides/03_Verification/` directory to validate your work.
    *   Each step in the execution guides explicitly states which checklist to use (e.g., "Step 6: Post-Task Verification").
    *   **[V_01_Post_Task_Checklist.md](./03_Verification/V_01_Post_Task_Checklist.md)** is the most fundamental verification tool used after all code writing and modification tasks.
*   **The Golden Rule:** **A task that fails verification is not considered complete, and you must not proceed to the next step.**

### **Stage 4: Run AIAD Auto Gate (Machine Validation)**

> **"Human checklist + machine gate = enforceable architecture discipline."**

*   **Objective:** To produce an objective, machine-readable pass/fail decision for architecture integrity.
*   **Action:** Run the unified gate script after Stage 3 human verification.

```powershell
# Spec + Code architecture gate (recommended)
python scripts/Verify-AIADGate.py -CodeRoot codes/comsect1 -ReportPath .aiad-gate-report.json

# Spec-only gate (if code root is not available)
python scripts/Verify-AIADGate.py -SkipCode -ReportPath .aiad-gate-report.json
```

*   **Output:** A JSON report (`.aiad-gate-report.json`) containing stage results and final gate status.
*   **Gate Rule:** If AIAD gate fails, the work is not complete.

---

## Relationship of Architecture Documents

*   **`specs/` (Specifications):** This is the constitution, containing the "definitions" and "laws" of the architecture. It is the foundation of everything.
*   **`guides/` (Guides & Appendices):** This is the implementation manual, explaining "how" to apply and enforce the constitution (`specs`) in a real-world context. These guides are the official appendices to the specifications.

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

