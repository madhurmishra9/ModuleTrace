"""Stage 6 entrypoint: turn stage5_candidates.json into an immutable, hashed Plan.

See docs/architecture.md, "Stage 6 — Plan Generation". Plans are never overwritten: regenerating
always produces a new plan_id (and thus a new plan_hash), forcing re-review.
"""

from __future__ import annotations

from datetime import datetime, timezone

from moduletrace.schemas.candidate import CleanupCandidate
from moduletrace.schemas.plan import Plan
from moduletrace.stages.s6_plan.hashing import compute_plan_hash


def run(
    plan_id: str, candidates: list[CleanupCandidate], state_versions_used: dict[str, str]
) -> Plan:
    generated_at = datetime.now(timezone.utc)
    plan_hash = compute_plan_hash(plan_id, candidates, state_versions_used, generated_at)
    return Plan(
        plan_id=plan_id,
        generated_at=generated_at,
        candidates=candidates,
        state_versions_used=state_versions_used,
        plan_hash=plan_hash,
        total_estimated_monthly_savings=sum(c.estimated_monthly_savings for c in candidates),
        total_blast_radius=sum(c.blast_radius for c in candidates),
    )
