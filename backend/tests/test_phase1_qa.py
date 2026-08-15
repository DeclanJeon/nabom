"""Phase 1 QA: design §14 edge cases, IDOR, fail-closed engines, coverage bands."""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-qa-", suffix=".sqlite")[1]
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


saju_main = _load_module("qa_saju_main", BACKEND / "saju-engine" / "app" / "main.py")
iching_main = _load_module("qa_iching_main", BACKEND / "iching-engine" / "app" / "main.py")
nabom_main = _load_module("qa_nabom_main", BACKEND / "nabom-api" / "app" / "main.py")

nabom_main.saju_transport = httpx.ASGITransport(app=saju_main.app)
nabom_main.iching_transport = httpx.ASGITransport(app=iching_main.app)
app = nabom_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def day_offset(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def birth_input():
    return {
        "calendar": "solar",
        "date": "1992-03-01",
        "time": "07:20",
        "time_precision": "exact",
        "location": {"label": "부산", "timezone": "Asia/Seoul", "lat": 35.1796, "lon": 129.0756},
        "gender": "male",
    }


async def dead_engine(scope, receive, send):
    from starlette.responses import JSONResponse

    response = JSONResponse(
        {"detail": {"code": "ENGINE_UNAVAILABLE", "message": "engine down", "retryable": True}},
        status_code=503,
    )
    await response(scope, receive, send)


async def signup(client, email: str, nickname: str = "QA") -> dict[str, str]:
    created = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password1", "nickname": nickname},
    )
    require(created.status_code == 200, f"signup {email}: {created.status_code} {created.text}")
    token = created.json()["token"]
    return {"Authorization": f"Bearer {token}"}


