"""Stage 5 output shape: resources/tag-groups flagged as safe-to-review-for-cleanup."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

ActionType = Literal["targeted_destroy", "tag_based_bulk_delete"]
RiskLevel = Literal["low", "medium", "high"]
CleanupReason = Literal["orphaned", "idle", "unused", "ttl_expired"]


class CleanupCandidate(BaseModel):
    """One unit of proposed cleanup, feeding into stage 6's plan generation."""

    candidate_id: str
    """Stable ID for this candidate within a run, e.g. a short hash of its resource addresses."""

    reason: CleanupReason
    action_type: ActionType

    resource_addresses: list[str]
    """Terraform resource addresses for `targeted_destroy`; empty for pure tag-based candidates."""

    tag_key: str | None = None
    tag_value: str | None = None
    """Set for `tag_based_bulk_delete` candidates."""

    estimated_monthly_savings: float
    blast_radius: int
    """Number of resources this candidate would affect."""

    risk_level: RiskLevel
    risk_reasons: list[str] = []
    """Why risk_level was escalated, e.g. "missing team tag", "referenced by module.other"."""
