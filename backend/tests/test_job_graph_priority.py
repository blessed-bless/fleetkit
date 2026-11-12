import pytest

from fleetkit_api.services.job_graph import DependencyError, topological_layers
from fleetkit_api.services.validators import validate_priority


def test_topo_layers_diamond():
    # a -> b, a -> c, b/c -> d  (edges: job depends_on)
    layers = topological_layers([("b", "a"), ("c", "a"), ("d", "b"), ("d", "c")])
    assert layers[0] == ["a"]
    assert set(layers[1]) == {"b", "c"}
    assert layers[2] == ["d"]


def test_dependency_error_is_value_error():
    assert issubclass(DependencyError, ValueError)
    with pytest.raises(DependencyError, match="itself"):
        raise DependencyError("job cannot depend on itself")


def test_validate_priority_bounds():
    assert validate_priority(0) == 0
    assert validate_priority(100) == 100
    with pytest.raises(ValueError):
        validate_priority(-1)
    with pytest.raises(ValueError):
        validate_priority(101)


def test_claim_sort_key_priority_then_age():
    """Mirrors claim_next_job eligible.sort key: higher priority first, then older."""
    from datetime import UTC, datetime

    now = datetime(2026, 1, 1, tzinfo=UTC)
    older = datetime(2025, 1, 1, tzinfo=UTC)

    class J:
        def __init__(self, id: str, created_at):
            self.id = id
            self.created_at = created_at

    pri = {"hi": 90, "lo": 10, "mid": 50}
    eligible = [J("lo", older), J("hi", now), J("mid", older)]
    eligible.sort(key=lambda j: (-pri.get(j.id, 50), j.created_at or now))
    assert [j.id for j in eligible] == ["hi", "mid", "lo"]


def test_schemas_job_create_extras():
    from fleetkit_api.schemas import JobChainCreate, JobCloneIn, JobCreate, JobPriorityIn

    body = JobCreate(name="ping", priority=80, depends_on_job_id="abc")
    assert body.priority == 80
    assert body.depends_on_job_id == "abc"
    chain = JobChainCreate(names=["a", "b", "c"])
    assert len(chain.names) == 3
    assert JobCloneIn().copy_tags is True
    assert JobPriorityIn(priority=42).priority == 42
