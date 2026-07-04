"""Stage 4 output shape: cost aggregated by module, workspace, and team."""

from __future__ import annotations

from pydantic import BaseModel


class WorkspaceCostBreakdown(BaseModel):
    workspace: str
    cost: float
    resource_count: int


class TeamCostBreakdown(BaseModel):
    team: str | None
    """None means the underlying resources had no `moduletrace:team` tag."""

    cost: float
    resource_count: int


class ModuleCostRollup(BaseModel):
    """Total attributed cost for one module (source + version) across all workspaces."""

    module_source: str
    module_version: str | None
    total_cost: float
    unattributed_cost: float
    """Cost that could not be joined to a specific resource/tag (see BilledResource.join_method)."""

    resource_count: int
    unattributed_resource_count: int
    per_workspace: list[WorkspaceCostBreakdown] = []
    per_team: list[TeamCostBreakdown] = []
