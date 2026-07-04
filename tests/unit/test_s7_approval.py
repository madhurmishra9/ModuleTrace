from datetime import datetime, timedelta, timezone

import pytest

from moduletrace.schemas.candidate import CleanupCandidate
from moduletrace.stages.s6_plan.run import run as generate_plan
from moduletrace.stages.s7_gate.approval import HashMismatchError, approve, is_expired


def _plan():
    candidate = CleanupCandidate(
        candidate_id="c1",
        reason="idle",
        action_type="targeted_destroy",
        resource_addresses=["module.vpc.aws_instance.this"],
        estimated_monthly_savings=42.0,
        blast_radius=1,
        risk_level="low",
    )
    return generate_plan("plan-1", [candidate], {"prod": "17"})


def test_approve_succeeds_with_matching_hash():
    plan = _plan()

    approval = approve(plan, plan.plan_hash, approver="alice@example.com")

    assert approval.plan_id == plan.plan_id
    assert approval.plan_hash == plan.plan_hash
    assert not is_expired(approval)


def test_approve_rejects_wrong_hash():
    plan = _plan()

    with pytest.raises(HashMismatchError):
        approve(plan, "not-the-real-hash", approver="alice@example.com")


def test_approval_expiry_window_is_respected():
    plan = _plan()

    approval = approve(plan, plan.plan_hash, approver="alice@example.com", validity=timedelta(days=7))

    assert not is_expired(approval, now=approval.approved_at + timedelta(days=6))
    assert is_expired(approval, now=approval.approved_at + timedelta(days=8))
