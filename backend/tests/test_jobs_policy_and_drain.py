import hashlib
import hmac
import time

from fleetkit_api.models import WorkerStatus
from fleetkit_api.routers.webhooks import _signature_ok
from fleetkit_api.services.jobs import PolicyDenied
from fleetkit_api.services.policy_engine import (
    PolicyContext,
    evaluate_claim_policy,
    evaluate_enqueue_policy,
    suggest_queue,
)


def test_policy_denied_exposes_reason():
    err = PolicyDenied("kill_switch enabled")
    assert err.reason == "kill_switch enabled"
    assert "kill_switch" in str(err)


def test_enqueue_kill_switch_blocks():
    d = evaluate_enqueue_policy(
        PolicyContext(project_id="p", feature_flags={"kill_switch": True}),
        job_name="ping",
        queue="default",
    )
    assert d.allow is False


def test_claim_drain_mode_blocks():
    d = evaluate_claim_policy(
        PolicyContext(project_id="p", feature_flags={"drain_mode": True}),
        worker_labels={},
    )
    assert d.allow is False


def test_claim_capability_gate():
    ctx = PolicyContext(project_id="p", labels={"requires": "gpu"})
    assert evaluate_claim_policy(ctx, worker_labels={"capability": "cpu"}).allow is False
    assert evaluate_claim_policy(ctx, worker_labels={"capability": "gpu"}).allow is True


def test_suggest_queue_for_webhook_and_cron():
    assert suggest_queue("webhook.received") == "webhooks"
    assert suggest_queue("cron.heartbeat") == "scheduled"


def test_worker_status_has_draining():
    assert WorkerStatus.draining.value == "draining"


def test_retry_rejects_running_status_via_policy_denied_type():
    # retry_job raises PolicyDenied for non-terminal statuses — type contract
    from fleetkit_api.services import jobs as jobsvc

    assert issubclass(jobsvc.PolicyDenied, RuntimeError)


def test_webhook_signature_raw_and_hmac():
    secret = "s3cret"
    body = b'{"ok":true}'
    assert _signature_ok(secret, body, secret) is True
    assert _signature_ok(secret, body, "wrong") is False

    ts = int(time.time())
    digest = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={digest}"
    assert _signature_ok(secret, body, header) is True
    assert _signature_ok(secret, body, f"t={ts},v1=deadbeef") is False
