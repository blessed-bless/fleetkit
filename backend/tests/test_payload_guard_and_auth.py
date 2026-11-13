import pytest

from fleetkit_api.security_suite.auth_hardening import (
    LoginProtector,
    is_insecure_bootstrap_password,
)
from fleetkit_api.security_suite.payload_guard import PayloadRejected, assert_payload_safe


def test_payload_guard_blocks_ssrf_url():
    with pytest.raises(PayloadRejected):
        assert_payload_safe({"url": "http://127.0.0.1/secret"})


def test_payload_guard_allows_benign():
    assert assert_payload_safe({"hello": "world", "n": 1}) == []


def test_login_lockout():
    protector = LoginProtector(max_failures=3, window_seconds=60, lock_seconds=30)
    assert not protector.is_locked("u1")
    protector.register_failure("u1")
    protector.register_failure("u1")
    assert not protector.is_locked("u1")
    protector.register_failure("u1")
    assert protector.is_locked("u1")
    protector.register_success("u1")
    assert not protector.is_locked("u1")


def test_bootstrap_password_flag():
    assert is_insecure_bootstrap_password("fleetkit-admin")
    assert not is_insecure_bootstrap_password("Str0ng!Pass99")
