"""Read-only update check: version parsing, comparison, and tag selection."""

import io
import json

from agent.runtime import updates


def test_current_version_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "genesis-agent"\nversion = "1.2.3"\n', encoding="utf-8"
    )
    assert updates.current_version(tmp_path) == "1.2.3"


def test_current_version_unknown_without_pyproject(tmp_path):
    # No pyproject and no installed metadata under this name in tmp → graceful.
    v = updates.current_version(tmp_path / "nope")
    assert isinstance(v, str)  # never raises; "unknown" or installed version


def test_is_newer():
    assert updates.is_newer("v0.6.0", "0.5.0") is True
    assert updates.is_newer("0.5.1", "0.5.0") is True
    assert updates.is_newer("v0.5.0", "0.5.0") is False
    assert updates.is_newer("v0.4.9", "0.5.0") is False
    assert updates.is_newer("garbage", "0.5.0") is False   # never nags on junk
    assert updates.is_newer("v1.0.0", "unknown") is False


def test_repo_slug_env_override(monkeypatch):
    monkeypatch.setenv("GENESIS_REPO", "me/fork")
    assert updates.repo_slug() == "me/fork"
    assert updates.repo_url() == "https://github.com/me/fork"


def test_latest_version_picks_highest_semver(monkeypatch):
    payload = json.dumps([
        {"name": "v0.4.0"}, {"name": "v0.10.0"}, {"name": "v0.9.1"},
        {"name": "nightly"}, {"name": "v0.10.0-rc1"},
    ]).encode()

    class _Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): self.close()

    monkeypatch.setattr(updates.urllib.request, "urlopen", lambda req, timeout=0: _Resp(payload))
    assert updates.latest_version("x/y") == "v0.10.0"   # numeric, not lexical


def test_latest_version_none_on_error(monkeypatch):
    def boom(req, timeout=0):
        raise OSError("no network")

    monkeypatch.setattr(updates.urllib.request, "urlopen", boom)
    assert updates.latest_version("x/y") is None
