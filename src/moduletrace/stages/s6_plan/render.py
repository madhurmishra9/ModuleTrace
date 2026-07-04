"""Renders a Plan as human-readable Markdown (plan.md) — terraform-plan-style summary.

See docs/architecture.md, "Stage 6 — Plan Generation".
"""

from __future__ import annotations

from moduletrace.schemas.plan import Plan


def render_plan_markdown(plan: Plan) -> str:
    """Render `plan` as Markdown suitable for pasting into a Slack message or PR description.

    Must surface: plan_id, plan_hash (prominently — this is what a human pastes back to approve),
    total_estimated_monthly_savings, total_blast_radius, and a per-candidate breakdown
    (reason, action_type, risk_level, affected resources).
    """
    raise NotImplementedError("plan Markdown rendering is not yet implemented")
