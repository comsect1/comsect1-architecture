# Appendix C. Dual-Engine Application Pattern

> **Heritage:** This appendix does not introduce a new concept. It documents
> a pattern that has been practiced since the Unix tradition of the 1970s and
> maps it to the comsect1 folder structure and contract boundary model.
>
> The Unix philosophy — "write programs that do one thing well" and "expect
> the output of every program to become the input to another" (Doug McIlroy,
> 1978) — established the principle that a program's **command interface and
> output format are its public contract**. GUI tools, scripts, and other
> consumers depend on that contract, not on the program's internal structure.
>
> This principle has been carried forward by generations of software:
> `git` (CLI core + many GUI surfaces), FFmpeg (CLI core + GUI front-ends),
> Blender (Python API core + GUI shell), ImageMagick, and countless others.
>
> comsect1 acknowledges this lineage with respect and formalizes it within
> the `/api` folder convention already defined in Section 7.7.

---

## A3.1 Scope

This appendix applies when an application is structured as:

- A **core engine** — a standalone executable or library that performs the
  actual work, invocable via CLI, IPC, or programmatic API.
- One or more **surface interfaces** — GUI, web UI, TUI, or scripting
  shell — that invoke the core engine and present its results to the user.

The surface does not contain domain logic. The core does not contain
presentation logic. The boundary between them is a **contract**.

---

## A3.2 Pattern Definition

### A3.2.1 Core Engine

The core engine:

- Accepts structured input (CLI arguments, stdin, IPC messages).
- Produces structured output (stdout, files, IPC messages).
- Contains all domain logic, organized per the comsect1 3-Layer Feature
  Model (Section 2.3).
- Is independently testable and usable without any surface.

### A3.2.2 Surface Interface

The surface interface:

- Invokes the core engine (as a subprocess, library call, or IPC client).
- Reads and displays the core's output.
- Manages user interaction (input, progress, results display).
- Contains no domain logic — only presentation mechanics.

### A3.2.3 Contract Boundary

The contract between core and surface consists of:

1. **Command specification** — available commands, arguments, options,
   and their default values.
2. **Output format specification** — the structure and semantics of the
   core's output (e.g., JSON-Lines message types, exit codes, file formats).
3. **Error contract** — how the core reports errors and warnings.

The surface depends exclusively on this contract. Changes to the core's
internal structure (layer refactoring, dependency changes, performance
optimization) must not affect the surface, as long as the contract is
preserved.

---

## A3.3 Mapping to comsect1 Folder Structure

Section 7.7 defines `/api` as the "public membrane" of a comsect1 unit.
In the dual-engine pattern, `/api` is the natural home for the contract
between core and surface.

### A3.3.1 What belongs in /api

| Contract element | File | Content |
|------------------|------|---------|
| Command specification | `app_<unit>.cs` (or equivalent) | Command names, argument types, option names, defaults, usage |
| Output message types | Re-exported or defined in `app_<unit>.cs` | All IPC message types that the surface may receive |
| Error/warning codes | Included in message type definitions | Structured error contract |

### A3.3.2 What does NOT belong in /api

- Internal domain types used only within the core.
- Layer implementation details (`ida_`, `prx_`, `poi_` internals).
- Configuration structures consumed only by the core.

### A3.3.3 Relationship to cfg_Core

`cfg_Core` defines the **internal** contract vocabulary — types shared across
layers within the core. `/api` defines the **external** contract — types shared
between the core and its surfaces.

Some types may appear in both (e.g., IPC message records defined in `cfg_Core`
and re-exported through `/api`). The distinction is audience:

- `cfg_Core` audience: internal layers (`ida_`, `prx_`, `poi_`).
- `/api` audience: external consumers (surfaces, scripts, other tools).

---

## A3.4 Contract Stability Rule

> **The contract is the most stable artifact in the system.**

When the core's internal architecture changes (layer splits, dependency
cleanup, performance refactoring), the contract must remain stable. Breaking
the contract requires explicit versioning and surface-side migration.

This is the Unix principle restated: a program's interface is its promise to
other programs. Internal reorganization is free; interface change is costly.

---

## A3.5 Verification

For dual-engine applications, the following additional verification applies:

1. Every command the surface invokes must be defined in `/api`.
2. Every output message type the surface parses must be defined in or
   re-exported through `/api`.
3. The surface must not import from `/infra`, `/project/features`, or any
   internal core namespace — only from `/api` and shared contract types.

---

## A3.6 Examples

### A3.6.1 CLI Core + GUI Surface (subprocess model)

```text
Core engine: hms-core.exe
  /comsect1
    /api
      app_hms.cs          <- CLI commands: scan, load, classify
                              JSON-Lines output: PhaseMsg, ScanProgressMsg, ...
    /infra/bootstrap      <- ida_Core, poi_Core, cfg_Core
    /project/features     <- scan, classify, excelio

Surface: Hatbit Mail Scanner.exe (WPF)
  Spawns hms-core.exe as subprocess
  Sends: CLI arguments per /api spec
  Receives: JSON-Lines on stdout per /api spec
  Displays: progress bar, log, results grid
```

### A3.6.2 Library Core + Web Surface (in-process model)

```text
Core library: MyEngine.dll
  /comsect1
    /api
      app_engine.cs       <- Public methods, DTOs, event types
    /infra, /project      <- Internal architecture

Surface: ASP.NET Web API
  References MyEngine.dll
  Calls only types defined in /api
  Exposes REST endpoints that map to /api methods
```

---

## A3.7 Historical Note

The separation of "engine that does the work" from "interface that presents
it" predates graphical computing. The Unix shell itself is a surface over
the kernel and userland tools. The X Window System separated the display
server (surface) from client applications (engines). This principle has
proven durable across five decades of computing because it aligns with a
fundamental insight: **the work and its presentation change for different
reasons, at different rates, under different pressures.**

comsect1's contribution is not the pattern itself — it is the mapping of
this pattern to a concrete, verifiable folder structure and contract
boundary that AI agents and gate scripts can enforce.

---

## License

This document is part of the **comsect1 Architecture Specification v1.0.1**.

**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

You are free to:
- **Share** - copy and redistribute the material in any medium or format for
  non-commercial purposes only.

Under the following terms:
- **Attribution** - You must give appropriate credit to the author (Kim
  Hyeongjeong), provide a reference to the license, and indicate if changes
  were made.
- **NonCommercial** - You may not use the material for commercial purposes.
- **NoDerivatives** - If you remix, transform, or build upon the material, you
  may not distribute the modified material.

No additional restrictions - You may not apply legal terms or technological
measures that legally restrict others from doing anything the license permits.

*Copyright 2025 Kim Hyeongjeong. All rights reserved under the terms above.*
