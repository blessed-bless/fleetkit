from datetime import UTC, datetime
from types import SimpleNamespace

from fleetkit_api.services.serializers import app_dict, job_dict, project_dict


def test_project_dict():
    p = SimpleNamespace(
        id="1",
        slug="default",
        name="Default",
        description="x",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    data = project_dict(p)
    assert data["slug"] == "default"
    assert data["created_at"].startswith("2026")


def test_app_and_job_dict():
    a = SimpleNamespace(
        id="a",
        project_id="p",
        slug="bot",
        name="Bot",
        kind="bot",
        config={},
        is_enabled=True,
        created_at=None,
    )
    j = SimpleNamespace(
        id="j",
        app_id="a",
        worker_id=None,
        queue="default",
        name="ping",
        status=SimpleNamespace(value="queued"),
        payload={},
        result=None,
        error=None,
        attempt=0,
        max_attempts=3,
        timeout_seconds=300,
        scheduled_for=None,
        started_at=None,
        finished_at=None,
        created_at=None,
    )
    assert app_dict(a)["slug"] == "bot"
    assert job_dict(j)["status"] == "queued"
