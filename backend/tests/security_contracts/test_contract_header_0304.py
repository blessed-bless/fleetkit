"""Security contract test_contract_header_0304."""

from __future__ import annotations

import pytest

from fleetkit_api.security_suite.headers import sanitize_header_value

SAMPLE = "abc\r\nX-Evil: 1"
FAMILY = "header"


def test_contract_0304_detect_or_block():
    with pytest.raises(ValueError):
        sanitize_header_value(SAMPLE)
