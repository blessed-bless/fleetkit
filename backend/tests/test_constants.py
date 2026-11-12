from fleetkit_api.constants import (
    AGENT_RATE_LIMIT_PER_MINUTE,
    ALERT_METRICS,
    DEFAULT_QUEUES,
    MAX_BATCH_JOBS,
    MEMBER_ROLES,
    RETENTION_KINDS,
)


def test_constants_shape():
    assert "default" in DEFAULT_QUEUES
    assert "queue.depth" in ALERT_METRICS
    assert "jobs" in RETENTION_KINDS
    assert "viewer" in MEMBER_ROLES
    assert MAX_BATCH_JOBS == 500
    assert AGENT_RATE_LIMIT_PER_MINUTE == 120
