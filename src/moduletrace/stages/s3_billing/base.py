"""BillingAdapter protocol: the multi-cloud seam for stage 3.

Each cloud implements this the same way, so stage 3's orchestration (run.py) never branches on
cloud beyond picking which adapter to call. See docs/architecture.md, "Stage 3 — Multi-Cloud
Billing Cross-Reference" for the per-cloud API mapping and its caveats (AWS Cost Explorer lag,
GCP's BigQuery-export dependency, Azure Cost Management throttling).
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Protocol

from moduletrace.schemas.billing import BillingRecord


class BillingAdapter(Protocol):
    cloud: Literal["aws", "gcp", "azure"]

    def fetch_cost_by_tag(self, tag_key: str, start: date, end: date) -> list[BillingRecord]:
        """Cost grouped by the values of `tag_key`, for the given date range.

        This is the common path — most billing APIs group by tag *value*, not resource ID.
        """
        ...

    def fetch_cost_by_resource_id(
        self, resource_ids: list[str], start: date, end: date
    ) -> list[BillingRecord]:
        """Cost per resource ID, for the given date range.

        Only meaningful when `supports_resource_level_cost()` is True; callers should fall back to
        `fetch_cost_by_tag` otherwise.
        """
        ...

    def supports_resource_level_cost(self) -> bool:
        """Whether this adapter/account is configured for resource-level cost granularity.

        E.g. AWS requires "resource-level data" enabled on the Cost Explorer account; GCP requires
        the BigQuery billing export to be enabled. Adapters should check this at construction time
        and warn (not silently degrade) if resource-level cost was expected but isn't available.
        """
        ...
