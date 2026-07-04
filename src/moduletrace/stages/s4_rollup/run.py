"""Stage 4 entrypoint: pure aggregation of stage3_billing_joined.json by module/workspace/team.

No API calls in this stage — see docs/architecture.md, "Stage 4 — Cost Attribution & Rollup", on
why it's split from stage 3 (so re-slicing the rollup doesn't re-hit rate-limited billing APIs).
"""

from __future__ import annotations

from moduletrace.schemas.billing import BilledResource
from moduletrace.schemas.rollup import ModuleCostRollup


def run(billed_resources: list[BilledResource]) -> list[ModuleCostRollup]:
    """Group `billed_resources` by (module_source, module_version) and roll up cost/counts,
    with per-workspace and per-team breakdowns, tracking unattributed cost/count separately.
    """
    raise NotImplementedError("stage 4 rollup aggregation is not yet implemented")
