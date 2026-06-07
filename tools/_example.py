"""Copy-me tool pattern. Rename to e.g. ``weather.py`` and edit.

A "tool" is just a module-level function in this ``tools/`` directory with:

1. a docstring (the model reads it to decide when/how to call the tool),
2. type hints on every parameter (Pydantic AI turns them into the JSON schema),
3. (optional) ``ctx: RunContext[AgentDeps]`` as the FIRST parameter to reach
   shared deps — the http client, the state store, and settings.yaml.

Files whose name starts with ``_`` are treated as patterns and skipped by the
registry, so this file does not register any tools. Remove the leading ``_``
to activate. Drop in as many files / functions as you like — they are
auto-discovered at startup; the core never changes.
"""

from __future__ import annotations

from pydantic_ai import RunContext

from agent.context import AgentDeps


def example_add(a: int, b: int) -> int:
    """Add two integers and return the sum.

    A pure tool needs no context — just typed params and a docstring.

    Args:
        a: First addend.
        b: Second addend.
    """
    return a + b


def example_remember(ctx: RunContext[AgentDeps], key: str, value: str) -> str:
    """Persist a key/value pair across runs in the agent's state store.

    Shows how to reach shared deps: the store, http client, and settings are all
    on ``ctx.deps``.

    Args:
        key: Name to store the value under.
        value: The value to remember.
    """
    ctx.deps.store.set(key, value)
    return f"Remembered {key!r} = {value!r}"


def example_fetch_title(ctx: RunContext[AgentDeps], url: str) -> str:
    """Fetch a URL using the shared http client and return its <title>.

    Args:
        url: The page to fetch.
    """
    import re

    resp = ctx.deps.http.get(url)
    match = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else "(no title found)"
