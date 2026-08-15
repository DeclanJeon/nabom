"""Focused ASGI tests for authenticated living-record APIs."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-living-", suffix=".sqlite")[1]
os.environ["NABOM_GENERATE_CHARACTERS"] = "0"
os.environ["NABOM_CHARACTER_DIR"] = tempfile.mkdtemp(prefix="nabom-char-")


import httpx  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


nabom_main = _load_module("nabom_living_app_main", BACKEND / "nabom-api" / "app" / "main.py")
app = nabom_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def headers(user: str) -> dict[str, str]:
    return {"X-User-Id": user}
def test_timezone_midnight_rollover():
    living = nabom_main.living
    just_before = datetime(2026, 8, 13, 14, 59, tzinfo=timezone.utc)
    just_after = datetime(2026, 8, 13, 15, 1, tzinfo=timezone.utc)
    require(living.local_today("Asia/Seoul", just_before).isoformat() == "2026-08-13", living.local_today("Asia/Seoul", just_before))
    require(living.local_today("Asia/Seoul", just_after).isoformat() == "2026-08-14", living.local_today("Asia/Seoul", just_after))
    require(living.parse_record_date("2026-08-13", "Asia/Seoul", just_before).isoformat() == "2026-08-13", "same local day must be allowed")
    try:
        living.parse_record_date("2026-08-14", "Asia/Seoul", just_before)
        raise SystemExit("Seoul tomorrow before midnight must be rejected")
    except living.LivingRecordError as error:
        require("future" in str(error), error)
    require(living.parse_record_date("2026-08-14", "Asia/Seoul", just_after).isoformat() == "2026-08-14", "after Seoul midnight must be allowed")


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        denied = await client.post(
            "/api/v1/living/entries",
            json={"date": "2026-08-12", "mood": 3, "energy": 3, "satisfaction": 3},
        )
        require(denied.status_code == 401, f"unauthenticated daily: {denied.status_code} {denied.text}")

        created = await client.post(
            "/api/v1/living/entries",
            json={
                "date": "2026-08-12",
                "timezone": "Asia/Seoul",
                "mood": 3,
                "energy": 2,
                "satisfaction": 4,
                "text": "오늘 작업을 마무리했다",
                "tags": ["work"],
            },
            headers=headers("usr_a"),
        )
        require(created.status_code == 200, f"daily create: {created.status_code} {created.text}")
        entry = created.json()
        require(entry["entry_id"].startswith("entry_"), entry["entry_id"])
        require(entry["mood"] == 3 and entry["energy"] == 2, entry)

        updated = await client.post(
            "/api/v1/living/entries",
            json={
                "date": "2026-08-12",
                "timezone": "Asia/Seoul",
                "mood": 4,
                "energy": 3,
                "satisfaction": 4,
                "text": "같은 날 다시 기록",
                "tags": ["work", "recovery"],
            },
            headers=headers("usr_a"),
        )
        require(updated.status_code == 200, f"daily upsert: {updated.status_code} {updated.text}")
        require(updated.json()["entry_id"] == entry["entry_id"], "same-day daily must keep entry_id")
        require(updated.json()["mood"] == 4, updated.json())

        future = await client.post(
            "/api/v1/living/entries",
            json={"date": "2099-01-01", "mood": 3, "energy": 3, "satisfaction": 3},
            headers=headers("usr_a"),
        )
        require(future.status_code == 422, f"future date: {future.status_code}")
        require(future.json()["detail"]["code"] == "INVALID_INPUT", future.json())

        bad_tz = await client.post(
            "/api/v1/living/entries",
            json={"date": "2026-08-11", "timezone": "Not/AZone", "mood": 3, "energy": 3, "satisfaction": 3},
            headers=headers("usr_a"),
        )
        require(bad_tz.status_code == 422, f"bad timezone: {bad_tz.status_code}")

        empty_journal = await client.post(
            "/api/v1/living/journals",
            json={"date": "2026-08-12", "text": "   "},
            headers=headers("usr_a"),
        )
        require(empty_journal.status_code == 422, f"empty journal: {empty_journal.status_code}")

        journal = await client.post(
            "/api/v1/living/journals",
            json={"date": "2026-08-12", "text": "불편함이 있었지만 하던 작업을 마무리함", "tags": ["work"]},
            headers=headers("usr_a"),
        )
        require(journal.status_code == 200, f"journal create: {journal.status_code} {journal.text}")
        journal_id = journal.json()["journal_id"]

        other = await client.get(f"/api/v1/living/journals/{journal_id}", headers=headers("usr_b"))
        require(other.status_code == 404, f"cross-user journal: {other.status_code}")

        daily_ev = await client.post(
            "/api/v1/living/evidence",
            json={"source_type": "daily", "source_record_id": entry["entry_id"]},
            headers=headers("usr_a"),
        )
        require(daily_ev.status_code == 200, f"daily evidence: {daily_ev.status_code} {daily_ev.text}")
        require("text" not in daily_ev.json(), daily_ev.json())
        require(daily_ev.json()["source_record_id"] == entry["entry_id"], daily_ev.json())

        journal_ev = await client.post(
            "/api/v1/living/evidence",
            json={"source_type": "journal", "source_record_id": journal_id},
            headers=headers("usr_a"),
        )
        require(journal_ev.status_code == 200, f"journal evidence: {journal_ev.status_code} {journal_ev.text}")
        require("불편함이 있었지만 하던 작업을 마무리함" == journal_ev.json()["summary"], journal_ev.json())
        require("text" not in journal_ev.json(), journal_ev.json())

        listed = await client.get("/api/v1/living/entries", headers=headers("usr_b"))
        require(listed.status_code == 200, listed.text)
        require(listed.json()["entries"] == [], listed.json())

        owned = await client.get("/api/v1/living/entries", headers=headers("usr_a"))
        require(len(owned.json()["entries"]) == 1, owned.json())

        rel = await client.post(
            "/api/v1/relationships",
            json={"participant_user_id": "usr_b"},
            headers=headers("usr_a"),
        )
        require(rel.status_code == 200, f"relationship: {rel.status_code} {rel.text}")
        body = rel.json()
        require("journal" not in body and "text" not in body and "birth_inputs" not in body, body)


if __name__ == "__main__":
    import asyncio

    test_timezone_midnight_rollover()
    asyncio.run(run())
    print("living-records-contract: PASS")


def test_experiment_limit(_=None):
    """설계 §9: 활성 Growth Experiment 최대 3개."""
    os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-exp-", suffix=".sqlite")[1]
    import importlib, store  # noqa: F401
    importlib.reload(store)
    from living_routes import store_experiments_from_mirror, _active_experiment_count, MAX_ACTIVE_EXPERIMENTS

    assert MAX_ACTIVE_EXPERIMENTS == 3
    for i in range(4):
        store_experiments_from_mirror(
            "usr_x",
            {
                "mirror_id": f"wm_{i}",
                "generated_at": f"2026-08-{i+1:02d}T00:00:00+00:00",
                "growth_experiment": {
                    "experiment_id": f"exp_{i}",
                    "title": f"실험 {i}",
                    "instruction": "테스트",
                    "success_condition": "완료",
                    "reversible": True,
                },
            },
        )
    records = [r for r in store.default_store.list("experiments") if r.get("user_id") == "usr_x"]
    assert len(records) == 3, f"expected 3 active experiments, got {len(records)}"
    assert _active_experiment_count("usr_x") == 3
    # 하나 완료하면 새 실험 허용
    records[0]["status"] = "completed"
    store.default_store.set("experiments", records[0]["experiment_id"], records[0])
    store_experiments_from_mirror(
        "usr_x",
        {
            "mirror_id": "wm_9",
            "generated_at": "2026-08-10T00:00:00+00:00",
            "growth_experiment": {
                "experiment_id": "exp_9",
                "title": "실험 9",
                "instruction": "t",
                "success_condition": "c",
                "reversible": True,
            },
        },
    )
    assert store.default_store.get("experiments", "exp_9") is not None, "완료 후 새 실험 허용"
    print("experiment-limit: PASS")


if __name__ == "__main__":
    test_experiment_limit()
