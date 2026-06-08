"""Optional reusable helpers so tools don't reinvent common plumbing.

Nothing in the core depends on this module — it's a convenience shelf for the
tools you write: HTTP with retries, a tiny TTL cache, and a dependency-free RSS
parser. Import what you need inside ``tools/*.py``.
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Callable

import httpx


def http_get(
    url: str,
    *,
    client: httpx.Client | None = None,
    retries: int = 3,
    backoff: float = 0.5,
    **kwargs: Any,
) -> httpx.Response:
    """GET *url* with exponential backoff on transport/5xx errors."""
    owns = client is None
    client = client or httpx.Client(timeout=30.0, follow_redirects=True)
    try:
        last_exc: Exception | None = None
        for attempt in range(retries):
            try:
                resp = client.get(url, **kwargs)
                if resp.status_code < 500:
                    return resp
                last_exc = httpx.HTTPStatusError(
                    f"server error {resp.status_code}", request=resp.request, response=resp
                )
            except httpx.HTTPError as exc:
                last_exc = exc
            time.sleep(backoff * (2**attempt))
        assert last_exc is not None
        raise last_exc
    finally:
        if owns:
            client.close()


class TTLCache:
    """A tiny in-process cache with per-entry time-to-live."""

    def __init__(self, ttl: float = 300.0):
        self.ttl = ttl
        self._data: dict[Any, tuple[float, Any]] = {}

    def get(self, key: Any, default: Any = None) -> Any:
        item = self._data.get(key)
        if item is None:
            return default
        expires, value = item
        if time.time() > expires:
            self._data.pop(key, None)
            return default
        return value

    def set(self, key: Any, value: Any) -> None:
        self._data[key] = (time.time() + self.ttl, value)

    def get_or_set(self, key: Any, producer: Callable[[], Any]) -> Any:
        hit = self.get(key, _MISS)
        if hit is _MISS:
            hit = producer()
            self.set(key, hit)
        return hit


_MISS = object()


@dataclass
class FeedItem:
    title: str
    link: str
    summary: str
    published: str


def parse_rss(xml_text: str, limit: int = 50) -> list[FeedItem]:
    """Parse RSS 2.0 or Atom into a list of :class:`FeedItem` — no deps."""
    items: list[FeedItem] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    # RSS 2.0: channel/item
    for node in root.iter("item"):
        items.append(
            FeedItem(
                title=_text(node, "title"),
                link=_text(node, "link"),
                summary=_text(node, "description"),
                published=_text(node, "pubDate"),
            )
        )
        if len(items) >= limit:
            return items

    # Atom: entry (tags are namespaced)
    if not items:
        ns = "{http://www.w3.org/2005/Atom}"
        for node in root.iter(f"{ns}entry"):
            link_el = node.find(f"{ns}link")
            items.append(
                FeedItem(
                    title=_text(node, f"{ns}title"),
                    link=(link_el.get("href") if link_el is not None else ""),
                    summary=_text(node, f"{ns}summary") or _text(node, f"{ns}content"),
                    published=_text(node, f"{ns}updated") or _text(node, f"{ns}published"),
                )
            )
            if len(items) >= limit:
                break
    return items


def _text(node: ET.Element, tag: str) -> str:
    el = node.find(tag)
    return (el.text or "").strip() if el is not None and el.text else ""
