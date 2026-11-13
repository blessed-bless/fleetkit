#!/usr/bin/env python3
"""Print the CHANGELOG section for a given version (for GitHub Releases)."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: extract_changelog.py <version>", file=sys.stderr)
        return 2

    version = sys.argv[1].lstrip("v")
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^##\s+{re.escape(version)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        print(f"## {version}\n\nSee the commit history for details.")
        return 0

    body = match.group(1).strip()
    print(f"## {version}\n")
    print(body if body else "See the commit history for details.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
