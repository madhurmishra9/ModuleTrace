"""Stage 3 entrypoint: join stage2_normalized.json against billing adapters.

See docs/architecture.md, "Stage 3 — Multi-Cloud Billing Cross-Reference". Unjoinable resources
are kept with join_method="unattributed" rather than dropped (see "Open design risks" #1).
"""

from __future__ import annotations

from datetime import date

from moduletrace.schemas.billing import BilledResource
from moduletrace.schemas.normalized import NormalizedResource
from moduletrace.stages.s3_billing.base import BillingAdapter


def run(
    resources: list[NormalizedResource],
    adapters: dict[str, BillingAdapter],
    start: date,
    end: date,
) -> list[BilledResource]:
    """Join `resources` to cost data via the adapter for each resource's cloud.

    Join strategy: prefer `fetch_cost_by_resource_id` when
    `adapter.supports_resource_level_cost()` is True, else fall back to `fetch_cost_by_tag` using
    each resource's `moduletrace:workspace` (or another convention tag) as the grouping key.
    """
    raise NotImplementedError("stage 3 orchestration is not yet implemented")
