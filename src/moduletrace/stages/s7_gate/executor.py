"""Plan execution: re-validate against live state, then destroy/delete, with per-resource audit logging.

See docs/architecture.md, "Human approval gate design" for the re-validation, drift-skip, and
resumability behavior this stage must implement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from moduletrace.schemas.plan import Approval, AuditEntry, Plan
from moduletrace.stages.s7_gate.approval import is_expired
from moduletrace.stages.s7_gate.audit import read_entries

OnDriftPolicy = Literal["skip", "abort"]


class ApprovalExpiredError(Exception):
    pass


class ApprovalMismatchError(Exception):
    """Raised when approval.plan_hash doesn't match plan.plan_hash (possible tampering)."""


def apply(
    plan: Plan,
    approval: Approval,
    audit_log_path: Path,
    on_drift: OnDriftPolicy = "skip",
) -> None:
    """Execute `plan`'s candidates, having already been approved via `approval`.

    Required checks before executing anything:
    1. `approval.plan_hash == plan.plan_hash` (else ApprovalMismatchError).
    2. `not is_expired(approval)` (else ApprovalExpiredError).
    3. Resume support: `read_entries(audit_log_path)` to skip candidates already executed by a
       prior, interrupted run of this same plan_id.

    Per-candidate: a live drift re-check (resource still exists / tags still match what the plan
    recorded) determines whether to execute or, under `on_drift="skip"`, log
    `outcome="skipped_state_drift"` and move on rather than aborting the whole run.
    Actual execution (terraform destroy -target=, or direct cloud SDK delete for
    tag_based_bulk_delete) is not yet implemented.
    """
    if approval.plan_hash != plan.plan_hash:
        raise ApprovalMismatchError(
            f"approval for plan {plan.plan_id} does not match the plan's current hash"
        )
    if is_expired(approval):
        raise ApprovalExpiredError(f"approval for plan {plan.plan_id} expired at {approval.expires_at}")

    already_executed = {e.candidate_id for e in read_entries(audit_log_path)}
    remaining = [c for c in plan.candidates if c.candidate_id not in already_executed]

    raise NotImplementedError(
        f"execution of {len(remaining)} remaining candidate(s) is not yet implemented "
        "(terraform destroy -target= / cloud SDK delete)"
    )
