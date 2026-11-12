from fleetkit_api.main import create_app


def test_healthz_route_wired():
    app = create_app()
    assert any(getattr(r, "path", None) == "/healthz" for r in app.routes)


def test_openapi_has_auth():
    app = create_app()
    paths = app.openapi()["paths"]
    assert "/api/v1/auth/login" in paths
