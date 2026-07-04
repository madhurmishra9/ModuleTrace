"""Azure billing adapter: Cost Management `query` action, grouped by tag or resource ID."""

from __future__ import annotations

from datetime import date
from typing import Literal


class AzureBillingAdapter:
    """Cost Management API via `azure-mgmt-costmanagement`. Supports resource-id-level
    granularity natively in query results, unlike GCP's export-dependent path.
    """

    cloud: Literal["aws", "gcp", "azure"] = "azure"

    def __init__(self, subscription_id: str) -> None:
        self.subscription_id = subscription_id

    def fetch_cost_by_tag(self, tag_key: str, start: date, end: date):
        raise NotImplementedError("Azure Cost Management integration is not yet implemented")

    def fetch_cost_by_resource_id(self, resource_ids: list[str], start: date, end: date):
        raise NotImplementedError("Azure Cost Management integration is not yet implemented")

    def supports_resource_level_cost(self) -> bool:
        return True
