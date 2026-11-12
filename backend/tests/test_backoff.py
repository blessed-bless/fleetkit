from fleetkit_api.services.backoff import compute_backoff_seconds, describe_policy, next_retry_at


def test_backoff_bounds():
    for attempt in range(1, 8):
        delay = compute_backoff_seconds(attempt, base=2, cap=30)
        assert 0 <= delay <= 30


def test_next_retry_future():
    assert next_retry_at(1) is not None


def test_describe_policy():
    info = describe_policy(3, 3)
    assert info["exhausted"] is True
    assert info["attempt"] == 3
