"""Drop-in tool: fetch configured RSS/Atom feeds, returning only new items.

Demonstrates every seam at once with ZERO core changes:
  - reads feed list from ``settings.yaml`` via ``ctx.deps.settings``
  - uses the shared http client and the ``toolkit`` rss parser
  - dedups against the persistent state store (seen-URL set)
"""

from __future__ import annotations

from pydantic_ai import RunContext

from agent.context import AgentDeps
from agent.toolkit import parse_rss

_SEEN_KEY = "seen_urls"


def rss_fetch(ctx: RunContext[AgentDeps]) -> list[dict]:
    """Fetch the configured feeds and return items not seen on prior runs.

    Returns a list of ``{title, link, summary, published, feed}`` dicts. URLs
    are remembered in the state store so the same item is never returned twice.
    """
    settings = ctx.deps.settings
    feeds: list[str] = settings.get("feeds", [])
    max_items = int(settings.get("max_items", 12))

    seen: set[str] = set(ctx.deps.store.get(_SEEN_KEY, []))
    fresh: list[dict] = []

    for feed_url in feeds:
        try:
            resp = ctx.deps.http.get(feed_url)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001 - report bad feed, keep going
            fresh.append({"title": f"(failed to fetch {feed_url}: {exc})", "link": "", "feed": feed_url})
            continue

        for item in parse_rss(resp.text):
            if not item.link or item.link in seen:
                continue
            seen.add(item.link)
            fresh.append(
                {
                    "title": item.title,
                    "link": item.link,
                    "summary": item.summary[:280],
                    "published": item.published,
                    "feed": feed_url,
                }
            )
            if len(fresh) >= max_items:
                break
        if len(fresh) >= max_items:
            break

    ctx.deps.store.set(_SEEN_KEY, sorted(seen))
    return fresh or [{"title": "(no new items)", "link": "", "feed": ""}]
