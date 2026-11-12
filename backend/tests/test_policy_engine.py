from fleetkit_api.services.policy_engine import (
    PolicyContext,
    bulk_suggest,
    evaluate_claim_policy,
    evaluate_enqueue_policy,
    explain_decision,
    score_job_urgency,
    suggest_queue,
)


def test_kill_switch():
    ctx = PolicyContext(project_id="p", feature_flags={"kill_switch": True})
    d = evaluate_enqueue_policy(ctx, job_name="ping", queue="default")
    assert d.allow is False


def test_suggest_queue():
    assert suggest_queue("cron.heartbeat") == "scheduled"
    assert suggest_queue("webhook.received") == "webhooks"
    assert suggest_queue("ping") == "default"


def test_claim_capability():
    ctx = PolicyContext(project_id="p", labels={"requires": "gpu"})
    deny = evaluate_claim_policy(ctx, worker_labels={"capability": "cpu"})
    allow = evaluate_claim_policy(ctx, worker_labels={"capability": "gpu"})
    assert deny.allow is False
    assert allow.allow is True


def test_score_and_explain():
    assert score_job_urgency(attempt=2, queue="priority", age_seconds=120) > 5
    d = evaluate_enqueue_policy(PolicyContext(project_id="p"), job_name="ping", queue="default")
    assert "allow" in explain_decision(d)


def test_bulk_suggest():
    mapping = bulk_suggest(["ping", "webhook.received", "schedule:x"])
    assert mapping["webhook.received"] == "webhooks"
