"""Two agent instances must not interfere: separate workspace + state store."""

from agent.config import load_config
from agent.context import build_deps, close_deps


def test_two_instances_are_isolated(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "settings.yaml").write_text("name: a\nstore: state.json\n", encoding="utf-8")
    (b / "settings.yaml").write_text("name: b\nstore: state.json\n", encoding="utf-8")

    da = build_deps(load_config(a))
    db = build_deps(load_config(b))
    try:
        # Each instance has its own sandbox.
        assert da.workspace != db.workspace

        # Writes to one store are invisible to the other.
        da.store.set("k", "from-a")
        db.store.set("k", "from-b")
        assert da.store.get("k") == "from-a"
        assert db.store.get("k") == "from-b"

        # State files live under their own workspace, not shared.
        assert (a / "workspace" / "state.json").exists()
        assert (b / "workspace" / "state.json").exists()
    finally:
        close_deps(da)
        close_deps(db)
