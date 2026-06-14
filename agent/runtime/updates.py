"""Read-only update check — is a newer core published upstream?

Deliberately minimal: it compares the local version (from this folder's
``pyproject.toml``) against the newest semver tag on the GitHub repo, and that's
it. No download, no auto-replace — updating the vendored ``agent/`` engine stays
a deliberate, visible action (git pull, or swap the folder from a release).

The repo defaults to the upstream project; override with ``GENESIS_REPO`` (the
same env var the install scripts use), e.g. ``GENESIS_REPO=you/your-fork``.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

DEFAULT_REPO = "ysz7/genesis-agent"
_VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)
_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")


def repo_slug() -> str:
    """The ``owner/name`` to check, from ``GENESIS_REPO`` or the default."""
    return (os.getenv("GENESIS_REPO") or DEFAULT_REPO).strip()


def repo_url() -> str:
    return f"https://github.com/{repo_slug()}"


def current_version(root: str | os.PathLike | None = None) -> str:
    """The installed version, read from this folder's ``pyproject.toml``.

    Reads the file directly (so it's correct without a reinstall) and falls back
    to package metadata, then ``"unknown"``.
    """
    pyproject = Path(root or os.getcwd()) / "pyproject.toml"
    try:
        match = _VERSION_RE.search(pyproject.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    except OSError:
        pass
    try:
        from importlib import metadata

        return metadata.version("genesis-agent")
    except Exception:  # noqa: BLE001
        return "unknown"


def _parse(version: str) -> tuple[int, int, int] | None:
    match = _SEMVER_RE.match(version.strip())
    return tuple(int(g) for g in match.groups()) if match else None  # type: ignore[return-value]


def latest_version(repo: str | None = None, timeout: float = 6.0) -> str | None:
    """Newest semver tag on the repo, or None if it can't be determined."""
    url = f"https://api.github.com/repos/{repo or repo_slug()}/tags?per_page=100"
    req = urllib.request.Request(
        url, headers={"User-Agent": "genesis-agent", "Accept": "application/vnd.github+json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            tags = json.loads(resp.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - network/parse failure → "unknown"
        return None
    best: tuple[int, int, int] | None = None
    best_name: str | None = None
    for tag in tags:
        name = tag.get("name", "") if isinstance(tag, dict) else ""
        parsed = _parse(name)
        if parsed is not None and (best is None or parsed > best):
            best, best_name = parsed, name
    return best_name


def is_newer(latest: str, current: str) -> bool:
    """True only when both parse and *latest* is strictly newer than *current*."""
    a, b = _parse(latest), _parse(current)
    return a is not None and b is not None and a > b
