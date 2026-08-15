"""Account signup/login/recovery and birth fail-closed QA."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_RECOVERY_RETURN_TOKEN"] = "true"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-auth-", suffix=".sqlite")[1]
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


saju_main = _load_module("saju_birth_app", BACKEND / "saju-engine" / "app" / "main.py")
nabom_main = _load_module("nabom_auth_app", BACKEND / "nabom-api" / "app" / "main.py")
nabom_main.saju_transport = httpx.ASGITransport(app=saju_main.app)


def require(condition, message):
    if not condition:
        raise SystemExit(message)


async def run():
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        created = await client.post(
            "/api/v1/auth/signup",
            json={"email": "qa@nabom.test", "password": "password1", "nickname": "QA"},
        )
        require(created.status_code == 200, f"signup: {created.status_code} {created.text}")
        token = created.json()["token"]
        require(created.json()["user_id"].startswith("usr_"), created.json())
        me = await client.get("/api/v1/living/entries", headers={"Authorization": f"Bearer {token}"})
        require(me.status_code == 200, f"bearer entries: {me.status_code} {me.text}")

        bad_login = await client.post("/api/v1/auth/login", json={"email": "qa@nabom.test", "password": "wrongpass"})
        require(bad_login.status_code == 401, f"bad login: {bad_login.status_code}")
        login = await client.post("/api/v1/auth/login", json={"email": "qa@nabom.test", "password": "password1"})
        require(login.status_code == 200, login.text)

        recovery = await client.post("/api/v1/auth/recovery", json={"email": "qa@nabom.test"})
        require(recovery.status_code == 200 and recovery.json().get("recovery_token"), recovery.text)
        reset = await client.post(
            "/api/v1/auth/recovery/confirm",
            json={"email": "qa@nabom.test", "token": recovery.json()["recovery_token"], "new_password": "password2"},
        )
        require(reset.status_code == 200, reset.text)
        old = await client.post("/api/v1/auth/login", json={"email": "qa@nabom.test", "password": "password1"})
        require(old.status_code == 401, old.text)
        new = await client.post("/api/v1/auth/login", json={"email": "qa@nabom.test", "password": "password2"})
        require(new.status_code == 200, new.text)

        headers = {"Authorization": f"Bearer {new.json()['token']}"}
        future = await client.post(
            "/api/v1/living/profiles/initial",
            json={"birth_input": {"calendar": "solar", "date": "2099-01-01", "time_precision": "unknown"}},
            headers=headers,
        )
        require(future.status_code == 422, f"future birth: {future.status_code} {future.text}")

        bad_tz = await client.post(
            "/api/v1/living/profiles/initial",
            json={"birth_input": {"calendar": "solar", "date": "1992-03-01", "time_precision": "exact", "time": "07:20", "location": {"timezone": "Not/AZone"}}},
            headers=headers,
        )
        require(bad_tz.status_code == 422, f"bad tz: {bad_tz.status_code} {bad_tz.text}")

        unknown = await client.post(
            "/api/v1/living/profiles/initial",
            json={"birth_input": {"calendar": "solar", "date": "1992-03-01", "time": "", "time_precision": "unknown", "location": {"label": "Busan", "timezone": "Asia/Seoul"}}},
            headers=headers,
        )
        require(unknown.status_code == 200, f"unknown time: {unknown.status_code} {unknown.text[:200]}")
        unknown_profile = unknown.json()["profile"]
        require("four_pillars" not in unknown_profile, unknown_profile.keys())
        require("analysis" not in unknown_profile, unknown_profile.keys())
        require(any("시간을 몰라서" in item for item in unknown_profile["watch_patterns"]), unknown_profile["watch_patterns"])
        leaked = str(unknown.json())
        require("hour_pillar_omitted" not in leaked, leaked)
        require("noon_placeholder_for_missing_time" not in leaked, leaked)
        require("four_pillars" not in leaked, leaked)

        mixed_unknown = await client.post(
            "/api/v1/living/profiles/initial",
            json={"birth_input": {"calendar": "solar", "date": "1992-03-01", "time": "07:20", "time_precision": "unknown", "location": {"timezone": "Asia/Seoul"}}},
            headers=headers,
        )
        require(mixed_unknown.status_code == 422, f"unknown+time: {mixed_unknown.status_code} {mixed_unknown.text[:240]}")

        midnight = await client.post(
            "/api/v1/living/profiles/initial",
            json={"birth_input": {"calendar": "solar", "date": "1992-03-01", "time": "23:00-01:00", "time_precision": "approximate", "time_window": "around_midnight", "location": {"timezone": "Asia/Seoul"}}},
            headers=headers,
        )
        require(midnight.status_code == 200, f"around midnight: {midnight.status_code} {midnight.text[:240]}")
        require("four_pillars" not in str(midnight.json()), midnight.json())

        lunar = await client.post(
            "/api/v1/living/profiles/initial",
            json={"birth_input": {"calendar": "lunar", "date": "1992-03-01", "time": "07:20", "time_precision": "exact", "is_lunar_leap_month": None, "location": {"timezone": "Asia/Seoul"}}},
            headers=headers,
        )
        require(lunar.status_code == 200, f"lunar auto: {lunar.status_code} {lunar.text[:240]}")
        require("leap_month_auto_resolved" not in str(lunar.json()), lunar.json())
        require("calendar_conversion" not in str(lunar.json()), lunar.json())

        ambiguous = await client.post(
            "/api/v1/living/profiles/initial",
            json={"birth_input": {"calendar": "lunar", "date": "2001-04-15", "time": "10:00", "time_precision": "exact", "is_lunar_leap_month": None, "location": {"timezone": "Asia/Seoul"}}},
            headers=headers,
        )
        require(ambiguous.status_code == 422, f"ambiguous leap: {ambiguous.status_code} {ambiguous.text[:240]}")
        detail = ambiguous.json()["detail"]
        require(detail["code"] == "LUNAR_LEAP_MONTH_AMBIGUOUS", detail)
        require(len(detail.get("candidates") or []) == 2, detail)
        require("four_pillars" not in str(detail), detail)

        exported = await client.get("/api/v1/privacy/export", headers=headers)
        require(exported.status_code == 200, exported.text)
        require(len(exported.json()["profiles"]) >= 1, exported.json())
        require("four_pillars" not in str(exported.json()), exported.json())
        require("judgment_text" not in str(exported.json()), exported.json())


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
    print("accounts-birth-qa: PASS")
