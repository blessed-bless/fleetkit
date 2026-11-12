from fleetkit_api.middleware import AgentRateLimitMiddleware, RequestIdMiddleware
from fleetkit_worker import builtin_jobs  # noqa: F401
from fleetkit_worker.handlers import get_handler


def test_middleware_classes_exist():
    assert RequestIdMiddleware is not None
    assert AgentRateLimitMiddleware is not None


def test_transform_handlers_exist():
    assert get_handler("transform.map_keys") is not None
    assert get_handler("transform.filter_keys") is not None
    assert get_handler("batch.split") is not None
