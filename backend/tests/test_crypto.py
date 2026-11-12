import pytest

from fleetkit_api.crypto_box import decrypt_text, encrypt_text


def test_encrypt_roundtrip(monkeypatch):
    monkeypatch.setenv("FLEETKIT_SECRET_KEY", "unit-test-secret-key")
    from fleetkit_api.config import get_settings

    get_settings.cache_clear()
    blob, nonce = encrypt_text("super-secret-value")
    assert decrypt_text(blob, nonce) == "super-secret-value"
    get_settings.cache_clear()


def test_tamper_detected(monkeypatch):
    monkeypatch.setenv("FLEETKIT_SECRET_KEY", "unit-test-secret-key")
    from fleetkit_api.config import get_settings

    get_settings.cache_clear()
    blob, nonce = encrypt_text("abc")
    with pytest.raises(ValueError):
        decrypt_text(blob[:-1] + ("A" if blob[-1] != "A" else "B"), nonce)
    get_settings.cache_clear()
