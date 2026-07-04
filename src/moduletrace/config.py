"""ModuleTrace runtime configuration: credentials, thresholds, run-directory locations."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MODULETRACE_", env_file=".env", extra="ignore")

    data_dir: Path = Field(default=Path(".moduletrace"))
    """Root directory for run artifacts and plans (gitignored)."""

    hcp_terraform_token: str | None = None
    hcp_terraform_org: str | None = None

    default_lookback_days: int = 30
    """Default billing date-range window used by `moduletrace analyze` when not overridden."""

    approval_validity_days: int = 7
    """Default approval expiry window (see stages/s7_gate/approval.py)."""

    on_drift_policy: str = "skip"
    """Default `--on-drift` policy for `moduletrace apply`: "skip" or "abort"."""

    @property
    def runs_dir(self) -> Path:
        return self.data_dir / "runs"

    @property
    def plans_dir(self) -> Path:
        return self.data_dir / "plans"
