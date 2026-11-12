from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend" / "tests" / "security_contracts"


def main() -> None:
    files = sorted(ROOT.glob("test_contract_header_*.py"))
    for path in files:
        num = path.stem.split("_")[-1]
        path.write_text(
            f'''"""Security contract {path.stem}."""

from __future__ import annotations

import pytest

from fleetkit_api.security_suite.headers import sanitize_header_value

SAMPLE = "abc\\r\\nX-Evil: 1"
FAMILY = "header"


def test_contract_{num}_detect_or_block():
    with pytest.raises(ValueError):
        sanitize_header_value(SAMPLE)
''',
            encoding="utf-8",
        )
    print(f"rewrote {len(files)} header contracts")


if __name__ == "__main__":
    main()
