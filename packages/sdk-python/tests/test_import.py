from fleetkit import FleetKit, FleetKitError


def test_exports():
    assert FleetKitError is not None
    assert callable(FleetKit)
