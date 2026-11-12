from fleetkit_api.security import (
    create_access_token,
    decode_access_token,
    hash_api_key,
    hash_password,
    verify_password,
)


def test_password_roundtrip():
    hashed = hash_password("fleetkit-admin")
    assert verify_password("fleetkit-admin", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip():
    token = create_access_token("user-1", extra={"email": "a@b.c"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["email"] == "a@b.c"


def test_api_key_hash_stable():
    assert hash_api_key("fk_abc") == hash_api_key("fk_abc")
    assert hash_api_key("fk_abc") != hash_api_key("fk_xyz")
