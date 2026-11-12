"""Security contract test_contract_password_0142."""

from __future__ import annotations

import pytest

from fleetkit_api.security_suite.detectors.registry import any_suspicious, scan_text
from fleetkit_api.security_suite.headers import sanitize_header_value
from fleetkit_api.security_suite.password_policy import WeakPassword, validate_password
from fleetkit_api.security_suite.ssrf import SSRFBlocked, assert_safe_url

SAMPLE = 'password123'
FAMILY = 'password'


def test_contract_0142_detect_or_block():
    if FAMILY == "ssrf":
        with pytest.raises(SSRFBlocked):
            assert_safe_url(SAMPLE)
        return
    if FAMILY == "header":
        with pytest.raises(ValueError):
            sanitize_header_value(SAMPLE)
        return
    if FAMILY == "password":
        with pytest.raises(WeakPassword):
            validate_password(SAMPLE)
        return
    assert any_suspicious(SAMPLE, min_score=1) or scan_text(SAMPLE)
