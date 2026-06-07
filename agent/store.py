"""Pluggable state store — the seam for cross-run state.

A minimal ``get/set/delete/append/all`` interface over either a JSON file or a
SQLite file in ``workspace/``. Trading positions/history, RSS seen-URL dedup,
counters — anything a vertical needs to remember between runs — live here
without touching the core.

Backend is chosen by file extension:

- ``.db`` / ``.sqlite``  → :class:`SQLiteStore`
- anything else (``.json``) → :class:`JSONStore`

``append(key, value)`` treats the value at *key* as a list and pushes onto it,
which is the natural primitive for logs and dedup sets.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class Store:
    """Common interface. Use :func:`open_store` to get a concrete backend."""

    def get(self, key: str, default: Any = None) -> Any:  # pragma: no cover
        raise NotImplementedError

    def set(self, key: str, value: Any) -> None:  # pragma: no cover
        raise NotImplementedError

    def delete(self, key: str) -> None:  # pragma: no cover
        raise NotImplementedError

    def append(self, key: str, value: Any) -> list:  # pragma: no cover
        raise NotImplementedError

    def all(self) -> dict:  # pragma: no cover
        raise NotImplementedError

    def keys(self) -> list[str]:
        return list(self.all().keys())

    def close(self) -> None:
        pass


class JSONStore(Store):
    """Whole-file JSON store. Simple and human-readable; fine up to a few MB."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict = {}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8") or "{}")
            except json.JSONDecodeError:
                self._data = {}

    def _flush(self) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, default=str), encoding="utf-8")
        tmp.replace(self.path)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self._flush()

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)
            self._flush()

    def append(self, key: str, value: Any) -> list:
        with self._lock:
            lst = self._data.get(key)
            if not isinstance(lst, list):
                lst = []
            lst.append(value)
            self._data[key] = lst
            self._flush()
            return list(lst)

    def all(self) -> dict:
        with self._lock:
            return dict(self._data)


class SQLiteStore(Store):
    """SQLite-backed KV store (values JSON-encoded). Durable under concurrency."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)"
        )
        self._conn.commit()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM kv WHERE key = ?", (key,)
            ).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO kv(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, json.dumps(value, default=str)),
            )
            self._conn.commit()

    def delete(self, key: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM kv WHERE key = ?", (key,))
            self._conn.commit()

    def append(self, key: str, value: Any) -> list:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM kv WHERE key = ?", (key,)
            ).fetchone()
            lst = json.loads(row[0]) if row else []
            if not isinstance(lst, list):
                lst = []
            lst.append(value)
            self._conn.execute(
                "INSERT INTO kv(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, json.dumps(lst, default=str)),
            )
            self._conn.commit()
            return lst

    def all(self) -> dict:
        with self._lock:
            rows = self._conn.execute("SELECT key, value FROM kv").fetchall()
        return {k: json.loads(v) for k, v in rows}

    def close(self) -> None:
        self._conn.close()


def open_store(path: str | Path) -> Store:
    """Return a :class:`Store` backed by JSON or SQLite, chosen by extension."""
    suffix = Path(path).suffix.lower()
    if suffix in (".db", ".sqlite", ".sqlite3"):
        return SQLiteStore(path)
    return JSONStore(path)
