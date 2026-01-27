# DP-01: Core Architectural Principles

This document provides guidance on the foundational principles of the comsect1 architecture and the location of its core specification documents.

All design and development activities must begin with an understanding of the official specifications defined in the `specs/` directory. All content within this `guides/` folder serves as the **Official Appendix** that explains 'how' to apply the `specs/` content in a practical, real-world context.

---

## Core Specification Documents

Before starting development, you must be familiar with the following documents:

*   **[../../specs/01_philosophy.md](../../specs/01_philosophy.md)**
    *   **Content:** Understand the philosophy and goals of the comsect1 architecture. This explains the "why" behind the design.

*   **[../../specs/03_architecture_structure.md](../../specs/03_architecture_structure.md)**
    *   **Content:** Grasp the overall structure and components of the architecture, including Features, Infra Capability, and Platform.

*   **[../../specs/04_layer_roles.md](../../specs/04_layer_roles.md)**
    *   **Content:** Clearly defines the roles and responsibilities of each layer, such as Idea, Praxis, and Poiesis. **This is the most critical document to study to avoid confusing layer roles.**
    *   **Note:** Includes the **Core Domain** as Section 4.0.

*   **[../../specs/05_dependency_rules.md](../../specs/05_dependency_rules.md)**
    *   **Content:** Defines the interaction rules and dependency direction between layers. This is the rulebook for "which layer can call which other layer."

---

**Conclusion: `specs/` is the 'Law', and `guides/` is the 'Practical Manual' for enforcing that law. Always check the law first.**

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
