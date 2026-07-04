"""Stage 6/7 shapes: the immutable Plan artifact, its Approval, and audit trail."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from moduletrace.schemas.candidate import CleanupCandidate

AuditOutcome = Literal["succeeded", "failed", "skipped_state_drift"]


class Plan(BaseModel):
    """An immutable, content-hashed cleanup plan. Always written as a new plan_id; never mutated."""

    plan_id: str
    generated_at: datetime
    candidates: list[CleanupCandidate]

    state_versions_used: dict[str, str]
    """workspace -> state_version, exactly as seen when candidates were computed.

    Included in the plan_hash so that state drift between plan generation and apply is detectable.
    """

    plan_hash: str
    """sha256 of the canonical serialization of (plan_id, candidates, state_versions_used, generated_at).

    See stages/s6_plan/hashing.py for the canonical serialization + hash function.
    """

    total_estimated_monthly_savings: float
    total_blast_radius: int


class Approval(BaseModel):
    """Human sign-off on a specific Plan, keyed by its exact plan_hash."""

    plan_id: str
    plan_hash: str
    approver: str
    approved_at: datetime
    comment: str | None = None
    expires_at: datetime
    """approved_at + the configured approval validity window (default 7 days)."""


class AuditEntry(BaseModel):
    """One line in a plan's append-only audit_log.jsonl, written during apply."""

    plan_id: str
    candidate_id: str
    resource_address: str | None = None
    tag_value: str | None = None
    outcome: AuditOutcome
    detail: str | None = None
    executed_at: datetime
