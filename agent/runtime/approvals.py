"""Approval seam (Phase 11e) — the human gate, with persistent "always allow".

One mechanism serves two callers: confirm-listed tools (Phase 2b) and the
activation of agent-written tools (Phase 11c). The human answers **once**,
**always**, or **deny**; an "always" grant is persisted to
``workspace/approvals.json`` keyed by *subject* plus a *content hash*, so:

- approving a generated tool persists by ``tool:<name>`` + sha256(code) — edit
  the code and the hash changes, re-triggering approval (you can't "approve
  once, swap the code later");
- approving a confirm-listed tool persists by ``confirm:<name>`` with a stable
  hash, so future calls of that tool skip the prompt.

Resolution order: persisted grant → ask the human. Headless (no
``approval_hook``) denies by default, honoring persisted grants only when
``approvals.headless_allow_granted`` is set in settings.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger("agent.approvals")

# The three answers an approval_hook may return.
ALLOW_ONCE = "once"
ALLOW_ALWAYS = "always"
DENY = "deny"


def content_hash(text: str) -> str:
    """Short, stable hash of *text* (generated-tool code)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class ApprovalStore:
    """Persisted ``subject -> approved content hash`` grants (a JSON file)."""

    def __init__(self, path: Path):
        self.path = path
        self._grants: dict[str, str] = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._grants = dict(data.get("grants", {}))
            except Exception as exc:  # noqa: BLE001 - a corrupt file shouldn't crash startup
                logger.warning("could not read %s: %s", path.name, exc)

    def is_granted(self, subject: str, hash_: str) -> bool:
        return self._grants.get(subject) == hash_

    def grant(self, subject: str, hash_: str) -> None:
        self._grants[subject] = hash_
        try:
            self.path.write_text(
                json.dumps({"grants": self._grants}, indent=2), encoding="utf-8"
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("could not write %s: %s", self.path.name, exc)


def request_approval(deps, subject: str, hash_: str, detail: str = "") -> bool:
    """Decide whether *subject* (at content *hash_*) may proceed.

    Persisted grant → allow. Otherwise ask ``deps.approval_hook``; an "always"
    answer is persisted. Headless (no hook) denies, except a persisted grant is
    honored when ``approvals.headless_allow_granted`` is true.
    """
    store = ApprovalStore(deps.approvals_path)
    granted = store.is_granted(subject, hash_)
    policy = deps.settings.get("approvals") or {}

    if deps.approval_hook is None:                      # headless / no human
        return bool(granted and policy.get("headless_allow_granted"))
    if granted:
        return True
    answer = deps.approval_hook(subject, detail)
    if answer == ALLOW_ALWAYS:
        store.grant(subject, hash_)
        return True
    return answer == ALLOW_ONCE


def resolve_confirm(deps, name: str, rendered_args: str) -> bool:
    """Gate a confirm-listed tool call (Phase 2b), with "always allow" support.

    Prefers the richer ``approval_hook`` (persistent); falls back to the simple
    boolean ``confirm_hook``; with neither (headless, nothing configured) the
    call is refused.
    """
    if deps.approval_hook is not None:
        # Stable hash: confirm is about the tool, not its arguments.
        return request_approval(deps, f"confirm:{name}", "stable", rendered_args)
    if deps.confirm_hook is not None:
        return bool(deps.confirm_hook(name, rendered_args))
    return False
