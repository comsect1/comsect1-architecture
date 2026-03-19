#!/usr/bin/env python3
"""Validate comsect1 specification document hygiene."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from comsect1_gate_helpers import resolve_repo_root


def add_issue(issues: list[str], message: str) -> None:
    issues.append(message)


def has_utf8_bom(path: Path) -> bool:
    return path.read_bytes().startswith(b"\xef\xbb\xbf")


def get_file_text_utf8(path: Path) -> str:
    # Use utf-8-sig for parsing after BOM checks so content validation remains stable.
    return path.read_text(encoding="utf-8-sig")


def iter_repo_text_files(repo_root: Path) -> list[Path]:
    files: set[Path] = set()

    fixed_files = [
        repo_root / "README.md",
        repo_root / "AGENTS.md",
        repo_root / "CLAUDE.md",
        repo_root / ".editorconfig",
        repo_root / ".gitattributes",
    ]
    for file in fixed_files:
        if file.is_file():
            files.add(file)

    glob_patterns = [
        "specs/**/*.md",
        "guides/**/*.md",
        "tooling/**/*.md",
        "tooling/**/*.ps1",
        "tooling/**/*.sh",
        "tooling/**/*.yaml",
        "tooling/**/*.yml",
        "scripts/**/*.py",
    ]
    for pattern in glob_patterns:
        files.update(path for path in repo_root.glob(pattern) if path.is_file())

    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify comsect1 spec consistency.")
    parser.add_argument("-RepoRoot", dest="repo_root", default=None)
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = resolve_repo_root(script_path, args.repo_root)

    specs_dir = repo_root / "specs"
    readme_path = repo_root / "README.md"

    if not specs_dir.is_dir():
        raise RuntimeError(f"Missing folder: {specs_dir}")

    spec_files = sorted(specs_dir.glob("*.md"), key=lambda p: p.name)
    if not spec_files:
        raise RuntimeError(f"No spec files found in: {specs_dir}")

    issues: list[str] = []
    repo_text_files = iter_repo_text_files(repo_root)

    for file in repo_text_files:
        if has_utf8_bom(file):
            rel_path = file.relative_to(repo_root).as_posix()
            add_issue(issues, f"UTF-8 BOM is not allowed: {rel_path}")

    # Numbered sections: NN_slug.md
    # Appendices: A<index>_slug.md (e.g., A1_exception_handling.md)
    name_regex = re.compile(r"^(?:(?P<num>\d{2})|A(?P<appendixNum>\d+))_(?P<slug>[a-z0-9_]+)\.md$")

    for spec_file in spec_files:
        if not name_regex.match(spec_file.name):
            add_issue(
                issues,
                f"Invalid spec filename (expected NN_slug.md or A#_slug.md): specs/{spec_file.name}",
            )

    for spec_file in spec_files:
        match = name_regex.match(spec_file.name)
        if not match:
            continue

        is_numbered_file = match.group("num") is not None
        file_number = int(match.group("num")) if is_numbered_file else None
        text = get_file_text_utf8(spec_file)

        if "\ufffd" in text:
            add_issue(issues, f"Encoding replacement character (U+FFFD) found: specs/{spec_file.name}")

        lines = text.splitlines()
        first_non_empty = next((line for line in lines if line.strip()), None)
        if first_non_empty is None:
            add_issue(issues, f"Empty file: specs/{spec_file.name}")
            continue

        h1_is_numeric = False
        h1_number = None

        h1_numeric_match = re.match(r"^#\s*(?P<n>\d+)\.\s+", first_non_empty)
        if h1_numeric_match:
            h1_number = int(h1_numeric_match.group("n"))
            h1_is_numeric = True
            if is_numbered_file and file_number is not None and h1_number != file_number:
                add_issue(
                    issues,
                    f"H1 section number mismatch: specs/{spec_file.name} (H1={h1_number}, filename={file_number:02d})",
                )
        elif re.match(r"^#\s*Appendix\s+[A-Z]\.", first_non_empty):
            pass
        else:
            add_issue(
                issues,
                f"H1 does not start with a section number (expected '# N. ...' or 'Appendix X. ...'): specs/{spec_file.name}",
            )

        if h1_is_numeric and is_numbered_file and h1_number is not None:
            numbered_heading_regex = re.compile(r"^(?P<hash>#{2,6})\s+(?P<n>\d+)\.(?P<rest>.*)$")
            numbered_headings: list[tuple[int, str, int]] = []
            for idx, line in enumerate(lines, start=1):
                heading_match = numbered_heading_regex.match(line)
                if heading_match:
                    numbered_headings.append((idx, line, int(heading_match.group("n"))))

            if numbered_headings:
                distinct_ns = sorted({item[2] for item in numbered_headings})
                is_prefixed = len(distinct_ns) == 1 and distinct_ns[0] == h1_number
                is_local = 1 in distinct_ns
                if not is_prefixed and not is_local:
                    first = numbered_headings[0]
                    add_issue(
                        issues,
                        "Numbered headings do not match H1 N and do not start at 1: "
                        f"specs/{spec_file.name}:{first[0]} ('{first[1].strip()}')",
                    )

    # SSOT term consistency: detect use of inf_ as an actual file-role prefix
    # in code examples or file references (not in rules that forbid it).
    # Matches inf_<word>.<ext> used as a filename, excluding inline code backticks
    # where the spec is explaining "do not use inf_".
    inf_file_usage_re = re.compile(r"(?<!`)inf_\w+\.(?:c|h|py|cs|vb)\b")

    for spec_file in spec_files:
        text = get_file_text_utf8(spec_file)
        in_code_block = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if stripped.startswith("#") or stripped.startswith(">"):
                continue
            if inf_file_usage_re.search(line):
                add_issue(
                    issues,
                    f"SSOT term: specs/{spec_file.name}:{line_no} -- "
                    f"inf_ file-role prefix used in example (§2.7.8: inf_ is forbidden)",
                )

    # Cross-reference validation: verify §X.Y and Section X.Y references
    # Build heading registry from all spec files
    section_heading_re = re.compile(
        r"^#{1,6}\s+(?:(?P<major>\d+)\.(?P<minor>\d+(?:\.\d+)*)?)\s",
    )
    # Also match "Appendix X." headings
    appendix_heading_re = re.compile(
        r"^#{1,6}\s+Appendix\s+(?P<letter>[A-Z])(?P<minor>\d+)?\.?\s",
    )
    known_sections: set[str] = set()

    for spec_file in spec_files:
        text = get_file_text_utf8(spec_file)
        for line in text.splitlines():
            m = section_heading_re.match(line)
            if m:
                major = m.group("major")
                minor = m.group("minor")
                if minor:
                    known_sections.add(f"{major}.{minor}")
                known_sections.add(major)
                continue
            m = appendix_heading_re.match(line)
            if m:
                letter = m.group("letter")
                app_minor = m.group("minor")
                if app_minor:
                    known_sections.add(f"A{app_minor}")
                known_sections.add(f"Appendix {letter}")

    # Scan for cross-references: §X.Y, Section X.Y, §X
    xref_re = re.compile(r"(?:§|Section\s+)(\d+(?:\.\d+)*)")
    for spec_file in spec_files:
        text = get_file_text_utf8(spec_file)
        for line_no, line in enumerate(text.splitlines(), start=1):
            # Skip lines that define headings (they are definitions, not references)
            if line.lstrip().startswith("#"):
                continue
            for m in xref_re.finditer(line):
                ref = m.group(1)
                # Check if the major section exists
                major_part = ref.split(".")[0]
                if major_part not in known_sections and ref not in known_sections:
                    add_issue(
                        issues,
                        f"Broken cross-reference '§{ref}': specs/{spec_file.name}:{line_no}",
                    )

    # -----------------------------------------------------------------------
    # SSOT restatement detection: warn when a normative rule is fully
    # restated outside its designated Single Source of Truth file.
    # -----------------------------------------------------------------------

    # Each entry: rule-id -> (ssot filename, compiled regex pattern)
    # The pattern matches FULL restatements, not brief "see §X" references.
    _ssot_rules: list[tuple[str, str, re.Pattern[str]]] = [
        (
            "dep-direction",
            "05_dependency_rules.md",
            re.compile(
                r"IDA\s*->\s*\{\s*own\s+PRX\s*,\s*own\s+POI\s*\}",
            ),
        ),
        (
            "ida-self-contain",
            "04_layer_roles.md",
            re.compile(
                r"[Ii]dea\s+(?:must\s+not|does\s+not|cannot)\s+(?:include|access|depend\s+on|import)"
                r".*(?:mdw_|svc_|hal_|bsp_)",
            ),
        ),
        (
            "feature-isolation",
            "05_dependency_rules.md",
            re.compile(
                r"[Ff]eature\s*(?:<->|↔|\sto\s)\s*[Ff]eature.*stm_\s*only",
            ),
        ),
        (
            "hal-bsp-direction",
            "05_dependency_rules.md",
            re.compile(
                r"(?:^|\s)HAL\s*->\s*BSP(?:\s|$)",
            ),
        ),
        (
            "cross-feature-prohibition",
            "05_dependency_rules.md",
            re.compile(
                r"(?:prx_|poi_).*must\s+not\s+include\s+(?:another|other)\s+feature",
                re.IGNORECASE,
            ),
        ),
    ]

    # Files that are exempt from restatement warnings:
    # - 09_code_examples.md: illustrative, non-normative
    # - 12_version_history.md: historical record (low priority, warn anyway
    #   for full restatements but we can suppress later if needed)
    _ssot_exempt_files: set[str] = {"09_code_examples.md"}

    # Rules whose signatures commonly appear inside code-block diagrams
    # and should still be checked there.
    _ssot_check_in_code_blocks: set[str] = {
        "dep-direction",
        "hal-bsp-direction",
        "feature-isolation",
    }

    ssot_warnings: list[str] = []
    for spec_file in spec_files:
        if spec_file.name in _ssot_exempt_files:
            continue
        text = get_file_text_utf8(spec_file)
        in_code_block = False
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            for rule_id, ssot_file, pattern in _ssot_rules:
                if in_code_block and rule_id not in _ssot_check_in_code_blocks:
                    continue
                if spec_file.name == ssot_file:
                    continue  # this IS the SSOT file
                if pattern.search(line):
                    ssot_warnings.append(
                        f"SSOT restatement: specs/{spec_file.name}:{line_no} -- "
                        f"rule '{rule_id}' restated outside SSOT "
                        f"(canonical: specs/{ssot_file})"
                    )

    if ssot_warnings:
        print(f"\nSSOT restatement warnings: {len(ssot_warnings)}")
        for w in ssot_warnings:
            print(f"  (advisory) {w}")

    # Lightweight README hygiene checks
    if readme_path.is_file():
        readme = get_file_text_utf8(readme_path)
        if "\ufffd" in readme:
            add_issue(issues, "Encoding replacement character (U+FFFD) found: README.md")
        if re.search(r"\?{2,}", readme):
            add_issue(issues, "Suspicious '??' sequences found: README.md (likely encoding artifacts)")
    else:
        add_issue(issues, "README.md not found")

    print("Spec verification complete.")
    print(f"Issues: {len(issues)}")
    for message in issues:
        print(f"- {message}")

    if issues:
        print(f"\nGate FAILED -- {len(issues)} issue(s) must be resolved.")
    else:
        print("\nGate passed -- no issues found.")

    return 2 if issues else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
