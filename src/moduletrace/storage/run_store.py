"""File I/O for .moduletrace/runs/<run_id>/ and .moduletrace/plans/<plan_id>/ artifacts.

Every stage reads/writes through here rather than touching paths directly, so the on-disk layout
(described in docs/architecture.md) has exactly one place that knows it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

STAGE_ARTIFACT_NAMES = {
    1: "stage1_inventory.json",
    2: "stage2_normalized.json",
    3: "stage3_billing_joined.json",
    4: "stage4_rollup.json",
    5: "stage5_candidates.json",
}

ModelT = TypeVar("ModelT", bound=BaseModel)


class RunStore:
    """Reads/writes the numbered stage artifacts for one pipeline run."""

    def __init__(self, runs_dir: Path, run_id: str) -> None:
        self.run_dir = runs_dir / run_id
        self.run_id = run_id

    def write_stage(self, stage_number: int, models: list[BaseModel]) -> Path:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        path = self.run_dir / STAGE_ARTIFACT_NAMES[stage_number]
        payload = [m.model_dump(mode="json") for m in models]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def read_stage(self, stage_number: int, model_cls: type[ModelT]) -> list[ModelT]:
        path = self.run_dir / STAGE_ARTIFACT_NAMES[stage_number]
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [model_cls.model_validate(item) for item in payload]


class PlanStore:
    """Resolves the fixed set of file paths under one plan's directory. See docs/architecture.md."""

    def __init__(self, plans_dir: Path, plan_id: str) -> None:
        self.plan_dir = plans_dir / plan_id
        self.plan_id = plan_id

    def plan_json_path(self) -> Path:
        return self.plan_dir / "plan.json"

    def plan_markdown_path(self) -> Path:
        return self.plan_dir / "plan.md"

    def approval_json_path(self) -> Path:
        return self.plan_dir / "approval.json"

    def audit_log_path(self) -> Path:
        return self.plan_dir / "audit_log.jsonl"

    def execution_report_path(self) -> Path:
        return self.plan_dir / "execution_report.md"

    def ensure_dir(self) -> None:
        self.plan_dir.mkdir(parents=True, exist_ok=True)
