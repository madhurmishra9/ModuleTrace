"""Stage 1 entrypoint: produce stage1_inventory.json from HCP Explorer + state sources.

See docs/architecture.md, "Stage 1 — Terraform State & HCP Explorer Scanner".
"""

from __future__ import annotations

from moduletrace.schemas.terraform import TerraformResourceRecord
from moduletrace.stages.s1_scanner.hcp_explorer import HcpExplorerClient
from moduletrace.stages.s1_scanner.state_reader import StateSource


def run(explorer: HcpExplorerClient, state_sources: list[StateSource]) -> list[TerraformResourceRecord]:
    """Discover module usage via Explorer, then pull full state for resource-level detail.

    Two-tier strategy: use `explorer` to decide which workspaces are in scope for a given query
    (e.g. "which workspaces use module X"), then only call `fetch_state()` on `state_sources` for
    those workspaces, to avoid O(workspaces) full state downloads when Explorer's summary already
    answers the question.
    """
    raise NotImplementedError("stage 1 orchestration is not yet implemented")
