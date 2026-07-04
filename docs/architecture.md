# ModuleTrace Architecture

## Framing

ModuleTrace runs as a pipeline of discrete, independently-testable stages, not a long-running
service. Each stage reads an input artifact (or live API data) and writes an output artifact to
a local run directory (`.moduletrace/runs/<run_id>/...`). This gives:

- **Resumability** — re-run stage 4 without re-hitting billing APIs.
- **Auditability** — every stage's output is inspectable JSON.
- **Testability** — each stage tested with fixture JSON in/out, no live cloud calls needed.
- **A natural seam for the human-approval gate** — it's just another stage boundary, deliberately
  hardened (see "Human approval gate design" below).

"Agent" here means pipeline stage/component, not an LLM agent. If ModuleTrace later grows an
LLM-assisted advisory layer (e.g. "explain why this is safe to delete"), it sits as an optional
enrichment on top of stage 5 and must never be in the approval or execution path — the gate stays
deterministic and human-driven.

## Pipeline stages

### Stage 1 — Terraform State & HCP Explorer Scanner

Discovers all workspaces/state in scope and extracts every managed resource with its module
source, module version, resource address, and cloud-native resource ID(s) (ARN, GCP self_link,
Azure resource ID) — the join key for stage 3.

- **Inputs:** config listing state sources (HCP Terraform org/workspace names via Explorer API,
  or backend configs for S3/GCS/azurerm remote state, or local `.tfstate` paths); HCP Terraform
  API token; cloud backend read access.
- **Outputs:** `stage1_inventory.json` — list of `TerraformResourceRecord`.

HCP Terraform Explorer gives a queryable cross-workspace view (resource counts, module usage,
providers) without pulling every state file. Use it first as a fast inventory/filter pass, then
only pull full state JSON for workspaces that need resource-level attribute detail. This avoids
O(workspaces) full state downloads when Explorer's summary is enough for stages 4-5.

Terraform state doesn't always retain a module's `version` constraint (only resolved values are
guaranteed). Best-effort version detection may require parsing root module HCL (`python-hcl2`)
or, for HCP-hosted workspaces without a local checkout, pulling the config via HCP Terraform's
configuration-version download endpoint. This is added scope worth validating early against a
real HCP Terraform org.

### Stage 2 — Resource & Tag Normalizer

Normalizes heterogeneous state output (AWS `tags`, GCP `labels`, Azure `tags`, and providers with
neither) into one canonical `NormalizedResource` shape: canonical cloud, canonical resource type
(an internal taxonomy, not provider-specific strings), and a normalized tag/label map with
ModuleTrace's convention keys extracted (see `tagging-convention.md`) plus a `tag_confidence`
flag: `complete` / `partial` / `missing` (untagged is a first-class case, not an error).

- **Inputs:** `stage1_inventory.json`
- **Outputs:** `stage2_normalized.json` — list of `NormalizedResource`.

This stage owns all provider-specific tag charset handling (GCP's stricter label rules — see
tagging doc) and its inverse (recognizing sanitized GCP labels and mapping them back to canonical
values for the join), so no later stage has to think about it.

### Stage 3 — Multi-Cloud Billing Cross-Reference

For each cloud in scope, calls that cloud's cost/billing API for line-item cost grouped/filterable
by tag, and joins those records to `NormalizedResource`s by resource ID (preferred) or tag-value
match (fallback — common, since many billing APIs group by tag *value*, not resource ID).

Adapter interface (the multi-cloud seam):

```python
class BillingAdapter(Protocol):
    cloud: Literal["aws", "gcp", "azure"]

    def fetch_cost_by_tag(self, tag_key: str, start: date, end: date) -> list[BillingRecord]: ...
    def fetch_cost_by_resource_id(self, resource_ids: list[str], start: date, end: date) -> list[BillingRecord]: ...
    def supports_resource_level_cost(self) -> bool: ...
```

- **AWS** — Cost Explorer (`ce:GetCostAndUsage`, tag/dimension grouping, resource-level if enabled
  on the account) + Resource Groups Tagging API (`GetResources`) to detect tag drift between
  Terraform config and live reality.
- **GCP** — Cloud Billing export via BigQuery (the realistic path for actuals; the Cloud Billing
  API itself is mostly SKU/pricing catalog), queried and grouped by `labels`. Resource-level cost
  generally requires the BigQuery export to be enabled — the adapter should check and warn at
  startup rather than fail silently.
- **Azure** — Cost Management `query` action (`azure-mgmt-costmanagement`), grouped by tag;
  supports resource-id-level granularity natively.

- **Inputs:** `stage2_normalized.json`, per-cloud credentials, date range (default trailing 30 days).
- **Outputs:** `stage3_billing_joined.json` — `NormalizedResource`s annotated with
  `cost_records: list[BillingRecord]` and `join_method: resource_id | tag_match | unattributed`.
  Unjoinable records are **kept**, not dropped, with zero-length cost_records (see Open Risks).

### Stage 4 — Cost Attribution & Rollup

