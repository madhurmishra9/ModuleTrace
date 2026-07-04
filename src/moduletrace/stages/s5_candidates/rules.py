"""Per-resource-type cleanup heuristics.

Rules are per canonical_resource_type (not global) because "zero recent billing activity" is a
meaningful unused-signal for a compute instance but not for, say, an IAM role or security group.
See docs/architecture.md, "Stage 5 — Cleanup Candidate Analysis".
"""

from __future__ import annotations

from pydantic import BaseModel

from moduletrace.schemas.billing import BilledResource
from moduletrace.schemas.candidate import CleanupReason


class CleanupRule(BaseModel):
    """One tunable threshold set, loaded from the rules config (YAML)."""

    canonical_resource_type: str
    idle_cost_threshold_usd_per_month: float | None = None
    idle_min_age_days: int | None = None
    treat_zero_cost_as_unused: bool = False


def load_rules(path: str) -> list[CleanupRule]:
    raise NotImplementedError("rules config loading is not yet implemented")


def evaluate(resource: BilledResource, rules: list[CleanupRule]) -> CleanupReason | None:
    """Return the cleanup reason for `resource` under `rules`, or None if it's not a candidate.

    TTL-expiry is checked first (cheapest, least ambiguous signal), then idle/unused heuristics
    per the matching rule's `canonical_resource_type`, then orphan detection.
    """
    raise NotImplementedError("cleanup heuristics are not yet implemented")
