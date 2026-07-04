"""The human approval gate: requires the exact plan_hash, not a generic confirmation.

See docs/architecture.md, "Human approval gate design".
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from moduletrace.schemas.plan import Approval, Plan

DEFAULT_APPROVAL_VALIDITY = timedelta(days=7)


class HashMismatchError(Exception):
    """Raised when the hash passed to `approve()` doesn't match the plan's stored plan_hash."""


def approve(
    plan: Plan,
    provided_hash: str,
    approver: str,
    comment: str | None = None,
    validity: timedelta = DEFAULT_APPROVAL_VALIDITY,
) -> Approval:
    """Approve `plan`, requiring `provided_hash` to exactly match `plan.plan_hash`.

    This is the core of the gate: a human must have the real hash (from `plan.md` or `moduletrace
    show`) to approve, not just a plan_id. Raises `HashMismatchError` on any mismatch.
    """
    if provided_hash != plan.plan_hash:
        raise HashMismatchError(
            f"provided hash {provided_hash!r} does not match plan {plan.plan_id}'s hash"
        )
    approved_at = datetime.now(timezone.utc)
    return Approval(
        plan_id=plan.plan_id,
        plan_hash=plan.plan_hash,
        approver=approver,
        approved_at=approved_at,
        comment=comment,
        expires_at=approved_at + validity,
    )


def is_expired(approval: Approval, now: datetime | None = None) -> bool:
    return (now or datetime.now(timezone.utc)) > approval.expires_at
