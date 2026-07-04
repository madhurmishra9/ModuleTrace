"""Canonical serialization and content-hashing for Plan artifacts.

The plan_hash is the anti-staleness mechanism described in docs/architecture.md: it binds a plan
to the exact candidate set and the state versions it was computed against, so a re-derived hash at
apply time will not match if state has changed underneath the plan.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from moduletrace.schemas.candidate import CleanupCandidate


def canonical_plan_payload(
    plan_id: str,
    candidates: list[CleanupCandidate],
    state_versions_used: dict[str, str],
    generated_at: datetime,
) -> str:
    """Deterministic JSON serialization of the fields that make up a plan_hash.

    Uses `sort_keys=True` and explicit separators so the same inputs always produce byte-identical
    output regardless of dict insertion order or platform whitespace defaults.
    """
    payload = {
        "plan_id": plan_id,
        "candidates": [c.model_dump(mode="json") for c in candidates],
        "state_versions_used": state_versions_used,
        "generated_at": generated_at.isoformat(),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_plan_hash(
    plan_id: str,
    candidates: list[CleanupCandidate],
    state_versions_used: dict[str, str],
    generated_at: datetime,
) -> str:
    """sha256 hex digest of `canonical_plan_payload(...)`."""
    payload = canonical_plan_payload(plan_id, candidates, state_versions_used, generated_at)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
