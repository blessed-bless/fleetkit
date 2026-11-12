from __future__ import annotations

import re


class WeakPassword(ValueError):
    pass


_COMMON = {
    "password",
    "password123",
    "12345678",
    "qwerty123",
    "fleetkit-admin",
    "admin123",
    "letmein",
}


def validate_password(password: str, *, min_len: int = 10) -> None:
    if len(password) < min_len:
        raise WeakPassword(f"password must be at least {min_len} chars")
    if password.lower() in _COMMON:
        raise WeakPassword("password is too common")
    classes = 0
    if re.search(r"[a-z]", password):
        classes += 1
    if re.search(r"[A-Z]", password):
        classes += 1
    if re.search(r"\d", password):
        classes += 1
    if re.search(r"[^A-Za-z0-9]", password):
        classes += 1
    if classes < 3:
        raise WeakPassword("password needs mixed case, digits and/or symbols")
