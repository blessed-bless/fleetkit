from fleetkit_api.services.alerts import _compare, _is_slack_url, _send_smtp_sync


def test_compare_ops():
    assert _compare(3, ">", 2)
    assert _compare(2, ">=", 2)
    assert not _compare(1, ">", 2)
    assert _compare(1, "==", 1)


def test_slack_url_detect():
    assert _is_slack_url("https://hooks.slack.com/services/T/B/x")
    assert not _is_slack_url("https://example.com/hook")


def test_smtp_without_host_logs_and_ok(monkeypatch):
    import fleetkit_api.services.alerts as alerts_mod

    monkeypatch.setattr(
        alerts_mod,
        "get_settings",
        lambda: type(
            "S",
            (),
            {
                "smtp_host": "",
                "smtp_port": 587,
                "smtp_user": "",
                "smtp_password": "",
                "smtp_from": "",
                "smtp_tls": True,
            },
        )(),
    )
    assert _send_smtp_sync(to="a@b.c", subject="s", body="hi") is True
