"""State store: both backends, chosen by file extension."""

import pytest

from agent.runtime.store import JSONStore, SQLiteStore, open_store


@pytest.mark.parametrize("filename", ["state.json", "state.db", "state.sqlite"])
def test_roundtrip(tmp_path, filename):
    store = open_store(tmp_path / filename)
    try:
        assert store.get("missing") is None
        assert store.get("missing", 42) == 42

        store.set("k", {"a": 1})
        assert store.get("k") == {"a": 1}

        assert store.append("log", "x") == ["x"]
        assert store.append("log", "y") == ["x", "y"]
        assert store.get("log") == ["x", "y"]

        assert set(store.keys()) == {"k", "log"}
        assert store.all()["k"] == {"a": 1}

        store.delete("k")
        assert store.get("k") is None
    finally:
        store.close()


def test_open_store_picks_backend(tmp_path):
    assert isinstance(open_store(tmp_path / "x.json"), JSONStore)
    assert isinstance(open_store(tmp_path / "x.db"), SQLiteStore)
    assert isinstance(open_store(tmp_path / "x.sqlite3"), SQLiteStore)


def test_persistence_across_instances(tmp_path):
    path = tmp_path / "state.json"
    s1 = open_store(path)
    s1.set("seen", ["a", "b"])
    s1.close()

    s2 = open_store(path)  # reopen — data must survive
    try:
        assert s2.get("seen") == ["a", "b"]
    finally:
        s2.close()
