"""HCP Terraform Explorer API client.

Explorer gives a queryable cross-workspace view (resource counts, module usage, providers) without
pulling every state file. Used as a fast inventory/filter pass before falling back to full state
reads (state_reader.py) for workspaces that need resource-level attribute detail.
"""

from __future__ import annotations

from pydantic import BaseModel


class ExplorerWorkspaceSummary(BaseModel):
    workspace_id: str
    workspace_name: str
    module_sources: list[str]
    resource_count: int


class HcpExplorerClient:
    """Thin REST client over the HCP Terraform Explorer API.

    No official Python SDK exists for Explorer specifically; this wraps `httpx` calls against the
    Terraform Cloud/Enterprise API's explorer/query endpoints.
    """

    def __init__(self, api_token: str, org: str, base_url: str = "https://app.terraform.io") -> None:
        self.api_token = api_token
        self.org = org
        self.base_url = base_url

    def list_workspaces_using_module(self, module_source: str) -> list[ExplorerWorkspaceSummary]:
        """Query Explorer for all workspaces in the org that use the given module source."""
        raise NotImplementedError("HCP Terraform Explorer API integration is not yet implemented")

    def list_all_workspace_summaries(self) -> list[ExplorerWorkspaceSummary]:
        """Query Explorer for a summary of every workspace in the org."""
        raise NotImplementedError("HCP Terraform Explorer API integration is not yet implemented")
