"""NABOM facade persistence: pluggable KV store drivers.

Collections: profiles, mirrors, feedback, relationships, groups, group_member_profiles,
daily_entries, journals, evidence.

Driver selection via env:
  NABOM_STORE_DRIVER = sqlite (default) | postgres
  DATABASE_URL (postgres only) e.g. postgresql://user:pass@host:5432/nabom
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path


class StoreDriver:
    """(collection, record_key) → JSON payload KV interface."""

    def set(self, collection: str, key: str, value: dict) -> None:
        raise NotImplementedError

    def get(self, collection: str, key: str) -> dict | None:
        raise NotImplementedError

    def list(self, collection: str) -> list[dict]:
        raise NotImplementedError

    def list_keys(self, collection: str) -> list[str]:
        raise NotImplementedError

    def delete(self, collection: str, key: str) -> bool:
        raise NotImplementedError

    def count(self, collection: str) -> int:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class SqliteStore(StoreDriver):
    """SQLite-backed JSON KV store (default, zero-dependency)."""

    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nabom_records (
                collection TEXT NOT NULL,
                record_key TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (collection, record_key)
            )
            """
        )
        self._conn.commit()

    def set(self, collection: str, key: str, value: dict) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        self._conn.execute(
            "INSERT INTO nabom_records (collection, record_key, payload) VALUES (?, ?, ?) "
            "ON CONFLICT(collection, record_key) DO UPDATE SET payload = excluded.payload",
            (collection, key, payload),
        )
        self._conn.commit()

    def get(self, collection: str, key: str) -> dict | None:
        row = self._conn.execute(
            "SELECT payload FROM nabom_records WHERE collection = ? AND record_key = ?",
            (collection, key),
        ).fetchone()
        return json.loads(row["payload"]) if row else None

    def list(self, collection: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT payload FROM nabom_records WHERE collection = ? ORDER BY record_key",
            (collection,),
        ).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def list_keys(self, collection: str) -> list[str]:
        rows = self._conn.execute(
            "SELECT record_key FROM nabom_records WHERE collection = ? ORDER BY record_key",
            (collection,),
        ).fetchall()
        return [r["record_key"] for r in rows]

    def delete(self, collection: str, key: str) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM nabom_records WHERE collection = ? AND record_key = ?",
            (collection, key),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def count(self, collection: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS n FROM nabom_records WHERE collection = ?",
            (collection,),
        ).fetchone()
        return int(row["n"])

    def close(self):
        self._conn.close()


class PostgresStore(StoreDriver):
    """PostgreSQL-backed JSON KV store.

    Uses the same table shape as SqliteStore (collection, record_key, payload)
    so the driver is a drop-in swap. Requires psycopg (optional dependency);
    a missing driver at construction time is a clear configuration error.
    """

    DDL = """
    CREATE TABLE IF NOT EXISTS nabom_records (
        collection TEXT NOT NULL,
        record_key TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (collection, record_key)
    )
    """

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.environ.get(
            "DATABASE_URL", "postgresql://localhost:5432/nabom"
        )
        try:
            import psycopg
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "PostgresStore requires psycopg — install backend[postgres] or set NABOM_STORE_DRIVER=sqlite"
            ) from exc
        self._conn = psycopg.connect(self.database_url)
        self._conn.execute(self.DDL)
        self._conn.commit()

    def set(self, collection: str, key: str, value: dict) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO nabom_records (collection, record_key, payload) VALUES (%s, %s, %s) "
                "ON CONFLICT (collection, record_key) DO UPDATE SET payload = EXCLUDED.payload",
                (collection, key, payload),
            )
        self._conn.commit()

    def get(self, collection: str, key: str) -> dict | None:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT payload FROM nabom_records WHERE collection = %s AND record_key = %s",
                (collection, key),
            )
            row = cur.fetchone()
        return json.loads(row[0]) if row else None

    def list(self, collection: str) -> list[dict]:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT payload FROM nabom_records WHERE collection = %s ORDER BY record_key",
                (collection,),
            )
            rows = cur.fetchall()
        return [json.loads(r[0]) for r in rows]

    def list_keys(self, collection: str) -> list[str]:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT record_key FROM nabom_records WHERE collection = %s ORDER BY record_key",
                (collection,),
            )
            rows = cur.fetchall()
        return [r[0] for r in rows]

    def delete(self, collection: str, key: str) -> bool:
        with self._conn.cursor() as cur:
            cur.execute(
                "DELETE FROM nabom_records WHERE collection = %s AND record_key = %s",
                (collection, key),
            )
            deleted = cur.rowcount
        self._conn.commit()
        return deleted > 0

    def count(self, collection: str) -> int:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM nabom_records WHERE collection = %s",
                (collection,),
            )
            row = cur.fetchone()
        return int(row[0])

    def close(self):
        self._conn.close()


def create_store(driver: str | None = None, **kwargs) -> StoreDriver:
    """Driver factory. Defaults to sqlite for zero-config local/test runs."""
    selected = (driver or os.environ.get("NABOM_STORE_DRIVER", "sqlite")).strip().lower()
    if selected == "postgres":
        return PostgresStore(kwargs.get("database_url"))
    return SqliteStore(kwargs.get("path") or os.environ.get("NABOM_STORE_PATH", ":memory:"))


# 하위 호환: 기존 코드는 NabomStore 이름을 사용한다.
NabomStore = SqliteStore


# 프로세스 공유 싱글턴: main.py와 relations_routes.py가 같은 스토어를 사용한다.
default_store = create_store()
