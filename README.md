# ModuleTrace

ModuleTrace answers "what is this Terraform module actually costing us, and what's safe to delete?"

It's a companion tool to DriftGuard: same gated-destructive-action philosophy, applied to cost
cleanup instead of drift detection. ModuleTrace scans Terraform state and the HCP Terraform
Explorer API for module usage, cross-references AWS/GCP/Azure billing APIs by resource tag to
attribute cost per module and workspace, and produces a cleanup plan (targeted destroy or
tag-based bulk delete) that sits behind a human approval gate before anything executes.

See [`docs/architecture.md`](docs/architecture.md) for the full pipeline design and
[`docs/tagging-convention.md`](docs/tagging-convention.md) for the tagging scheme that makes
cost attribution possible.

## Status

Early scaffold. The pipeline stages, schemas, and CLI surface are defined; billing/Terraform
integrations are stubbed pending real credentials/workspaces to build against.

## CLI

```
moduletrace scan     [--workspace/-w ... | --all]   # stages 1-2: discover + normalize
moduletrace analyze  --run <run_id>                 # stages 3-5: billing join, rollup, candidates
moduletrace plan     --run <run_id>                 # stage 6: generate a hashed, reviewable plan
moduletrace show     <plan_id>                       # pretty-print a plan
moduletrace approve  <plan_id> --hash <plan_hash>    # human gate: requires the exact plan hash
moduletrace apply    <plan_id>                       # stage 7: re-validate + execute + audit log
moduletrace report   <plan_id>                       # render the execution report
```

## Development

```
pip install -e ".[dev]"
pytest tests/unit
python -m moduletrace.cli --help
```
