"""Stage 2 output shape: resources with canonical type/tags after normalization."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from moduletrace.schemas.terraform import Cloud

TagConfidence = Literal["complete", "partial", "missing"]


class ModuleTraceTags(BaseModel):
    """The canonical ModuleTrace tag convention, extracted from a resource's raw tags/labels.

    See docs/tagging-convention.md for the per-cloud realization of these keys.
    """

    module_source: str | None = None
    module_version: str | None = None
    workspace: str | None = None
    team: str | None = None
    ttl: str | None = None


class NormalizedResource(BaseModel):
    """A `TerraformResourceRecord` after canonical typing and tag normalization."""

    workspace: str
    state_version: str
    resource_address: str
    cloud: Cloud

    canonical_resource_type: str
    """Internal taxonomy, not a provider-specific type string, e.g. `compute_instance`, `object_storage`."""

    cloud_resource_id: str | None = None

    moduletrace_tags: ModuleTraceTags
    tag_confidence: TagConfidence

    gcp_label_lookup: dict[str, str] = {}
    """For GCP resources: hashed label value -> original value, populated by gcp_label_codec.

    Empty for non-GCP resources.
    """
