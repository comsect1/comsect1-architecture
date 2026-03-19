#!/usr/bin/env python3
"""Create a minimal comsect1 scaffold layout.

With -FullProject, generates a complete IAR embedded C project package
including unit-qualified files, CMake cross-compile setup, and VSCode
IAR/C-STAT configuration.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


INVALID_WINDOWS_CHARS = set('<>:"/\\|?*')

MCU_IAR_MAP: dict[str, dict[str, str]] = {
    "STM32F4": {"cpu": "cortex-m4", "fpu": "VFPv4_sp"},
    "STM32F7": {"cpu": "cortex-m7", "fpu": "VFPv5_sp"},
    "STM32H7": {"cpu": "cortex-m7", "fpu": "VFPv5_dp"},
    "STM32L4": {"cpu": "cortex-m4", "fpu": "VFPv4_sp"},
    "STM32G4": {"cpu": "cortex-m4", "fpu": "VFPv4_sp"},
    "STM32F1": {"cpu": "cortex-m3", "fpu": "none"},
    "STM32F0": {"cpu": "cortex-m0", "fpu": "none"},
    "STM32L0": {"cpu": "cortex-m0plus", "fpu": "none"},
}


def assert_valid_feature_name(name: str) -> None:
    trimmed = name.strip()
    if not trimmed:
        raise ValueError("Feature name cannot be empty.")
    if "/" in trimmed or "\\" in trimmed:
        raise ValueError(f"Invalid feature name: '{trimmed}' (must be a folder name, not a path)")
    if re.match(r"^\.+$", trimmed):
        raise ValueError(f"Invalid feature name: '{trimmed}'")
    if any(ch in INVALID_WINDOWS_CHARS for ch in trimmed):
        raise ValueError(f"Invalid feature name: '{trimmed}' (contains invalid path characters)")
    if any(ord(ch) < 32 for ch in trimmed):
        raise ValueError(f"Invalid feature name: '{trimmed}' (contains control characters)")
    if re.match(r"^[./\\]", trimmed):
        raise ValueError(f"Invalid feature name: '{trimmed}' (must be a folder name, not a path)")


def assert_valid_unit_name(name: str) -> None:
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        raise ValueError(
            f"Invalid unit name: '{name}' (must be lowercase ASCII, "
            "start with a letter, contain only [a-z0-9_])"
        )


def to_upper_ident(name: str) -> str:
    return name.upper()


def to_pascal(name: str) -> str:
    return "".join(word.capitalize() for word in name.split("_"))


def write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalize_feature_args(features: list[str]) -> list[str]:
    names: list[str] = []
    for value in features:
        if value is None:
            continue
        for item in value.split(","):
            trimmed = item.strip()
            if trimmed:
                names.append(trimmed)
    return sorted(set(names))


def _lookup_mcu_flags(mcu: str) -> dict[str, str]:
    mcu_upper = mcu.upper()
    for prefix, flags in MCU_IAR_MAP.items():
        if mcu_upper.startswith(prefix):
            return flags
    return {"cpu": "/* TODO: set IAR CPU */", "fpu": "/* TODO: set IAR FPU */"}


# ---------------------------------------------------------------------------
# Full-project file generators (all use write_if_missing)
# ---------------------------------------------------------------------------


def _gen_cfg_core(root: Path, unit: str, features: list[str]) -> None:
    guard = f"CFG_CORE_{to_upper_ident(unit)}_H"
    ida_ids = ["IDA_ID_CORE"]
    for f in features:
        ida_ids.append(f"IDA_ID_{to_upper_ident(f)}")
    ida_ids.append("IDA_ID_COUNT")
    ida_enum = ",\n    ".join(ida_ids)
    write_if_missing(
        root / "infra" / "bootstrap" / f"cfg_core_{unit}.h",
        "\n".join([
            f"#ifndef {guard}",
            f"#define {guard}",
            "",
            "#include <stdint.h>",
            "#include <stdbool.h>",
            "",
            "/* comsect1 Core Contract header. */",
            "",
            "typedef enum {",
            "    RESULT_OK = 0,",
            "    RESULT_ERROR",
            "} Result_t;",
            "",
            "typedef enum {",
            f"    {ida_enum}",
            "} Ida_Id_t;",
            "",
            "typedef struct {",
            "    Result_t (*Init)(void);",
            "    void     (*Main)(void);",
            "} Ida_Interface_t;",
            "",
            f"#endif /* {guard} */",
            "",
        ]),
    )


def _gen_cfg_project(root: Path, unit: str, mcu: str) -> None:
    guard = f"CFG_PROJECT_{to_upper_ident(unit)}_H"
    write_if_missing(
        root / "project" / "config" / f"cfg_project_{unit}.h",
        "\n".join([
            f"#ifndef {guard}",
            f"#define {guard}",
            "",
            f"/* Project target configuration for {mcu}.",
            " * Praxis and Poiesis may include this header; Idea must not. */",
            "",
            f"#define TARGET_MCU \"{mcu}\"",
            "",
            f"#endif /* {guard} */",
            "",
        ]),
    )


def _gen_app_header(root: Path, unit: str) -> None:
    guard = f"APP_{to_upper_ident(unit)}_H"
    pascal = to_pascal(unit)
    write_if_missing(
        root / "api" / f"app_{unit}.h",
        "\n".join([
            f"#ifndef {guard}",
            f"#define {guard}",
            "",
            f"#include \"cfg_core_{unit}.h\"",
            "",
            f"Result_t App_{pascal}_Init(void);",
            f"void     App_{pascal}_Run(void);",
            "",
            f"#endif /* {guard} */",
            "",
        ]),
    )


def _gen_ida_core(root: Path, unit: str, features: list[str]) -> None:
    guard = f"IDA_CORE_{to_upper_ident(unit)}_H"
    pascal = to_pascal(unit)
    includes = [f'#include "cfg_core_{unit}.h"']
    for f in features:
        includes.append(f'#include "ida_{f}_{unit}.h"')
    includes_str = "\n".join(includes)

    reg_lines = []
    for f in features:
        fp = to_pascal(f)
        reg_lines.append(
            f"    Poi_Core_{pascal}_Register(IDA_ID_{to_upper_ident(f)}, "
            f"Ida_{fp}_{pascal}_GetInterface());"
        )
    reg_str = "\n".join(reg_lines)

    # Header
    write_if_missing(
        root / "infra" / "bootstrap" / f"ida_core_{unit}.h",
        "\n".join([
            f"#ifndef {guard}",
            f"#define {guard}",
            "",
            f'#include "cfg_core_{unit}.h"',
            "",
            f"Result_t Ida_Core_{pascal}_Init(void);",
            f"void     Ida_Core_{pascal}_Entry(void);",
            "",
            f"#endif /* {guard} */",
            "",
        ]),
    )

    # Source
    write_if_missing(
        root / "infra" / "bootstrap" / f"ida_core_{unit}.c",
        "\n".join([
            f'#include "ida_core_{unit}.h"',
            f'#include "poi_core_{unit}.h"',
            includes_str,
            "",
            f"Result_t Ida_Core_{pascal}_Init(void)",
            "{",
            reg_str,
            "    return RESULT_OK;",
            "}",
            "",
            f"void Ida_Core_{pascal}_Entry(void)",
            "{",
            f"    Ida_Core_{pascal}_Init();",
            f"    Poi_Core_{pascal}_Start();",
            "}",
            "",
        ]),
    )


def _gen_poi_core(root: Path, unit: str) -> None:
    guard = f"POI_CORE_{to_upper_ident(unit)}_H"
    pascal = to_pascal(unit)

    # Header
    write_if_missing(
        root / "infra" / "bootstrap" / f"poi_core_{unit}.h",
        "\n".join([
            f"#ifndef {guard}",
            f"#define {guard}",
            "",
            f'#include "cfg_core_{unit}.h"',
            "",
            f"Result_t Poi_Core_{pascal}_Init(void);",
            f"void     Poi_Core_{pascal}_Register(Ida_Id_t id, Ida_Interface_t iface);",
            f"void     Poi_Core_{pascal}_Start(void);",
            "",
            f"#endif /* {guard} */",
            "",
        ]),
    )

    # Source
    write_if_missing(
        root / "infra" / "bootstrap" / f"poi_core_{unit}.c",
        "\n".join([
            f'#include "poi_core_{unit}.h"',
            "",
            "static Ida_Interface_t s_interfaces[IDA_ID_COUNT];",
            "",
            f"Result_t Poi_Core_{pascal}_Init(void)",
            "{",
            "    return RESULT_OK;",
            "}",
            "",
            f"void Poi_Core_{pascal}_Register(Ida_Id_t id, Ida_Interface_t iface)",
            "{",
            "    if (id < IDA_ID_COUNT) {",
            "        s_interfaces[id] = iface;",
            "    }",
            "}",
            "",
            f"void Poi_Core_{pascal}_Start(void)",
            "{",
            "    for (Ida_Id_t i = 0; i < IDA_ID_COUNT; i++) {",
            "        if (s_interfaces[i].Init != (void*)0) {",
            "            s_interfaces[i].Init();",
            "        }",
            "    }",
            "",
            "    /* Main loop */",
            "    while (1) {",
            "        for (Ida_Id_t i = 0; i < IDA_ID_COUNT; i++) {",
            "            if (s_interfaces[i].Main != (void*)0) {",
            "                s_interfaces[i].Main();",
            "            }",
            "        }",
            "    }",
            "}",
            "",
        ]),
    )


def _gen_feature_ida(root: Path, unit: str, feat: str) -> None:
    guard = f"IDA_{to_upper_ident(feat)}_{to_upper_ident(unit)}_H"
    pascal_u = to_pascal(unit)
    pascal_f = to_pascal(feat)

    # Header
    write_if_missing(
        root / "project" / "features" / feat / f"ida_{feat}_{unit}.h",
        "\n".join([
            f"#ifndef {guard}",
            f"#define {guard}",
            "",
            f'#include "cfg_core_{unit}.h"',
            "",
            f"Ida_Interface_t Ida_{pascal_f}_{pascal_u}_GetInterface(void);",
            "",
            f"#endif /* {guard} */",
            "",
        ]),
    )

    # Source
    write_if_missing(
        root / "project" / "features" / feat / f"ida_{feat}_{unit}.c",
        "\n".join([
            f'#include "ida_{feat}_{unit}.h"',
            f'#include "poi_{feat}_{unit}.h"',
            "",
            f"static Result_t Ida_{pascal_f}_{pascal_u}_Init(void)",
            "{",
            "    return RESULT_OK;",
            "}",
            "",
            f"static void Ida_{pascal_f}_{pascal_u}_Main(void)",
            "{",
            f"    /* TODO: {feat} business logic */",
            "}",
            "",
            f"Ida_Interface_t Ida_{pascal_f}_{pascal_u}_GetInterface(void)",
            "{",
            f"    Ida_Interface_t iface = {{",
            f"        .Init = Ida_{pascal_f}_{pascal_u}_Init,",
            f"        .Main = Ida_{pascal_f}_{pascal_u}_Main,",
            "    };",
            "    return iface;",
            "}",
            "",
        ]),
    )


def _gen_feature_poi(root: Path, unit: str, feat: str) -> None:
    guard = f"POI_{to_upper_ident(feat)}_{to_upper_ident(unit)}_H"
    pascal_u = to_pascal(unit)
    pascal_f = to_pascal(feat)

    # Header
    write_if_missing(
        root / "project" / "features" / feat / f"poi_{feat}_{unit}.h",
        "\n".join([
            f"#ifndef {guard}",
            f"#define {guard}",
            "",
            f'#include "cfg_core_{unit}.h"',
            "",
            f"Result_t Poi_{pascal_f}_{pascal_u}_Init(void);",
            "",
            f"#endif /* {guard} */",
            "",
        ]),
    )

    # Source
    write_if_missing(
        root / "project" / "features" / feat / f"poi_{feat}_{unit}.c",
        "\n".join([
            f'#include "poi_{feat}_{unit}.h"',
            f'#include "cfg_project_{unit}.h"',
            "",
            f"Result_t Poi_{pascal_f}_{pascal_u}_Init(void)",
            "{",
            f"    /* TODO: {feat} mechanical execution */",
            "    return RESULT_OK;",
            "}",
            "",
        ]),
    )


def _gen_main_c(codes_dir: Path, unit: str) -> None:
    pascal = to_pascal(unit)
    write_if_missing(
        codes_dir / "main.c",
        "\n".join([
            f'#include "ida_core_{unit}.h"',
            "",
            "int main(void)",
            "{",
            f"    Ida_Core_{pascal}_Entry();",
            "    return 0;",
            "}",
            "",
        ]),
    )


def _gen_cmakelists(project_dir: Path, unit: str, features: list[str]) -> None:
    pascal = to_pascal(unit)
    feat_list = " ".join(features)
    write_if_missing(
        project_dir / "CMakeLists.txt",
        "\n".join([
            "cmake_minimum_required(VERSION 3.16)",
            f"project({pascal}Project C)",
            "",
            "set(CMAKE_C_STANDARD 11)",
            "",
            "# IAR toolchain (uncomment for cross-compilation)",
            "# include(cmake/iar-toolchain.cmake)",
            "",
            f'set(COMSECT1 "${{CMAKE_SOURCE_DIR}}/codes/comsect1")',
            "",
            "# Domain include paths (§7.11.1)",
            "include_directories(",
            "    ${COMSECT1}/api",
            "    ${COMSECT1}/project/config",
            "    ${COMSECT1}/project/datastreams",
            "    ${COMSECT1}/infra/bootstrap",
            "    ${COMSECT1}/infra/service",
            "    ${COMSECT1}/infra/platform/hal",
            "    ${COMSECT1}/infra/platform/bsp",
            "    ${COMSECT1}/deps/middleware",
            "    ${COMSECT1}/deps/extern",
            ")",
            "",
            "# Feature selection",
            f"set(FEATURES {feat_list})",
            "set(PROJECT_SRCS)",
            "",
            "foreach(feat ${FEATURES})",
            "    include_directories(${COMSECT1}/project/features/${feat})",
            '    file(GLOB FEAT_SRCS "${COMSECT1}/project/features/${feat}/*.c")',
            "    list(APPEND PROJECT_SRCS ${FEAT_SRCS})",
            "endforeach()",
            "",
            'file(GLOB BOOTSTRAP_SRCS "${COMSECT1}/infra/bootstrap/*.c")',
            "",
            "add_executable(${PROJECT_NAME}",
            "    codes/main.c",
            "    ${BOOTSTRAP_SRCS}",
            "    ${PROJECT_SRCS}",
            ")",
            "",
        ]),
    )


def _gen_iar_toolchain(project_dir: Path, mcu: str) -> None:
    flags = _lookup_mcu_flags(mcu)
    cpu = flags["cpu"]
    fpu = flags["fpu"]
    write_if_missing(
        project_dir / "cmake" / "iar-toolchain.cmake",
        "\n".join([
            "# IAR Embedded Workbench toolchain file",
            f"# Target MCU: {mcu}",
            "",
            "set(CMAKE_SYSTEM_NAME Generic)",
            "set(CMAKE_SYSTEM_PROCESSOR ARM)",
            "",
            "# IAR installation path (adjust to your environment)",
            'set(IAR_ROOT "C:/Program Files/IAR Systems/Embedded Workbench 9.2")',
            'set(CMAKE_C_COMPILER "${IAR_ROOT}/arm/bin/iccarm.exe")',
            'set(CMAKE_ASM_COMPILER "${IAR_ROOT}/arm/bin/iasmarm.exe")',
            'set(CMAKE_AR "${IAR_ROOT}/arm/bin/iarchive.exe")',
            "",
            f"# MCU flags for {mcu}",
            f'set(MCU_FLAGS "--cpu {cpu}")',
            "",
        ] + ([
            f'set(FPU_FLAGS "--fpu {fpu}")',
        ] if fpu != "none" else [
            "# No FPU for this MCU",
            'set(FPU_FLAGS "")',
        ]) + [
            "",
            "# Linker script (set to your .icf file)",
            'set(LINKER_SCRIPT "${CMAKE_SOURCE_DIR}/config.icf")',
            'set(CMAKE_C_LINK_FLAGS "${CMAKE_C_LINK_FLAGS} --config ${LINKER_SCRIPT}")',
            "",
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} ${MCU_FLAGS} ${FPU_FLAGS}\")",
            "set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)",
            "set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)",
            "set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)",
            "",
        ]),
    )


def _gen_vscode_tasks(project_dir: Path) -> None:
    import json

    tasks_data = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "CMake Configure",
                "type": "shell",
                "command": "cmake",
                "args": ["-B", "build", "-S", "."],
                "group": "build",
                "problemMatcher": [],
            },
            {
                "label": "CMake Build",
                "type": "shell",
                "command": "cmake",
                "args": ["--build", "build"],
                "group": {"kind": "build", "isDefault": True},
                "problemMatcher": ["$gcc"],
            },
            {
                "label": "IAR Build (iarbuild)",
                "type": "shell",
                "command": "iarbuild",
                "args": ["${workspaceFolder}/*.ewp", "-build", "Debug"],
                "group": "build",
                "problemMatcher": [],
            },
            {
                "label": "C-STAT Analyze",
                "type": "shell",
                "command": "iarbuild",
                "args": ["${workspaceFolder}/*.ewp", "-cstat_analyze", "Debug"],
                "group": "test",
                "problemMatcher": [],
            },
        ],
    }
    vscode_dir = project_dir / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)
    write_if_missing(
        vscode_dir / "tasks.json",
        json.dumps(tasks_data, indent=4) + "\n",
    )


def _gen_vscode_launch(project_dir: Path, mcu: str) -> None:
    import json

    launch_data = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": f"IAR C-SPY ({mcu})",
                "type": "cspy",
                "request": "launch",
                "program": "${workspaceFolder}/build/Debug/Exe/*.out",
                "driver": "Simulator",
                "stopOnEntry": True,
                "driverOptions": [],
            },
        ],
    }
    vscode_dir = project_dir / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)
    write_if_missing(
        vscode_dir / "launch.json",
        json.dumps(launch_data, indent=4) + "\n",
    )


def _gen_vscode_settings(project_dir: Path, features: list[str]) -> None:
    import json

    feat_paths = [f"codes/comsect1/project/features/{f}/**" for f in features]
    settings_data = {
        "C_Cpp.default.includePath": [
            "codes/comsect1/api",
            "codes/comsect1/project/config",
            "codes/comsect1/project/datastreams",
            "codes/comsect1/infra/bootstrap",
            "codes/comsect1/infra/service",
            "codes/comsect1/infra/platform/hal",
            "codes/comsect1/infra/platform/bsp",
            "codes/comsect1/deps/middleware",
            "codes/comsect1/deps/extern",
        ]
        + feat_paths,
    }
    vscode_dir = project_dir / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)
    write_if_missing(
        vscode_dir / "settings.json",
        json.dumps(settings_data, indent=4) + "\n",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Create comsect1 scaffold folders/files.")
    parser.add_argument(
        "-Path",
        dest="path",
        default=str(Path.cwd() / "codes" / "comsect1"),
        help="Destination comsect1 root path.",
    )
    parser.add_argument(
        "-Features",
        dest="features",
        nargs="*",
        default=[],
        help="Optional feature folder names (supports comma-separated values).",
    )
    parser.add_argument(
        "-Unit",
        dest="unit",
        default=None,
        help="Project unit identifier (lowercase). Required with -FullProject.",
    )
    parser.add_argument(
        "-MCU",
        dest="mcu",
        default=None,
        help="IAR target MCU (e.g. STM32F407). Required with -FullProject.",
    )
    parser.add_argument(
        "-FullProject",
        dest="full_project",
        action="store_true",
        default=False,
        help="Generate full IAR project package (unit-qualified files, CMake, VSCode).",
    )
    args = parser.parse_args()

    root_path = Path(args.path).resolve()

    if args.full_project:
        if not args.unit:
            print("ERROR: -Unit is required when using -FullProject.", file=sys.stderr)
            return 2
        if not args.mcu:
            print("ERROR: -MCU is required when using -FullProject.", file=sys.stderr)
            return 2
        assert_valid_unit_name(args.unit)

    root_path.mkdir(parents=True, exist_ok=True)

    # Path convention check
    parts = root_path.parts
    if len(parts) >= 2:
        tail = "/".join(parts[-2:]).replace("\\", "/")
        if tail != "codes/comsect1":
            print(f"WARNING: comsect1 root does not end with /codes/comsect1 (got: {root_path})")

    relative_dirs = [
        "api",
        "project",
        "project/config",
        "project/datastreams",
        "project/features",
        "infra",
        "infra/bootstrap",
        "infra/service",
        "infra/platform",
        "infra/platform/hal",
        "infra/platform/bsp",
        "deps",
        "deps/extern",
        "deps/middleware",
    ]

    for rel in relative_dirs:
        (root_path / rel).mkdir(parents=True, exist_ok=True)

    feature_names = normalize_feature_args(args.features)
    for feature_name in feature_names:
        assert_valid_feature_name(feature_name)
        (root_path / "project" / "features" / feature_name).mkdir(parents=True, exist_ok=True)

    if args.full_project:
        unit = args.unit
        mcu = args.mcu
        codes_dir = root_path.parent       # /codes
        project_dir = codes_dir.parent      # /Project

        # Core contract and project config (unit-qualified)
        _gen_cfg_core(root_path, unit, feature_names)
        _gen_cfg_project(root_path, unit, mcu)

        # Application API header
        _gen_app_header(root_path, unit)

        # Bootstrap files
        _gen_ida_core(root_path, unit, feature_names)
        _gen_poi_core(root_path, unit)

        # Feature files (ida + poi only; prx not generated per spec §5)
        for feat in feature_names:
            _gen_feature_ida(root_path, unit, feat)
            _gen_feature_poi(root_path, unit, feat)

        # main.c in /codes
        _gen_main_c(codes_dir, unit)

        # Build system files at project root
        _gen_cmakelists(project_dir, unit, feature_names)
        _gen_iar_toolchain(project_dir, mcu)

        # VSCode configuration
        _gen_vscode_tasks(project_dir)
        _gen_vscode_launch(project_dir, mcu)
        _gen_vscode_settings(project_dir, feature_names)

        print(f"comsect1 full project ready: {root_path}")
        print(f"Unit: {unit}, MCU: {mcu}")
        if feature_names:
            print(f"Features: {', '.join(feature_names)}")
        print(f"CMake/VSCode at: {project_dir}")
    else:
        # Legacy mode: non-unit-qualified cfg_core.h / cfg_project.h
        cfg_core_path = root_path / "infra" / "bootstrap" / "cfg_core.h"
        write_if_missing(
            cfg_core_path,
            "\n".join(
                [
                    "#ifndef CFG_CORE_H",
                    "#define CFG_CORE_H",
                    "",
                    "/* comsect1 Core Contract header (shared types/interfaces). */",
                    "",
                    "#endif /* CFG_CORE_H */",
                    "",
                ]
            ),
        )

        cfg_project_path = root_path / "project" / "config" / "cfg_project.h"
        write_if_missing(
            cfg_project_path,
            "\n".join(
                [
                    "#ifndef CFG_PROJECT_H",
                    "#define CFG_PROJECT_H",
                    "",
                    "/* Project target interface header (customize per project).",
                    " * Praxis and Poiesis may include this header; Idea must not. */",
                    "",
                    "#endif /* CFG_PROJECT_H */",
                    "",
                ]
            ),
        )

        print(f"comsect1 scaffold ready: {root_path}")
        print("Created: project/, infra/, deps/ (and subfolders)")
        if feature_names:
            print(f"Features: {', '.join(feature_names)}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
