"""AWS billing adapter: Cost Explorer for cost, Resource Groups Tagging API for live tag drift checks."""

from __future__ import annotations

from datetime import date
from typing import Literal


class AWSBillingAdapter:
    """Cost Explorer (`ce:GetCostAndUsage`) grouped by tag or resource, plus
    Resource Groups Tagging API (`GetResources`) to detect tag drift between Terraform config and
    live reality (surfaced as a signal, not silently corrected — see docs/architecture.md).
    """

    cloud: Literal["aws", "gcp", "azure"] = "aws"

    def __init__(self, region: str = "us-east-1") -> None:
        self.region = region

    def fetch_cost_by_tag(self, tag_key: str, start: date, end: date):
        raise NotImplementedError("AWS Cost Explorer integration is not yet implemented")

    def fetch_cost_by_resource_id(self, resource_ids: list[str], start: date, end: date):
        raise NotImplementedError("AWS Cost Explorer integration is not yet implemented")

    def supports_resource_level_cost(self) -> bool:
        """True only if the account has "resource-level data" enabled in Cost Explorer preferences."""
        raise NotImplementedError("AWS Cost Explorer integration is not yet implemented")
