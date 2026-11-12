"""Symmetric secret box using Fernet-like HMAC+XOR fallback without extra deps.

Uses hashlib + HMAC derived from FLEETKIT_SECRET_KEY. Good enough for local vault;
swap to cryptography.Fernet in production if you prefer.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

from fleetkit_api.config import get_settings


def _key_bytes() -> bytes:
    raw = get_settings().secret_key.encode("utf-8")
    return hashlib.sha256(raw).digest()


def encrypt_text(plain: str) -> tuple[str, str]:
    key = _key_bytes()
    nonce = os.urandom(16)
    data = plain.encode("utf-8")
    # stream xor with HMAC-DRBG style keystream
    stream = b""
    counter = 0
    while len(stream) < len(data):
        stream += hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        counter += 1
    cipher = bytes(a ^ b for a, b in zip(data, stream[: len(data)], strict=True))
    tag = hmac.new(key, nonce + cipher, hashlib.sha256).digest()
    blob = base64.urlsafe_b64encode(tag + cipher).decode("ascii")
    return blob, base64.urlsafe_b64encode(nonce).decode("ascii")


def decrypt_text(ciphertext: str, nonce_b64: str) -> str:
    key = _key_bytes()
    nonce = base64.urlsafe_b64decode(nonce_b64.encode("ascii"))
    raw = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    tag, cipher = raw[:32], raw[32:]
    expect = hmac.new(key, nonce + cipher, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expect):
        raise ValueError("secret integrity check failed")
    stream = b""
    counter = 0
    while len(stream) < len(cipher):
        stream += hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        counter += 1
    plain = bytes(a ^ b for a, b in zip(cipher, stream[: len(cipher)], strict=True))
    return plain.decode("utf-8")
