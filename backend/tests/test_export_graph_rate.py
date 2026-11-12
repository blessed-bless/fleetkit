from fleetkit_api.services.job_graph import topological_layers
from fleetkit_api.services.rate_limit import MemoryRateLimiter


def test_topo_layers_linear():
    layers = topological_layers([("b", "a"), ("c", "b")])
    assert layers[0] == ["a"]
    assert "b" in layers[1]
    assert "c" in layers[2]


def test_topo_layers_empty():
    assert topological_layers([]) == []


def test_rate_limiter():
    lim = MemoryRateLimiter()
    assert lim.allow("k", limit=2, window_seconds=60)
    assert lim.allow("k", limit=2, window_seconds=60)
    assert not lim.allow("k", limit=2, window_seconds=60)
    assert lim.remaining("k", limit=2, window_seconds=60) == 0