Pure aggregation over `stage3_billing_joined.json`: groups cost by module source+version, by
workspace, by owning team, producing `ModuleCostRollup`s. No API calls — split from stage 3
specifically so the rollup can be re-sliced (different grouping dimension) without re-hitting
rate-limited billing APIs.

- **Inputs:** `stage3_billing_joined.json`
- **Outputs:** `stage4_rollup.json`

### Stage 5 — Cleanup Candidate Analysis

Applies per-resource-type heuristics to flag candidates: orphaned (in state but no matching
module block / detached), idle (cost present but below a configurable, cost/age-based threshold —
v1 does not pull utilization metrics like CPU; that's a documented extension point via a future
`UtilizationAdapter`), unused (zero cost + zero recent billing activity — not a signal for every
resource type, e.g. IAM roles/security groups, so rules are per-type not global), and TTL-expired.

Each candidate gets an **action type**: `targeted_destroy` (specific resource address(es), maps to
`terraform destroy -target=<addr>` semantics) vs `tag_based_bulk_delete` (a tag-value-defined set,
for resources not cleanly under one address or spanning workspaces).

- **Inputs:** `stage3_billing_joined.json`, `stage4_rollup.json`, a rules config (YAML, tunable thresholds).
- **Outputs:** `stage5_candidates.json` — `CleanupCandidate`s with `reason`, `action_type`,
  `estimated_monthly_savings`, `blast_radius`, and `risk_level` (`low`/`medium`/`high` — anything
  missing a `team` tag, or with cross-references from other modules, is auto-escalated to `high`
  regardless of cost).

### Stage 6 — Plan Generation

Turns candidates into a single, immutable, content-hashed **Plan**: a diff-like document (in the
spirit of `terraform plan` output) showing exactly what would be destroyed/deleted, total
estimated savings, total blast radius, and a `plan_hash` (hash of the canonical serialization of
the candidate set + the state snapshot versions it was computed against). This is the artifact a
human reviews.

- **Inputs:** `stage5_candidates.json`
- **Outputs:** `plans/<plan_id>/plan.json` (machine-readable), `plans/<plan_id>/plan.md`
  (human-readable — pastable into a Slack message or PR description).

### Stage 7 — Human Approval Gate + Execution + Audit

Two sub-phases sharing one plan state machine:

- **Gate:** `moduletrace approve <plan_id> --hash <plan_hash>` requires the human to pass the
  *exact* plan hash (not just a plan_id or a generic yes) — the CLI prints the plan summary
  (savings, blast radius, risk level, resource list breakdown) as part of the flow, requiring the
  hash *in addition to* interactive confirmation, for defense in depth. Writes
  `plans/<plan_id>/approval.json` (`approver`, `approved_at`, `plan_hash`, `comment`) — never
  auto-generated, never defaulted.
- **Execution + audit:** `moduletrace apply <plan_id>` re-validates the plan hash against current
  state (a cheap targeted re-check for just the affected resources, not a full pipeline re-run)
  before executing anything, then executes each action — `terraform destroy -target=` subprocess
  for `targeted_destroy`, direct cloud SDK delete for `tag_based_bulk_delete` — writing an
  append-only audit log entry per resource action (success/failure/skipped-due-to-drift) plus a
  final human-readable report.

- **Outputs:** `plans/<plan_id>/approval.json`, `plans/<plan_id>/audit_log.jsonl` (append-only,
  one JSON line per resource action), `plans/<plan_id>/execution_report.md`.

## Data flow

```
                    ┌─────────────────────────┐     ┌──────────────────────┐
                    │ HCP Terraform Explorer  │     │ Remote state backends │
                    │ API (workspace/module   │     │ (S3/GCS/AzureRM/local) │
                    │ summary, fast filter)   │     │ (full state JSON)     │
                    └───────────┬─────────────┘     └───────────┬───────────┘
                                └───────────┬───────────────────┘
                                            ▼
                              ┌──────────────────────────┐
                              │ Stage 1: TF/Explorer      │
                              │ Scanner → stage1_inventory│
                              └─────────────┬─────────────┘
                                            ▼
                              ┌──────────────────────────┐
                              │ Stage 2: Resource/Tag      │
                              │ Normalizer → stage2_normalized│
                              └─────────────┬─────────────┘
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        ▼                                   ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐              ┌──────────────────┐
│ AWS Cost Explorer │              │ GCP Billing       │              │ Azure Cost Mgmt   │
│ + Tagging API      │              │ export (labels)   │              │ API (tags)         │
└─────────┬─────────┘              └─────────┬─────────┘              └─────────┬─────────┘
          └───────────────────────┬───────────────────────────────────────────┘
                                   ▼
                     ┌──────────────────────────┐
                     │ Stage 3: Billing Cross-   │
                     │ Reference → stage3_billing_joined│
                     └─────────────┬─────────────┘
                                   ▼
                     ┌──────────────────────────┐
                     │ Stage 4: Cost Attribution │
                     │ & Rollup → stage4_rollup  │
                     └─────────────┬─────────────┘
                                   ▼
                     ┌──────────────────────────┐
                     │ Stage 5: Cleanup Candidate│
                     │ Analysis → stage5_candidates│
                     └─────────────┬─────────────┘
                                   ▼
                     ┌──────────────────────────┐
                     │ Stage 6: Plan Generation  │
                     │ → plans/<id>/plan.json+md │
                     └─────────────┬─────────────┘
                                   ▼
                         ╔═══════════════════╗
                         ║  HUMAN APPROVAL   ║   ← blocking, requires plan_hash match
                         ║       GATE        ║
                         ╚═════════┬═════════╝
                                   ▼
                     ┌──────────────────────────┐
                     │ Stage 7: Execution        │
                     │ (re-validate hash, then   │
                     │ terraform destroy -target │
                     │ or cloud SDK bulk delete)  │
                     │ → audit_log.jsonl          │
                     │   execution_report.md      │
                     └──────────────────────────┘
```

