#!/usr/bin/env python3
"""Validate comsect1 specification document hygiene."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def add_issue(issues: list[str], message: str) -> None:
    issues.append(message)


def get_file_text_utf8(path: Path) -> str:
    # Use utf-8-sig to match prior PowerShell behavior and ignore optional BOM.
    return path.read_text(encoding="utf-8-sig")


def resolve_repo_root(script_path: Path, repo_root_arg: str | None) -> Path:
    if repo_root_arg:
        return Path(repo_root_arg).resolve()
    return (script_path.parent / "..").resolve()


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

    return 2 if issues else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
