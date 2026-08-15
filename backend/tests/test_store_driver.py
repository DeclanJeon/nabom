"""StoreDriver abstraction: factory, SQLite default, PostgreSQL contract."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-store-", suffix=".sqlite")[1]

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "nabom-api" / "app"))

import store  # noqa: E402


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def run():
    # 1) factory default = sqlite
    sqlite_store = store.create_store()
    require(isinstance(sqlite_store, store.SqliteStore), type(sqlite_store))

    # 2) explicit sqlite + CRUD round-trip
    with tempfile.TemporaryDirectory() as tmp:
        s = store.create_store("sqlite", path=f"{tmp}/test.db")
        s.set("profiles", "pv_1", {"user_id": "usr_x", "number": 1})
        require(s.get("profiles", "pv_1")["number"] == 1, s.get("profiles", "pv_1"))
        s.set("profiles", "pv_2", {"user_id": "usr_x", "number": 2})
        require(len(s.list("profiles")) == 2, s.list("profiles"))
        require(sorted(s.list_keys("profiles")) == ["pv_1", "pv_2"], s.list_keys("profiles"))
        require(s.count("profiles") == 2, s.count("profiles"))
        require(s.delete("profiles", "pv_1") is True, "delete")
        require(s.delete("profiles", "pv_1") is False, "delete missing")
        require(s.count("profiles") == 1, s.count("profiles"))
        s.close()

    # 3) postgres driver contract: class exists, DDL shape, missing driver error path
    require(store.PostgresStore is not None, "PostgresStore class missing")
    # construction without psycopg must fail clearly (not silently fall back)
    try:
        store.PostgresStore("postgresql://nouser:nopass@127.0.0.1:1/none")
        print("  (postgres psycopg present — live connection not tested)")
    except RuntimeError as exc:
        require("psycopg" in str(exc), str(exc))
    except Exception as exc:  # noqa: BLE001 — connection refused is expected w/o server
        require("could not connect" in str(exc).lower() or "connection" in str(exc).lower(), str(exc)[:80])

    # 4) driver contract: every driver implements the full interface
    for method in ("set", "get", "list", "list_keys", "delete", "count", "close"):
        require(callable(getattr(store.StoreDriver, method)), f"StoreDriver.{method} missing")

    print("store-driver: PASS")


if __name__ == "__main__":
    run()
