"""Tests for the facade SQLite store: durability, collections, isolation."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "nabom-api" / "app"))

from store import NabomStore  # noqa: E402


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def test_durable_across_reopen():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "nabom.sqlite"
        store = NabomStore(db)
        store.set("profiles", "pv_1", {"user_id": "usr_a", "profile": {"trait_candidates": []}})
        store.set("feedback", "usr_a:pv_1", [{"trait": "x", "rating": "rejected"}])
        store.close()

        # 재시작 시뮬레이션: 새 인스턴스로 같은 파일
        reopened = NabomStore(db)
        profile = reopened.get("profiles", "pv_1")
        require(profile is not None and profile["user_id"] == "usr_a", "profile should survive restart")
        fb = reopened.get("feedback", "usr_a:pv_1")
        require(fb and fb[0]["rating"] == "rejected", "feedback should survive restart")
        require(reopened.count("profiles") == 1, "count after restart")
        reopened.close()


def test_collection_isolation():
    store = NabomStore()
    store.set("profiles", "k1", {"a": 1})
    store.set("mirrors", "k1", {"b": 2})
    require(store.get("profiles", "k1") == {"a": 1}, "profiles read")
    require(store.get("mirrors", "k1") == {"b": 2}, "mirrors read")
    require(store.get("mirrors", "k2") is None, "missing key returns None")
    require(store.list_keys("profiles") == ["k1"], "list keys")


def test_update_and_delete():
    store = NabomStore()
    store.set("profiles", "k", {"v": 1})
    store.set("profiles", "k", {"v": 2})
    require(store.get("profiles", "k")["v"] == 2, "upsert should overwrite")
    require(store.delete("profiles", "k") is True, "delete ok")
    require(store.get("profiles", "k") is None, "deleted")


def main():
    test_durable_across_reopen()
    test_collection_isolation()
    test_update_and_delete()
    print("store persistence tests passed")


if __name__ == "__main__":
    main()