## Human approval gate design

- **Plan immutability + hashing:**
  `plan_hash = sha256(canonical_json({plan_id, candidates, state_versions_used, generated_at}))`.
  `state_versions_used` captures the exact state serial/version each candidate was computed
  against — the anti-staleness mechanism: if state changes between plan generation and apply, a
  re-derived hash at apply time won't match. Plans are append-only; regenerating always creates a
  new `plan_id` (never overwrites), forcing re-review rather than silently reusing an approval.
- **Approval command:** `moduletrace approve <plan_id> --hash <plan_hash> [--reason "..."]`.
  Requires the human to have actually opened and read the plan (or gotten the hash from someone
  who did) — not an implicit "yes". The CLI prints the plan summary as part of the approve flow
  and requires interactive confirmation *in addition to* the hash match.
- **Re-validation at apply time:** before executing anything, `apply` confirms `approval.json`'s
  `plan_hash` matches `plan.json`'s stored hash (detects post-approval tampering), then does a
  cheap targeted re-check per candidate resource against live state. If a resource no longer
  exists or its tags changed materially, that resource is **skipped** (`skipped_state_drift`,
  logged) rather than failing the whole apply — partial application with per-resource skip is
  safer than all-or-nothing for a cleanup tool, though this should be a configurable policy
  (`--on-drift={skip,abort}`) rather than hardcoded, since some orgs need strict abort semantics.
- **Idempotent/resumable apply:** if interrupted partway, re-running `apply <plan_id>` skips
  already-executed resources (per audit log) and only acts on the remainder.
- **Expiry:** approvals have a configurable validity window (default 7 days); `apply` refuses to
  run against an expired approval, requiring a fresh plan.

## Open design risks / judgment calls

1. **Unattributable resources.** Billing API lag (AWS Cost Explorer can be 24-48h behind),
   too-recent resources, or providers without resource-level billing (GCP without BigQuery export)
   mean some resources never join to cost data. Kept visible (`join_method="unattributed"`) with
   `unattributed_cost`/`unattributed_resource_count` surfaced at rollup and plan level, so a
   reviewer can see a plan's savings estimate excludes resources that couldn't be priced.
2. **Remote state backend diversity.** v1 scope: HCP Terraform-hosted state (via Explorer + state-
   version API — the strongest path), S3+DynamoDB, GCS, azurerm. Local state is dev/test only.
   Other backends (Consul, on-prem TFE with nonstandard auth) are out of scope; `state_reader.py`
   exposes a `StateSource` protocol so adding backends later doesn't touch stage 1's orchestration.
3. **Billing API rate limits.** AWS Cost Explorer has low RPS limits and small nonzero per-request
   cost; Azure Cost Management throttles queries; GCP's BigQuery export path bills its own queries.
   Stage 3 must batch/cache aggressively (fetch grouped cost once per run, not once per resource)
   and support a `--use-cached-billing <path>` escape hatch for iterating on stages 4-6 without
   re-hitting APIs during development.
4. **Approved-plan-vs-drifted-state.** Handled via hash-based staleness check + per-resource
   skip-on-drift (see gate design), chosen over all-or-nothing abort since aborting a 50-resource
   plan over one drifted resource is likely worse than skipping it — but this should be a
   configurable policy, not hardcoded, for orgs with stricter compliance needs.
5. **`terraform destroy -target` execution mechanism.** v1 shells out to
   `terraform destroy -target=<addr> -auto-approve` per resource post-gate/post-drift-check,
   rather than reimplementing Terraform's destroy graph. `-target` is a known blunt instrument
   with complex dependency graphs — document this constraint. `tag_based_bulk_delete` (direct
   cloud SDK delete, bypassing Terraform) is preferred for resources cleanly identifiable by tag
   without complex Terraform-side dependents; stage 5's classification heuristic will need
   real-world tuning.
6. **Module version detection from state alone.** State doesn't always retain module version
   constraints — see Stage 1 notes above. Needs validation against a real HCP Terraform org before
   committing further.
7. **Cross-workspace/cross-module shared resources.** A resource tagged with one module-source
   could be relied on by resources in a different workspace not visible in that workspace's state
   (e.g. a shared VPC via data source). Stage 5's `risk_level` escalation is a coarse mitigation,
   not a solve — true cross-workspace dependency-graph analysis is out of scope for v1.
