"""Structured-output runner for the RSS research agent.

Demonstrates the ``output_type`` seam: the same frozen base, the same tools, but
the agent now returns a typed ``Briefing`` object instead of prose — Pydantic AI
validates the model's output against the schema.

Run from this folder:

    uv run python brief.py
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent.config import load_config
from agent.context import build_deps, close_deps
from agent.factory import build_agent


class BriefingItem(BaseModel):
    title: str
    why_it_matters: str = Field(description="One sentence on why this is significant")
    link: str


class Briefing(BaseModel):
    overview: str = Field(description="One-line summary of the day's items")
    items: list[BriefingItem]


def main() -> None:
    config = load_config(".")
    agent = build_agent(config, output_type=Briefing)
    deps = build_deps(config)
    try:
        result = agent.run_sync(
            "Fetch the latest items and produce the briefing.", deps=deps
        )
    finally:
        close_deps(deps)

    briefing: Briefing = result.output
    print(f"\n{briefing.overview}\n")
    for item in briefing.items:
        print(f"• {item.title}\n  {item.why_it_matters}\n  {item.link}\n")


if __name__ == "__main__":
    main()
