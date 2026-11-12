from fleetkit_api.security_suite.fast_scan import fast_hits, needs_deep_scan
from fleetkit_api.security_suite.payload_guard import PayloadRejected, assert_payload_safe
from fleetkit_api.services.cache import TtlCache


def test_fast_scan_skips_benign():
    assert needs_deep_scan("hello world") is False
    assert fast_hits("normal payload") == []


def test_fast_scan_flags_ssrf_and_sqli():
    assert needs_deep_scan("http://127.0.0.1/admin") is True
    assert "sqli" in fast_hits("1' OR 1=1; DROP TABLE users")


def test_payload_guard_still_blocks_ssrf():
    try:
        assert_payload_safe({"url": "http://127.0.0.1/secret"})
        raise AssertionError("expected reject")
    except PayloadRejected:
        pass


def test_payload_guard_benign_is_fast():
    assert assert_payload_safe({"ok": True, "n": 3, "msg": "ping"}) == []


def test_ttl_cache_expires():
    cache = TtlCache()
    cache.set("a", 1, ttl_seconds=0.01)
    assert cache.get("a") == 1
    import time

    time.sleep(0.02)
    assert cache.get("a") is None


def test_ttl_cache_prefix_invalidate():
    cache = TtlCache()
    cache.set(("overview", "u1"), {"x": 1}, ttl_seconds=60)
    cache.set(("other", "u1"), {"y": 2}, ttl_seconds=60)
    cache.invalidate_prefix("overview")
    assert cache.get(("overview", "u1")) is None
    assert cache.get(("other", "u1")) == {"y": 2}