async def add_entry(client, headers, day: str, **fields):
    payload = {"date": day, "mood": 3, "energy": 3, "satisfaction": 3, "text": f"기록 {day}", **fields}
    response = await client.post("/api/v1/living/entries", json=payload, headers=headers)
    require(response.status_code == 200, f"entry {day}: {response.status_code} {response.text}")
    return response.json()


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        headers = await signup(client, "qa-edge@nabom.test", "엣지")
        other = await signup(client, "qa-other@nabom.test", "타인")

        # ── Auth / IDOR ───────────────────────────────────────────────────
        unauth = await client.get("/api/v1/living/entries")
        require(unauth.status_code == 401, f"unauth entries: {unauth.status_code}")
        bad = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-token"})
        require(bad.status_code == 401, f"bad token: {bad.status_code}")
        me = await client.get("/api/v1/auth/me", headers=headers)
        require(me.status_code == 200 and me.json()["email"] == "qa-edge@nabom.test", me.text)

        # ── Scale / text limits / emoji / multilingual ────────────────────
        scale = await client.post(
            "/api/v1/living/entries",
            json={"date": day_offset(20), "mood": 0, "energy": 3, "satisfaction": 3, "text": "bad"},
            headers=headers,
        )
        require(scale.status_code == 422, f"mood 0 should 422: {scale.status_code}")
        too_long = await client.post(
            "/api/v1/living/entries",
            json={"date": day_offset(20), "mood": 3, "energy": 3, "satisfaction": 3, "text": "가" * 8001},
            headers=headers,
        )
        require(too_long.status_code == 422, f"oversize daily: {too_long.status_code}")
        empty_ok = await client.post(
            "/api/v1/living/entries",
            json={"date": day_offset(19), "mood": 2, "energy": 5, "satisfaction": 1, "text": ""},
            headers=headers,
        )
        require(empty_ok.status_code == 200, f"empty daily text: {empty_ok.status_code} {empty_ok.text}")
        mixed = await add_entry(
            client,
            headers,
            day_offset(18),
            text="힘들었지만 괜찮아요 😊 今日は静かな日. café",
            mood=1,
            energy=5,
            satisfaction=2,
        )
        require(mixed["text"].startswith("힘들었지만"), mixed)

        # ── Duplicate same-day upsert ─────────────────────────────────────
        first = await add_entry(client, headers, day_offset(17), text="첫 기록")
        second = await add_entry(client, headers, day_offset(17), text="같은 날 다시")
        require(first["entry_id"] == second["entry_id"], "same-day upsert must keep entry_id")
        require(second["text"] == "같은 날 다시", second)

        # ── Timezone midnight rollover (Seoul UTC+9) ──────────────────────
        living = nabom_main.living
        just_before = datetime(2026, 8, 13, 14, 59, tzinfo=timezone.utc)
        just_after = datetime(2026, 8, 13, 15, 1, tzinfo=timezone.utc)
        require(living.local_today("Asia/Seoul", just_before).isoformat() == "2026-08-13", "before Seoul midnight")
        require(living.local_today("Asia/Seoul", just_after).isoformat() == "2026-08-14", "after Seoul midnight")
        # ── Timezone / future date ────────────────────────────────────────
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        future = await client.post(
            "/api/v1/living/entries",
            json={"date": tomorrow, "timezone": "Asia/Seoul", "mood": 3, "energy": 3, "satisfaction": 3, "text": "내일"},
            headers=headers,
        )
        require(future.status_code == 422, f"future seoul date: {future.status_code}")

        # ── Negative + conflicting evidence ───────────────────────────────
        low = await add_entry(client, headers, day_offset(16), mood=1, energy=1, satisfaction=1, text="바닥")
        ev_low = await client.post(
            "/api/v1/living/evidence",
            json={"source_type": "daily", "source_record_id": low["entry_id"], "timezone": "Asia/Seoul"},
            headers=headers,
        )
        require(ev_low.status_code == 200, ev_low.text)
        directions = {(s["trait"], s["direction"]) for s in ev_low.json()["signals"]}
        require(("recovery", "negative") in directions, ev_low.json())
        require(("execution", "negative") in directions, ev_low.json())
        clash = await add_entry(client, headers, day_offset(15), mood=5, energy=1, satisfaction=5, text="기분은 좋은데 힘은 없음")
        ev_clash = await client.post(
            "/api/v1/living/evidence",
            json={"source_type": "daily", "source_record_id": clash["entry_id"], "timezone": "Asia/Seoul"},
            headers=headers,
        )
        clash_dirs = {(s["trait"], s["direction"]) for s in ev_clash.json()["signals"]}
        require(("recovery", "positive") in clash_dirs and ("execution", "negative") in clash_dirs, ev_clash.json())

        # ── Coverage bands via reflections ────────────────────────────────
        empty_user = await signup(client, "qa-empty@nabom.test")
        start, end = day_offset(6), day_offset(0)
        none = await client.post(
            "/api/v1/living/reflections",
            json={"period_from": start, "period_to": end, "timezone": "Asia/Seoul"},
            headers=empty_user,
        )
        require(none.status_code == 422, f"0 days reflection: {none.status_code} {none.text}")

        async def coverage_for(email: str, offsets: list[int]) -> dict:
            user = await signup(client, email)
            for offset in offsets:
                saved = await add_entry(client, user, day_offset(offset), mood=4 if offset % 2 else 2, energy=4 if offset % 2 else 2)
                await client.post(
                    "/api/v1/living/evidence",
                    json={"source_type": "daily", "source_record_id": saved["entry_id"], "timezone": "Asia/Seoul"},
                    headers=user,
                )
            reflected = await client.post(
                "/api/v1/living/reflections",
                json={"period_from": start, "period_to": end, "timezone": "Asia/Seoul"},
                headers=user,
            )
            require(reflected.status_code == 200, f"{email} reflection: {reflected.status_code} {reflected.text}")
            return reflected.json()

        one = await coverage_for("qa-1day@nabom.test", [1])
        require(one["mirror"]["coverage"] == {"days_recorded": 1, "mode": "light"}, one["mirror"]["coverage"])
        require(one["mirror"]["patterns"] == [], one["mirror"])
        require(one["mirror"]["growth_experiment"] is None, one["mirror"])
        require("적어요" in one["mirror"]["summary"] or "단정" in " ".join(one["reflection"]["caution_signals"]), one)

        two = await coverage_for("qa-2day@nabom.test", [2, 1])
        require(two["mirror"]["coverage"]["mode"] == "light", two["mirror"]["coverage"])

        partial = await coverage_for("qa-4day@nabom.test", [4, 3, 2, 1])
        require(partial["mirror"]["coverage"] == {"days_recorded": 4, "mode": "partial"}, partial["mirror"]["coverage"])
        require("부분" in partial["mirror"]["summary"] or "조심스럽게" in partial["mirror"]["summary"], partial["mirror"]["summary"])

        full = await coverage_for("qa-7day@nabom.test", [6, 5, 4, 3, 2, 1, 0])
        require(full["mirror"]["coverage"]["mode"] == "full", full["mirror"]["coverage"])
        require(full["mirror"]["growth_experiment"]["reversible"] is True, full["mirror"])
        require("code" not in full["reflection"]["situation"], full["reflection"]["situation"])
        require(len(full["reflection"]["situation"]["label_ko"]) > 2, full["reflection"]["situation"])
        leaked = str(full)
        require("judgment_text" not in leaked and "name_zh" not in leaked, "raw hexagram leak")
        require("운명" not in leaked and "반드시" not in leaked, "forbidden certainty language")
        for pattern in full["mirror"]["patterns"]:
            title = pattern.get("title") or ""
            require("와(과)" not in title, title)
            if pattern.get("trait") == "execution":
                require(title.startswith("추진력과"), title)
            if pattern.get("trait") == "structure":
                require(title.startswith("안정감과"), title)

        # ── Cross-user IDOR ───────────────────────────────────────────────
        listed = await client.get("/api/v1/living/entries", headers=other)
        require(listed.json()["entries"] == [], listed.json())
        stolen = await client.get(f"/api/v1/living/entries/{first['entry_id']}", headers=other)
        require(stolen.status_code == 404, f"cross-user entry: {stolen.status_code}")
        stolen_mirror = await client.get(
            f"/api/v1/living/mirrors/{full['mirror']['mirror_id']}",
            headers=other,
        )
        require(stolen_mirror.status_code == 404, f"cross-user mirror: {stolen_mirror.status_code}")
        stolen_profile = await client.get("/api/v1/living/profiles/current", headers=other)
        require(stolen_profile.status_code == 404, f"other user has no profile: {stolen_profile.status_code}")

        # ── Engine unavailable must not create a profile ──────────────────
        previous = nabom_main.saju_transport
        nabom_main.saju_transport = httpx.ASGITransport(app=dead_engine)
        try:
            failed = await client.post(
                "/api/v1/living/profiles/initial",
                json={"birth_input": birth_input()},
                headers=headers,
            )
        finally:
            nabom_main.saju_transport = previous
        require(failed.status_code == 502, f"engine down: {failed.status_code} {failed.text}")
        require(failed.json()["detail"]["code"] == "ENGINE_UNAVAILABLE", failed.json())
        after_fail = await client.get("/api/v1/living/profiles/current", headers=headers)
        require(after_fail.status_code == 404, f"failed create must not leave a profile: {after_fail.status_code}")

        # ── Successful profile still works after engine recovery ──────────
        created = await client.post(
            "/api/v1/living/profiles/initial",
            json={"birth_input": birth_input(), "current_goal": "천천히 기록하기"},
            headers=headers,
        )
        require(created.status_code == 200, f"profile after recovery: {created.status_code} {created.text}")
        traits = created.json()["profile"]["traits"]
        require(all(0.05 <= t["value"] <= 0.95 for t in traits), traits)
        require(all(t["confidence"] <= 0.4 for t in traits), traits)
        require(all(t["label_ko"] for t in traits), traits)
        leaked = str(created.json())
        for term in ("주작", "백호", "청룡", "현무", "황룡", "일간", "丙", "병화", "오행", "용신"):
            require(term not in leaked, f"myeongni term leaked: {term}")
        require("four_pillars" not in leaked, leaked)
        require("use_god_schools" not in leaked, leaked)
        require("boundary_candidates" not in leaked, leaked)
        require(all(t["confidence"] <= 0.4 for t in created.json()["profile"]["traits"]), created.json()["profile"]["traits"])

        unknown_fb = await client.post(
            f"/api/v1/living/profiles/{created.json()['profile_version_id']}/feedback",
            json={"target_type": "trait", "target_key": "destiny", "rating": "correct"},
            headers=headers,
        )
        require(unknown_fb.status_code == 422, unknown_fb.text)

        # ── Export contains owned records only ────────────────────────────
        exported = await client.get("/api/v1/privacy/export", headers=headers)
        require(exported.status_code == 200, exported.text)
        payload = exported.json()
        require(payload["user_id"] == me.json()["user_id"], payload["user_id"])
        for profile in payload["profiles"]:
            require("analysis" not in profile, profile.keys())
            require("four_pillars" not in str(profile), profile)
        require("judgment_text" not in str(payload) and "name_zh" not in str(payload), "export must not include raw engine chart")


if __name__ == "__main__":
    asyncio.run(run())
    print("phase1-qa-edges: PASS")
