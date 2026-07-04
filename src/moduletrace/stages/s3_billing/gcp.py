"""GCP billing adapter: BigQuery billing export queried and grouped by labels.

The Cloud Billing API itself is mostly a SKU/pricing catalog, not per-resource actuals — the
realistic path for actual cost data is the BigQuery billing export table, which must be enabled on
the account. Resource-level cost generally requires that export; this adapter should check for it
at construction time and warn rather than silently degrade to tag-only granularity.
"""

from __future__ import annotations

from datetime import date
from typing import Literal


class GCPBillingAdapter:
    cloud: Literal["aws", "gcp", "azure"] = "gcp"

    def __init__(self, billing_export_table: str) -> None:
        """`billing_export_table` is the fully-qualified BigQuery table, e.g.
        `project.dataset.gcp_billing_export_v1_XXXXXX`.
        """
        self.billing_export_table = billing_export_table

    def fetch_cost_by_tag(self, tag_key: str, start: date, end: date):
        raise NotImplementedError("GCP BigQuery billing export integration is not yet implemented")

    def fetch_cost_by_resource_id(self, resource_ids: list[str], start: date, end: date):
        raise NotImplementedError("GCP BigQuery billing export integration is not yet implemented")

    def supports_resource_level_cost(self) -> bool:
        """True only if the BigQuery billing export includes resource-level fields."""
        raise NotImplementedError("GCP BigQuery billing export integration is not yet implemented")
