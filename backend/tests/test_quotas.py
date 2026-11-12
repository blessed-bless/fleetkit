import asyncio

from fleetkit_api.services.quotas import ProjectQuota, assert_can_create_app


class _DummyScalar:
    def __init__(self, value):
        self.value = value

    async def scalar(self, *_args, **_kwargs):
        return self.value


def test_quota_dataclass_defaults():
    q = ProjectQuota()
    assert q.max_apps == 100
    assert q.max_secrets == 200


def test_assert_can_create_app_raises(monkeypatch):
    async def _run():
        class DB:
            async def scalar(self, *_a, **_k):
                return 100

        try:
            await assert_can_create_app(DB(), "p1", ProjectQuota(max_apps=100))
            raised = False
        except ValueError:
            raised = True
        assert raised

    asyncio.run(_run())
