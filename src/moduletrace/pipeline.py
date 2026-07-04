"""Stage sequencing and run-directory orchestration.

Wires the seven stages from docs/architecture.md together. Each stage function's actual work
(stages/s*/run.py) is still stubbed pending real Terraform/billing integrations — this module owns
sequencing and artifact hand-off, not the per-stage logic itself.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from moduletrace.config import Settings
from moduletrace.schemas.billing import BilledResource
from moduletrace.schemas.candidate import CleanupCandidate
from moduletrace.schemas.normalized import NormalizedResource
from moduletrace.schemas.plan import Plan
from moduletrace.schemas.rollup import ModuleCostRollup
from moduletrace.schemas.terraform import TerraformResourceRecord
from moduletrace.stages.s1_scanner.hcp_explorer import HcpExplorerClient
from moduletrace.stages.s1_scanner.state_reader import StateSource
from moduletrace.stages.s1_scanner import run as s1
from moduletrace.stages.s2_normalizer import run as s2
from moduletrace.stages.s3_billing import run as s3
from moduletrace.stages.s3_billing.base import BillingAdapter
from moduletrace.stages.s4_rollup import run as s4
from moduletrace.stages.s5_candidates import run as s5
from moduletrace.stages.s5_candidates.rules import CleanupRule
from moduletrace.stages.s6_plan import run as s6
from moduletrace.storage.run_store import RunStore


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class ScanResult:
    run_id: str
    normalized: list[NormalizedResource]


def scan(
    settings: Settings, explorer: HcpExplorerClient, state_sources: list[StateSource]
) -> ScanResult:
    """Stages 1-2: discover Terraform-managed resources and normalize their tags/types."""
    run_id = new_run_id()
    store = RunStore(settings.runs_dir, run_id)

    records: list[TerraformResourceRecord] = s1.run(explorer, state_sources)
    store.write_stage(1, records)

    normalized: list[NormalizedResource] = s2.run(records)
    store.write_stage(2, normalized)

    return ScanResult(run_id=run_id, normalized=normalized)


@dataclass
class AnalyzeResult:
    billed: list[BilledResource]
    rollups: list[ModuleCostRollup]
    candidates: list[CleanupCandidate]


def analyze(
    settings: Settings,
    run_id: str,
    adapters: dict[str, BillingAdapter],
    rules: list[CleanupRule],
    start: date,
    end: date,
) -> AnalyzeResult:
    """Stages 3-5: billing cross-reference, cost rollup, cleanup candidate classification."""
    store = RunStore(settings.runs_dir, run_id)
    normalized = store.read_stage(2, NormalizedResource)

    billed = s3.run(normalized, adapters, start, end)
    store.write_stage(3, billed)

    rollups = s4.run(billed)
    store.write_stage(4, rollups)

    candidates = s5.run(billed, rollups, rules)
    store.write_stage(5, candidates)

    return AnalyzeResult(billed=billed, rollups=rollups, candidates=candidates)


def generate_plan(
    settings: Settings, run_id: str, state_versions_used: dict[str, str]
) -> Plan:
    """Stage 6: turn a run's candidates into a new, immutable, hashed Plan."""
    store = RunStore(settings.runs_dir, run_id)
    candidates = store.read_stage(5, CleanupCandidate)
    plan_id = new_run_id()
    return s6.run(plan_id, candidates, state_versions_used)
