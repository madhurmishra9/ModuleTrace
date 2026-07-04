"""Backend-agnostic Terraform state reading.

v1 scope: HCP Terraform-hosted state (via the state-version API), S3+DynamoDB, GCS, and azurerm
remote backends, plus local .tfstate files for dev/test. Other backends (Consul, on-prem TFE with
nonstandard auth) are out of scope — see docs/architecture.md "Open design risks" #2.
"""

from __future__ import annotations

from typing import Any, Protocol


class StateSource(Protocol):
    """A source of Terraform state JSON for one workspace.

    Implementations: HcpTerraformStateSource, S3StateSource, GcsStateSource, AzureRmStateSource,
    LocalFileStateSource. Adding a new backend means adding a new implementation of this protocol
    without touching stage 1's orchestration (see stages/s1_scanner/run.py).
    """

    workspace: str

    def fetch_state(self) -> dict[str, Any]:
        """Return the raw Terraform state document (parsed JSON) for this workspace."""
        ...

    def state_version(self) -> str:
        """Return a stable identifier for the exact state snapshot (serial, or HCP state-version ID).

        Used to populate `TerraformResourceRecord.state_version` and, later, `Plan.state_versions_used`.
        """
        ...


class LocalFileStateSource:
    """Reads a local .tfstate file. Dev/test only — not intended for production workspaces."""

    def __init__(self, workspace: str, path: str) -> None:
        self.workspace = workspace
        self.path = path

    def fetch_state(self) -> dict[str, Any]:
        raise NotImplementedError("local state reading is not yet implemented")

    def state_version(self) -> str:
        raise NotImplementedError("local state reading is not yet implemented")


class S3StateSource:
    """Reads state from an S3 + DynamoDB-lock remote backend via a read-only IAM role."""

    def __init__(self, workspace: str, bucket: str, key: str, region: str) -> None:
        self.workspace = workspace
        self.bucket = bucket
        self.key = key
        self.region = region

    def fetch_state(self) -> dict[str, Any]:
        raise NotImplementedError("S3 backend state reading is not yet implemented")

    def state_version(self) -> str:
        raise NotImplementedError("S3 backend state reading is not yet implemented")
