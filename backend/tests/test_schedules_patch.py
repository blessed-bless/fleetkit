from fleetkit_api.routers.schedules import SchedulePatch


def test_schedule_patch_schema_defaults():
    body = SchedulePatch()
    assert body.is_enabled is None
    assert body.cron is None
    assert body.name is None


def test_schedule_patch_partial():
    body = SchedulePatch(is_enabled=False)
    assert body.is_enabled is False
    assert body.cron is None
