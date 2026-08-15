"""Focused tests for Weekly Mirror coverage bands from stored records."""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-weekly-", suffix=".sqlite")[1]
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


nabom_main = _load_module("nabom_weekly_app_main", BACKEND / "nabom-api" / "app" / "main.py")
app = nabom_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def day_offset(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


async def add_day(client, user: str, day: str, mood=3, energy=3, satisfaction=3):
    response = await client.post(
        "/api/v1/living/entries",
        json={"date": day, "mood": mood, "energy": energy, "satisfaction": satisfaction, "text": f"기록 {day}"},
        headers={"X-User-Id": user},
    )
    require(response.status_code == 200, f"{day}: {response.status_code} {response.text}")
    return response.json()


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        start = day_offset(6)
        end = day_offset(0)
        empty = await client.post(
            "/api/v1/living/mirrors",
            json={"period_from": start, "period_to": end},
            headers={"X-User-Id": "usr_a"},
        )
        require(empty.status_code == 422, f"zero days: {empty.status_code} {empty.text}")

        await add_day(client, "usr_a", day_offset(6), mood=2, energy=2)
        await add_day(client, "usr_a", day_offset(5), mood=4, energy=4)
        light = await client.post(
            "/api/v1/living/mirrors",
            json={"period_from": start, "period_to": end},
            headers={"X-User-Id": "usr_a"},
        )
        require(light.status_code == 200, light.text)
        require(light.json()["coverage"] == {"days_recorded": 2, "mode": "light"}, light.json())
        require(light.json()["growth_experiment"] is None, light.json())
        require(light.json()["patterns"] == [], light.json())
        light_id = light.json()["mirror_id"]

        for offset in (4, 3, 2):
            await add_day(client, "usr_a", day_offset(offset), energy=2)
        full = await client.post(
            "/api/v1/living/mirrors",
            json={"period_from": start, "period_to": end},
            headers={"X-User-Id": "usr_a"},
        )
        require(full.status_code == 200, full.text)
        require(full.json()["coverage"]["mode"] == "full", full.json())
        require(full.json()["coverage"]["days_recorded"] == 5, full.json())
        require(full.json()["growth_experiment"]["reversible"] is True, full.json())
        require(full.json()["mirror_id"] != light_id, "mirrors must be append-only")
        require(full.json()["metrics"]["average_energy"] is not None, full.json())

        other = await client.get(f"/api/v1/living/mirrors/{full.json()['mirror_id']}", headers={"X-User-Id": "usr_b"})
        require(other.status_code == 404, f"cross-user mirror: {other.status_code}")

        listed = await client.get("/api/v1/living/mirrors", headers={"X-User-Id": "usr_a"})
        require(len(listed.json()["mirrors"]) == 2, listed.json())


if __name__ == "__main__":
    asyncio.run(run())
    print("weekly-mirror-contract: PASS")
