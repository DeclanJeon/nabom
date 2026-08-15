"""Phase 1 facade contract tests: current profile, reflection latest,
experiments, journey, feedback, account delete (offline, ASGI)."""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-p1-", suffix=".sqlite")[1]
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


saju_main = _load_module("p1_saju_main", BACKEND / "saju-engine" / "app" / "main.py")
iching_main = _load_module("p1_iching_main", BACKEND / "iching-engine" / "app" / "main.py")
nabom_main = _load_module("p1_nabom_main", BACKEND / "nabom-api" / "app" / "main.py")

nabom_main.saju_transport = httpx.ASGITransport(app=saju_main.app)
nabom_main.iching_transport = httpx.ASGITransport(app=iching_main.app)

app = nabom_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def birth_input():
    return {
        "calendar": "solar",
        "date": "1992-03-01",
        "time": "07:20",
        "time_precision": "exact",
        "location": {"label": "부산", "timezone": "Asia/Seoul", "lat": 35.1796, "lon": 129.0756},
        "gender": "male",
    }


def day_offset(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        # ── 1) signup + initial profile ───────────────────────────────────
        created = await client.post(
            "/api/v1/auth/signup",
            json={"email": "p1@nabom.test", "password": "password1", "nickname": "P1"},
        )
        require(created.status_code == 200, f"signup: {created.status_code} {created.text}")
        token = created.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = await client.get("/api/v1/auth/me", headers=headers)
        require(me.status_code == 200, f"auth me: {me.status_code} {me.text}")
        require(me.json()["email"] == "p1@nabom.test", me.json())
        require(me.json()["nickname"] == "P1", me.json())

        profile = await client.post(
            "/api/v1/living/profiles/initial",
            json={
                "birth_input": birth_input(),
                "current_priorities": ["career", "growth"],
                "change_goal": "완성도 높이기",
                "current_goal": "3개월 안에 취미 하나 꾸준히 하기",
            },
            headers=headers,
        )
        require(profile.status_code == 200, f"initial profile: {profile.status_code} {profile.text}")
        body = profile.json()
        p = body["profile"]
        require(p["number"] == 1, "profile number must be 1")
        require(p["identity_sentence"], "identity sentence missing")
        require(len(p["traits"]) >= 2, f"traits must include at least dominant+deficient: {p['traits']}")
        require(all("label_ko" in t and "value" in t and "confidence" in t for t in p["traits"]), "trait shape")
        require(len(p["strengths"]) == 3, "3 strengths expected")
        require(len(p["watch_patterns"]) >= 1, "watch patterns expected")
        require(p["growth_theme"], "growth theme missing")
        require(p["character_profile"]["guardian_beast"]["label_ko"], "guardian beast label missing")
        require(p["character_profile"]["guardian_beast"]["source"] == "day_stem_element", "beast source")
        require(p["character_profile"]["guardian_beast"]["code"] == "brightener", p["character_profile"])
        require("visual_key" not in p["character_profile"], "internal visual key must stay hidden")
        require(p["character_profile"]["condition_state"] == "steady", p["character_profile"])
        require(p["character_profile"]["condition_label"], p["character_profile"])
        require(str(p["character_profile"]["image_url"]).startswith("/characters/brightener_"), p["character_profile"])
        require("narrative" not in p and "use_god_candidates" not in p, "internal engine fields must stay hidden")
        raw = str(body)
        require("judgment_text" not in raw and "name_zh" not in raw, "raw engine data must not leak")
        for leaked in ("주작", "백호", "청룡", "현무", "황룡", "일간", "丙", "병화", "오행", "용신"):
            require(leaked not in raw, f"myeongni term leaked: {leaked}")

        # ── 2) current profile ────────────────────────────────────────────
        current = await client.get("/api/v1/living/profiles/current", headers=headers)
        require(current.status_code == 200, f"current profile: {current.status_code} {current.text}")
        require(current.json()["profile"]["profile_version_id"] == body["profile_version_id"], "current must be latest")
        require(current.json()["character_profile"]["guardian_beast"]["label_ko"], "current character profile")

        # ── 3) feedback (Phase 1 5단계 rating) ────────────────────────────
        bad = await client.post(
            f"/api/v1/living/profiles/{body['profile_version_id']}/feedback",
            json={"target_type": "trait", "target_key": "nope", "rating": "incorrect"},
            headers=headers,
        )
        require(bad.status_code == 422, f"unknown trait should 422: {bad.status_code}")
        feedback = await client.post(
            f"/api/v1/living/profiles/{body['profile_version_id']}/feedback",
            json={"target_type": "overall", "target_key": "overall", "rating": "mostly_correct", "comment": "대체로 비슷해요"},
            headers=headers,
        )
        require(feedback.status_code == 200, f"feedback: {feedback.status_code} {feedback.text}")
        require(feedback.json()["feedback"]["rating"] == "mostly_correct", "rating roundtrip")

        # ── 4) entry + evidence + reflection ──────────────────────────────
        start, end = day_offset(6), day_offset(0)
        for offset in (6, 5, 4, 3, 2, 1, 0):
            entry = await client.post(
                "/api/v1/living/entries",
                json={"date": day_offset(offset), "mood": 4 if offset % 2 else 3, "energy": 4 if offset % 2 else 2, "satisfaction": 4, "text": f"기록 {offset}일차"},
                headers=headers,
            )
            require(entry.status_code == 200, f"entry {offset}: {entry.status_code} {entry.text}")
            entry_id = entry.json()["entry_id"]
            evidence = await client.post(
                "/api/v1/living/evidence",
                json={"source_type": "daily", "source_record_id": entry_id, "timezone": "Asia/Seoul"},
                headers=headers,
            )
            require(evidence.status_code == 200, f"evidence {offset}: {evidence.status_code} {evidence.text}")

        reflection = await client.post(
            "/api/v1/living/reflections",
            json={"period_from": start, "period_to": end, "timezone": "Asia/Seoul"},
            headers=headers,
        )
        require(reflection.status_code == 200, f"reflection: {reflection.status_code} {reflection.text}")
        rbody = reflection.json()
        require(rbody["mirror"]["coverage"]["mode"] == "full", rbody["mirror"]["coverage"])
        require(rbody["mirror"]["notable_moments"], "notable moments should be generated")
        require(rbody["mirror"]["emotion_flow"] and rbody["mirror"]["emotion_flow"][0].get("label"), "emotion flow labels")
        require(rbody["reflection"]["situation"]["label_ko"], "situation label missing")
        require("code" not in rbody["reflection"]["situation"], "situation must not expose internal hexagram code")
        require(len(rbody["reflection"]["situation"]["label_ko"]) > 2, "situation label must be user-facing, not a hexagram name")
        # Vault 주제별 해석 렌즈가 일상어로 연결되어야 한다
        situation = rbody["reflection"]["situation"]
        if situation.get("theme_lens"):
            require(situation["theme_topic"], "theme topic missing")
            require("—" not in situation["theme_lens"], "theme lens must not include hexagram name prefix")
            require(all(ord(ch) < 0x4E00 or ord(ch) > 0x9FFF for ch in situation["theme_lens"]), "theme lens must not contain hanja")
            require(len(situation["theme_lens"]) <= 80, "theme lens must not be classical text")
        require(rbody["reflection"]["resolver_version"], "resolver version missing")
        require(rbody["reflection"]["evidence_refs"], "evidence refs missing")
        raw_r = str(rbody)
        require("judgment_text" not in raw_r and "name_zh" not in raw_r, "raw hexagram must not leak")

        latest = await client.get("/api/v1/living/reflections/latest", headers=headers)
        require(latest.status_code == 200, f"latest reflection: {latest.status_code} {latest.text}")
        require(latest.json()["reflection"]["reflection_id"] == rbody["reflection"]["reflection_id"], "latest must match created")
        require(latest.json()["mirror"]["mirror_id"] == rbody["mirror"]["mirror_id"], "latest mirror must match")

        # ── 5) experiments ────────────────────────────────────────────────
        exps = await client.get("/api/v1/living/experiments", headers=headers)
        require(exps.status_code == 200 and len(exps.json()["experiments"]) == 1, f"experiments: {exps.text}")
        experiment_id = exps.json()["experiments"][0]["experiment_id"]
        started = await client.post(
            f"/api/v1/living/experiments/{experiment_id}",
            json={"status": "in_progress"},
            headers=headers,
        )
        require(started.status_code == 200 and started.json()["status"] == "in_progress", f"start experiment: {started.text}")
        completed = await client.post(
            f"/api/v1/living/experiments/{experiment_id}",
            json={"status": "completed", "user_result": "4일 동안 기록했어요"},
            headers=headers,
        )
        require(completed.status_code == 200 and completed.json()["user_result"] == "4일 동안 기록했어요", f"complete experiment: {completed.text}")
        cross = await client.get(f"/api/v1/living/experiments/{experiment_id}", headers={"Authorization": "Bearer bad-token"})
        require(cross.status_code == 401, f"experiment auth: {cross.status_code}")

        # ── 6) journey ────────────────────────────────────────────────────
        journey = await client.get("/api/v1/living/journey", headers=headers)
        require(journey.status_code == 200, f"journey: {journey.status_code} {journey.text}")
        jbody = journey.json()
        require(jbody["summary"]["profile_count"] == 1, jbody["summary"])
        require(jbody["summary"]["recorded_days"] == 7, jbody["summary"])
        require(len(jbody["profiles"]) == 1 and jbody["profiles"][0]["traits"], "journey profiles")

        # ── 7) living records delete keeps the account ────────────────────
        wiped = await client.delete("/api/v1/living/records", headers=headers)
        require(wiped.status_code == 200, f"records delete: {wiped.status_code} {wiped.text}")
        still_me = await client.get("/api/v1/auth/me", headers=headers)
        require(still_me.status_code == 200, still_me.text)
        still_profile = await client.get("/api/v1/living/profiles/current", headers=headers)
        require(still_profile.status_code == 200, still_profile.text)
        gone_entries = await client.get("/api/v1/living/entries", headers=headers)
        require(gone_entries.status_code == 200 and gone_entries.json()["entries"] == [], gone_entries.text)
        gone_exps = await client.get("/api/v1/living/experiments", headers=headers)
        require(gone_exps.status_code == 200 and gone_exps.json()["experiments"] == [], gone_exps.text)

        # ── 8) account delete ─────────────────────────────────────────────
        deleted = await client.delete("/api/v1/account", headers=headers)
        require(deleted.status_code == 200, f"account delete: {deleted.status_code} {deleted.text}")
        after = await client.get("/api/v1/living/profiles/current", headers=headers)
        require(after.status_code in {401, 404}, f"profile must be gone after delete: {after.status_code}")
        gone = await client.get("/api/v1/living/experiments", headers=headers)
        require(gone.status_code in {200, 401}, f"experiments after delete: {gone.status_code}")
        if gone.status_code == 200:
            require(gone.json()["experiments"] == [], "experiments must be deleted")
        me_gone = await client.get("/api/v1/auth/me", headers=headers)
        require(me_gone.status_code == 401, f"session must be revoked: {me_gone.status_code}")


if __name__ == "__main__":
    asyncio.run(run())
    print("phase1-facade-contract: PASS")
