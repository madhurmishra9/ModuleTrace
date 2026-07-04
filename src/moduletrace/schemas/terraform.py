"""Stage 1 output shape: raw resources discovered from Terraform state / HCP Explorer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Cloud = Literal["aws", "gcp", "azure"]


class TerraformResourceRecord(BaseModel):
    """One managed resource as seen in Terraform state, before tag normalization."""

    workspace: str
    """Workspace/state name this resource belongs to."""

    state_version: str
    """State serial or HCP Terraform state-version ID, captured for later plan-hash staleness checks."""

    resource_address: str
    """Terraform resource address, e.g. `module.vpc.aws_vpc.this`."""

    resource_type: str
    """Provider-native resource type, e.g. `aws_vpc`."""

    module_source: str | None = None
    """Module source string as declared, e.g. `git::https://github.com/org/tf-modules//vpc`."""

    module_version: str | None = None
    """Pinned module version/ref, if resolvable from state or root module config."""

    cloud: Cloud | None = None

    cloud_resource_id: str | None = None
    """Cloud-native ID: AWS ARN, GCP self_link, or Azure resource ID. Primary join key for stage 3."""

    raw_tags: dict[str, str] = {}
    """Tags/labels exactly as they appear in state, before any per-cloud normalization."""
