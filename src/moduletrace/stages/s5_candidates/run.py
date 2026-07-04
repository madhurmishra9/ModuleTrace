"""Stage 5 entrypoint: classify cleanup candidates from stage3/stage4 output + rules config.

See docs/architecture.md, "Stage 5 — Cleanup Candidate Analysis" for the action-type
(targeted_destroy vs tag_based_bulk_delete) and risk_level (auto-escalation) logic.
"""

from __future__ import annotations

from moduletrace.schemas.billing import BilledResource
from moduletrace.schemas.candidate import CleanupCandidate
from moduletrace.schemas.rollup import ModuleCostRollup
from moduletrace.stages.s5_candidates.rules import CleanupRule


def run(
    billed_resources: list[BilledResource],
    rollups: list[ModuleCostRollup],
    rules: list[CleanupRule],
) -> list[CleanupCandidate]:
    """Evaluate `rules` against `billed_resources`, classify each match into an action_type, and
    compute risk_level (escalating to "high" for missing-team-tag or cross-module references).
    """
    raise NotImplementedError("stage 5 candidate classification is not yet implemented")
