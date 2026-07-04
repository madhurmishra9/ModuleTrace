from datetime import datetime, timezone

from moduletrace.schemas.candidate import CleanupCandidate
from moduletrace.stages.s6_plan.hashing import compute_plan_hash


def _candidate(candidate_id: str = "c1") -> CleanupCandidate:
    return CleanupCandidate(
        candidate_id=candidate_id,
        reason="idle",
        action_type="targeted_destroy",
        resource_addresses=["module.vpc.aws_instance.this"],
        estimated_monthly_savings=42.0,
        blast_radius=1,
        risk_level="low",
    )


def test_hash_is_deterministic_for_identical_inputs():
    generated_at = datetime(2026, 7, 4, tzinfo=timezone.utc)
    state_versions = {"prod": "17"}
    candidates = [_candidate()]

    hash_a = compute_plan_hash("plan-1", candidates, state_versions, generated_at)
    hash_b = compute_plan_hash("plan-1", candidates, state_versions, generated_at)

    assert hash_a == hash_b
    assert len(hash_a) == 64  # sha256 hex digest


def test_hash_changes_when_state_version_changes():
    generated_at = datetime(2026, 7, 4, tzinfo=timezone.utc)
    candidates = [_candidate()]

    original = compute_plan_hash("plan-1", candidates, {"prod": "17"}, generated_at)
    drifted = compute_plan_hash("plan-1", candidates, {"prod": "18"}, generated_at)

    assert original != drifted


def test_hash_changes_when_candidates_change():
    generated_at = datetime(2026, 7, 4, tzinfo=timezone.utc)
    state_versions = {"prod": "17"}

    hash_one_candidate = compute_plan_hash("plan-1", [_candidate("c1")], state_versions, generated_at)
    hash_two_candidates = compute_plan_hash(
        "plan-1", [_candidate("c1"), _candidate("c2")], state_versions, generated_at
    )

    assert hash_one_candidate != hash_two_candidates


def test_hash_changes_when_plan_id_changes():
    generated_at = datetime(2026, 7, 4, tzinfo=timezone.utc)
    candidates = [_candidate()]
    state_versions = {"prod": "17"}

    assert compute_plan_hash("plan-1", candidates, state_versions, generated_at) != compute_plan_hash(
        "plan-2", candidates, state_versions, generated_at
    )
