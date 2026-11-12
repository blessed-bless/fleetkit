from fleetkit import (
    FleetKit,
    build_ingest_url,
    parse_event,
    sign_payload,
    verify_signature,
)
from fleetkit import __version__


def test_version_bumped():
    assert __version__.startswith("0.2")


def test_sign_and_verify_roundtrip():
    body = b'{"hello":"world"}'
    header = sign_payload("sekrit", body, timestamp=1_700_000_000)
    assert verify_signature("sekrit", body, header, now=1_700_000_000)
    assert not verify_signature("wrong", body, header, now=1_700_000_000)


def test_build_ingest_and_parse():
    url = build_ingest_url("http://localhost:8000/", "tok123")
    assert url.endswith("/api/v1/hooks/tok123")
    ev = parse_event({"type": "push", "data": {"x": 1}})
    assert ev["event"] == "push"
    assert ev["data"]["x"] == 1


def test_fleetkit_has_claim_batch_and_drain():
    assert hasattr(FleetKit, "claim_batch")
    assert hasattr(FleetKit, "drain")
    assert hasattr(FleetKit, "run_loop")
