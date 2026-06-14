"""Explicit planning / todo scratchpad (Phase 13) — opt-in.

When ``planning.enabled`` is set, the agent gains ``update_plan`` — a tool to
keep a short, visible checklist for multi-step tasks. The current plan is
injected into the system prompt each turn (so the model tracks its own progress)
and rendered in the CLI live tree (so the human sees it). It's a scratchpad, not
enforced control flow, and lives per-run in ``deps.extra["plan"]``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic_ai import RunContext

from ..runtime.context import AgentDeps

MAX_STEPS = 20
MAX_TITLE = 120
_MARK = {"pending": "○", "in_progress": "▸", "done": "✓"}


class PlanStep(BaseModel):
    """One checklist item."""

    title: str
    status: Literal["pending", "in_progress", "done"] = "pending"


def update_plan(ctx: RunContext[AgentDeps], steps: list[PlanStep]) -> str:
    """Create or replace your task plan — a short checklist you keep up to date.

    Call this at the start of a multi-step task to lay out the steps, then call
    it again to flip a step to ``in_progress`` / ``done`` as you go (it replaces
    the whole list each time). Keep one step ``in_progress`` at a time. The plan
    is a scratchpad for you and the user — it doesn't execute anything.

    Args:
        steps: The full ordered checklist; each step has a short ``title`` and a
            ``status`` of ``pending``, ``in_progress``, or ``done``.
    """
    plan: list[dict] = []
    for step in steps[:MAX_STEPS]:
        title = step.title.strip()[:MAX_TITLE]
        if title:
            plan.append({"title": title, "status": step.status})
    ctx.deps.extra["plan"] = plan
    return render_plan(plan) or "(empty plan)"


def render_plan(plan: list[dict]) -> str:
    """A compact one-line-per-step rendering of *plan*."""
    return "\n".join(f"{_MARK.get(s['status'], '○')} {s['title']}" for s in plan)


def plan_overview(deps: AgentDeps) -> str:
    """The current plan for the system prompt, or '' when there is none."""
    plan = deps.extra.get("plan")
    if not plan:
        return ""
    return "Current plan (keep it updated with update_plan):\n" + render_plan(plan)


#: Registered when ``planning.enabled`` is true.
PLANNING_TOOLS = [update_plan]
