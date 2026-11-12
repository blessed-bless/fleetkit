from fleetkit_api.models_ext import AlertSeverity
from fleetkit_api.services.alerts import EXPR_RE, _compare, parse_severity


def test_expr_parse():
    m = EXPR_RE.match("queue.depth>10")
    assert m is not None
    assert m.group("metric") == "queue.depth"
    assert m.group("op") == ">"
    assert m.group("value") == "10"


def test_compare_ops():
    assert _compare(5, ">", 3)
    assert _compare(5, ">=", 5)
    assert _compare(2, "<", 3)
    assert _compare(2, "<=", 2)
    assert _compare(2, "==", 2)


def test_severity():
    assert parse_severity("critical") == AlertSeverity.critical
    assert parse_severity("nope") == AlertSeverity.warning
