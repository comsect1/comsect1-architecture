#!/usr/bin/env python3
"""Create a minimal comsect1 scaffold layout."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


INVALID_WINDOWS_CHARS = set('<>:"/\\|?*')


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
    args = parser.parse_args()

    root_path = Path(args.path).resolve()
    root_path.mkdir(parents=True, exist_ok=True)

    relative_dirs = [
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

    feature_names = normalize_feature_args(args.features)
    for feature_name in feature_names:
        assert_valid_feature_name(feature_name)
        (root_path / "project" / "features" / feature_name).mkdir(parents=True, exist_ok=True)

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
