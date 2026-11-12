import asyncio

from fleetkit_worker import builtin_jobs  # noqa: F401
from fleetkit_worker.handlers import get_handler


def test_ping_and_http_handlers_registered():
    assert get_handler("ping") is not None
    assert get_handler("http.fetch") is not None
    assert get_handler("system.info") is not None
    assert get_handler("text.stats") is not None


def test_util_hash_runs():
    handler = get_handler("util.hash")
    assert handler is not None
    result = asyncio.run(handler({"text": "abc", "algo": "sha256"}))
    assert "digest" in result
