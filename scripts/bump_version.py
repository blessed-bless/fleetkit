#!/usr/bin/env python3
"""Sync package versions across backend, SDK, CLI and frontend."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TARGETS = [
    ROOT / "backend" / "pyproject.toml",
    ROOT / "backend" / "fleetkit_api" / "__init__.py",
    ROOT / "backend" / "fleetkit_worker" / "__init__.py",
    ROOT / "packages" / "sdk-python" / "pyproject.toml",
    ROOT / "packages" / "sdk-python" / "src" / "fleetkit" / "__init__.py",
    ROOT / "packages" / "cli" / "pyproject.toml",
    ROOT / "packages" / "cli" / "src" / "fleetkit_cli" / "__init__.py",
    ROOT / "frontend" / "package.json",
]


def replace_version(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".toml":
        updated, n = re.subn(
            r'(?m)^version\s*=\s*"[^"]+"',
            f'version = "{version}"',
            text,
            count=1,
        )
    elif path.name == "package.json":
        updated, n = re.subn(
            r'"version"\s*:\s*"[^"]+"',
            f'"version": "{version}"',
            text,
            count=1,
        )
    else:
        updated, n = re.subn(
            r'__version__\s*=\s*"[^"]+"',
            f'__version__ = "{version}"',
            text,
            count=1,
        )
    if n != 1:
        raise SystemExit(f"failed to update version in {path}")
    path.write_text(updated, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: bump_version.py <version>", file=sys.stderr)
        return 2
    version = sys.argv[1].lstrip("v")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[.-][0-9A-Za-z.]+)?", version):
        print(f"invalid version: {version}", file=sys.stderr)
        return 2
    for path in TARGETS:
        replace_version(path, version)
        print(f"updated {path.relative_to(ROOT)} -> {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
