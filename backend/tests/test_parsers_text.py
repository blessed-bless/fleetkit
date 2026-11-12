import asyncio

from fleetkit_worker import text_jobs  # noqa: F401
from fleetkit_worker.handlers import get_handler
from fleetkit_worker.parsers import chunked, deep_get, extract_emails, flatten, require_url


def test_parsers():
    assert extract_emails("mail me a@b.com and c@d.org") == ["a@b.com", "c@d.org"]
    assert require_url({"url": "https://example.com/x"}) == "https://example.com/x"
    assert deep_get({"a": {"b": 1}}, "a.b") == 1
    assert flatten({"a": {"b": 2}})["a.b"] == 2
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_text_stats_job():
    handler = get_handler("text.stats")
    assert handler is not None
    result = asyncio.run(handler({"text": "hello world hello"}))
    assert result["words"] == 3
