"""ModuleTrace CLI: scan -> analyze -> plan -> show -> approve -> apply -> report.

See README.md and docs/architecture.md for what each command does and why they're split this way
(billing calls in `analyze` are rate-limited/costly, so `plan`/`show` can iterate on an existing
run without re-triggering them).
"""

from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(
    name="moduletrace",
    help="Scan Terraform module usage, attribute cloud cost by tag, and propose gated cleanup plans.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def scan(
    workspace: list[str] = typer.Option(
        [], "--workspace", "-w", help="Workspace(s) to scan. Omit with --all to scan every workspace."
    ),
    all_workspaces: bool = typer.Option(False, "--all", help="Scan every known workspace."),
) -> None:
    """Discover Terraform-managed resources (stages 1-2) and print the resulting run_id."""
    raise NotImplementedError("wiring `scan` to moduletrace.pipeline.scan is not yet implemented")


@app.command()
def analyze(
    run: str = typer.Option(..., "--run", help="run_id produced by a prior `scan`."),
) -> None:
    """Cross-reference billing, roll up cost, and classify cleanup candidates (stages 3-5)."""
    raise NotImplementedError("wiring `analyze` to moduletrace.pipeline.analyze is not yet implemented")


@app.command(name="plan")
def make_plan(
    run: str = typer.Option(..., "--run", help="run_id produced by a prior `analyze`."),
) -> None:
    """Generate a new, immutable, hashed cleanup plan (stage 6) and print its plan_id + plan_hash."""
    raise NotImplementedError(
        "wiring `plan` to moduletrace.pipeline.generate_plan is not yet implemented"
    )


@app.command()
def show(plan_id: str) -> None:
    """Pretty-print an existing plan's plan.md to the terminal."""
    raise NotImplementedError("`show` is not yet implemented")


@app.command()
def approve(
    plan_id: str,
    plan_hash: str = typer.Option(..., "--hash", help="The exact plan_hash shown in plan.md."),
    reason: str | None = typer.Option(None, "--reason", help="Optional approval comment."),
) -> None:
    """Approve a plan for execution. Requires pasting the plan's exact hash (see s7_gate/approval.py)."""
    raise NotImplementedError(
        "wiring `approve` to moduletrace.stages.s7_gate.approval.approve is not yet implemented"
    )


@app.command()
def apply(plan_id: str) -> None:
    """Re-validate an approved plan against live state, then execute it (stage 7)."""
    raise NotImplementedError(
        "wiring `apply` to moduletrace.stages.s7_gate.executor.apply is not yet implemented"
    )


@app.command()
def report(plan_id: str) -> None:
    """Render a plan's execution_report.md / audit log to the terminal."""
    raise NotImplementedError("`report` is not yet implemented")


if __name__ == "__main__":
    app()
