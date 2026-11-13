"""Regression tests for SSRF wiring, webhook secret hashing, WS token parsing."""

from __future__ import annotations

import pytest

from fleetkit_api.routers.live import token_from_websocket
from fleetkit_api.routers.webhooks import (
    filter_ingest_headers,
    verify_webhook_signature,
)
from fleetkit_api.security import hash_api_key
from fleetkit_api.security_suite.redaction import redact_mapping
from fleetkit_api.security_suite.ssrf import SSRFBlocked, assert_safe_url, resolve_and_check


def test_ssrf_still_blocks_private_targets():
    with pytest.raises(SSRFBlocked):
        assert_safe_url("http://127.0.0.1/admin")
    with pytest.raises(SSRFBlocked):
        assert_safe_url("http://169.254.169.254/latest/meta-data/")
    with pytest.raises(SSRFBlocked):
        resolve_and_check("localhost")


def test_webhook_signature_hashed_and_legacy():
    raw = "whsec_test_value_please_rotate"
    digest = hash_api_key(raw)
    assert verify_webhook_signature(raw, digest)
    assert not verify_webhook_signature("wrong", digest)
    # Legacy plaintext rows still verify until upgraded on ingest.
    assert verify_webhook_signature(raw, raw)
    assert not verify_webhook_signature("nope", raw)
    assert not verify_webhook_signature(None, digest)


def test_ingest_headers_drop_auth_cookies():
    filtered = filter_ingest_headers(
        {
            "Authorization": "Bearer leak",
            "Cookie": "session=1",
            "X-FleetKit-Signature": "secret",
            "Content-Type": "application/json",
            "X-GitHub-Event": "push",
            "User-Agent": "hooks/1",
        }
    )
    assert "Authorization" not in filtered
    assert "Cookie" not in filtered
    assert "X-FleetKit-Signature" not in filtered
    assert filtered["Content-Type"] == "application/json"
    assert filtered["X-GitHub-Event"] == "push"


def test_channel_config_redaction():
    masked = redact_mapping(
        {"url": "https://hooks.example.com/x", "bot_token": "123:ABC", "chat_id": "9"}
    )
    assert masked["bot_token"] == "[REDACTED]"
    assert masked["url"] == "https://hooks.example.com/x"
    assert masked["chat_id"] == "9"


def test_ws_token_from_subprotocol():
    class _WS:
        def __init__(self, header: str | None):
            self.headers = {}
            if header is not None:
                self.headers["sec-websocket-protocol"] = header

    assert token_from_websocket(_WS("fleetkit-jwt, eyJhbGciOiJIUzI1NiJ9.a.b")) == (
        "eyJhbGciOiJIUzI1NiJ9.a.b"
    )
    assert token_from_websocket(_WS("fleetkit.eyJ.payload.sig")) == "eyJ.payload.sig"
    assert token_from_websocket(_WS(None)) is None
    assert token_from_websocket(_WS("chat, superchat")) is None


@pytest.mark.asyncio
async def test_http_fetch_ignores_allow_private_flag():
    from fleetkit_worker.builtin_jobs import http_fetch

    with pytest.raises(SSRFBlocked):
        await http_fetch({"url": "http://127.0.0.1/", "allow_private": True})
