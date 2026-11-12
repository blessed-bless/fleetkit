import pytest

from fleetkit_api.security_suite.headers import sanitize_header_map, sanitize_header_value
from fleetkit_api.security_suite.password_policy import WeakPassword, validate_password
from fleetkit_api.security_suite.rbac import Permission, role_allows
from fleetkit_api.security_suite.redaction import redact_mapping, redact_text
from fleetkit_api.security_suite.ssrf import SSRFBlocked, assert_safe_url, is_blocked_host


def test_ssrf_blocks_localhost_and_metadata():
    assert is_blocked_host("localhost")
    assert is_blocked_host("127.0.0.1")
    assert is_blocked_host("169.254.169.254")
    assert is_blocked_host("metadata.google.internal")
    with pytest.raises(SSRFBlocked):
        assert_safe_url("http://127.0.0.1/secret")
    with pytest.raises(SSRFBlocked):
        assert_safe_url("http://user:pass@example.com/")


def test_redaction_masks_tokens_and_keys():
    text = "Authorization: Bearer abc.def and api_key=supersecret fk_abcdefghijklmnop"
    red = redact_text(text)
    assert "supersecret" not in red
    assert "fk_abcdefghijklmnop" not in red
    assert "[REDACTED]" in red
    payload = redact_mapping({"token": "x", "nested": {"password": "y"}, "ok": 1})
    assert payload["token"] == "[REDACTED]"
    assert payload["nested"]["password"] == "[REDACTED]"
    assert payload["ok"] == 1


def test_rbac_matrix():
    assert role_allows("viewer", Permission.job_read)
    assert not role_allows("viewer", Permission.secret_reveal)
    assert role_allows("admin", Permission.secret_reveal)
    assert role_allows("owner", Permission.import_cfg)


def test_header_crlf_rejected():
    with pytest.raises(ValueError):
        sanitize_header_value("evil\r\nX-Injected: 1")
    cleaned = sanitize_header_map({"X-Trace": "ok", "Host": "evil"})
    assert "Host" not in cleaned
    assert cleaned["X-Trace"] == "ok"


def test_password_policy():
    with pytest.raises(WeakPassword):
        validate_password("short")
    with pytest.raises(WeakPassword):
        validate_password("fleetkit-admin")
    validate_password("Str0ng!Pass99")
