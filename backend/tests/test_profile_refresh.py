"""Profile refresh: evidence blend → new ProfileVersion (002)."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-refresh-", suffix=".sqlite")[1]
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


saju_main = _load_module("ref_saju_main", BACKEND / "saju-engine" / "app" / "main.py")
nabom_main = _load_module("ref_nabom_main", BACKEND / "nabom-api" / "app" / "main.py")
nabom_main.saju_transport = httpx.ASGITransport(app=saju_main.app)
app = nabom_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def day_offset(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        created = await client.post(
            "/api/v1/auth/signup",
            json={"email": "refresh@nabom.test", "password": "password1", "nickname": "REFRESH"},
        )
        require(created.status_code == 200, f"signup: {created.status_code} {created.text}")
        token = created.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1) initial profile
        profile = await client.post(
            "/api/v1/living/profiles/initial",
            json={
                "birth_input": {
                    "calendar": "solar",
                    "date": "1992-03-01",
                    "time": "07:20",
                    "time_precision": "exact",
                    "gender": "male",
                    "location": {"label": "부산", "timezone": "Asia/Seoul", "lat": 35.1796, "lon": 129.0756},
                },
                "current_priorities": ["career"],
                "change_goal": "t",
                "current_goal": "t",
            },
            headers=headers,
        )
        require(profile.status_code == 200, f"initial: {profile.status_code} {profile.text}")
        p1 = profile.json()["profile"]
        require(p1["number"] == 1, p1["number"])

        # 2) refresh without enough evidence → 409
        early = await client.post("/api/v1/living/profiles/refresh", headers=headers)
        require(early.status_code == 409, f"early refresh: {early.status_code} {early.text}")
        require(early.json()["detail"]["code"] == "INSUFFICIENT_EVIDENCE", early.json())

        # 3) add 28 days of entries (evidence generated via upsert)
        for i in range(28):
            day = day_offset(i)
            res = await client.post(
                "/api/v1/living/entries",
                json={
                    "date": day,
                    "timezone": "Asia/Seoul",
                    "mood": 4 if i % 2 == 0 else 5,
                    "energy": 4,
                    "satisfaction": 4,
                    "text": "오늘은 기록을 남긴 날입니다. 에너지가 좋았어요.",
                    "tags": ["growth"],
                },
                headers=headers,
            )
            require(res.status_code == 200, f"entry {i}: {res.status_code} {res.text[:120]}")

        evidence = await client.get("/api/v1/living/entries", headers=headers)
        require(evidence.status_code == 200, "entries list")

        # 4) refresh now → new version 002 with refresh metadata
        refreshed = await client.post("/api/v1/living/profiles/refresh", headers=headers)
        require(refreshed.status_code == 200, f"refresh: {refreshed.status_code} {refreshed.text[:200]}")
        body = refreshed.json()
        p2 = body["profile"]
        require(p2["number"] == 2, p2["number"])
        require(body["refresh"]["recorded_days"] >= 28, body["refresh"])
        require(body["refresh"]["previous_version"] == p1["profile_version_id"], body["refresh"])
        require("visual_key" not in p2["character_profile"], p2["character_profile"])
        require(p2["character_profile"]["condition_state"] in {"rising", "steady", "strained", "recovering"}, p2["character_profile"])

        # 5) current profile is now version 2
        current = await client.get("/api/v1/living/profiles/current", headers=headers)
        require(current.status_code == 200 and current.json()["profile"]["number"] == 2, current.text[:150])

        # 6) idempotency: same call returns cached
        again = await client.post(
            "/api/v1/living/profiles/refresh",
            headers={**headers, "Idempotency-Key": "refresh-key-1"},
        )
        require(again.status_code == 200, f"idempotent: {again.status_code} {again.text[:200]}")
        cached = await client.post(
            "/api/v1/living/profiles/refresh",
            headers={**headers, "Idempotency-Key": "refresh-key-1"},
        )
        require(cached.status_code == 200, f"cached: {cached.status_code} {cached.text[:200]}")
        cached_body = cached.json()
        require(
            cached_body.get("profile_version_id") == again.json().get("profile_version_id"),
            f"idempotency replay: {again.text[:120]} vs {cached.text[:120]}",
        )

        # 7) leak scan
        raw = str(body)
        for leaked in ("주작", "백호", "청룡", "현무", "황룡", "일간", "병화", "오행", "용신", "신강", "신약", "대운", "세운", "운세"):
            require(leaked not in raw, f"leak: {leaked}")

    print("profile-refresh: PASS")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
