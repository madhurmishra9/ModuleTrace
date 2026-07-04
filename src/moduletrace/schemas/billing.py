"""Stage 3 output shape: billing line items joined to normalized resources."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

from moduletrace.schemas.normalized import NormalizedResource

JoinMethod = Literal["resource_id", "tag_match", "unattributed"]


class BillingRecord(BaseModel):
    """A single cost line item returned by a `BillingAdapter`."""

    cloud: Literal["aws", "gcp", "azure"]
    period_start: date
    period_end: date
    amount: float
    currency: str = "USD"
    tag_key: str | None = None
    tag_value: str | None = None
    resource_id: str | None = None
    """Present only when the adapter supports resource-level cost (see `supports_resource_level_cost`)."""


class BilledResource(BaseModel):
    """A `NormalizedResource` annotated with the cost records joined to it."""

    resource: NormalizedResource
    cost_records: list[BillingRecord] = []
    join_method: JoinMethod
    total_cost: float = 0.0
