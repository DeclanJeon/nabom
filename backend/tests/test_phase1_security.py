"""Phase 1 P0 privacy: rate limit, admin RBAC, legal docs, no journal leak."""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_AUTH_RATE_LIMIT"] = "5"
os.environ["NABOM_RATE_LIMIT_WINDOW"] = "60"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-sec-", suffix=".sqlite")[1]
os.environ["NABOM_ADMIN_USER_IDS"] = ""
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


nabom_main = _load_module("sec_nabom_main", BACKEND / "nabom-api" / "app" / "main.py")
rate_limit = _load_module("sec_rate_limit", BACKEND / "nabom-api" / "app" / "rate_limit.py")
app = nabom_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


async def run():
    rate_limit.reset()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        privacy = await client.get("/api/v1/legal/privacy")
        require(privacy.status_code == 200, privacy.text)
        require(privacy.json()["title"] == "개인정보처리방침", privacy.json())
        require(privacy.json()["sections"], privacy.json())
        terms = await client.get("/api/v1/legal/terms")
        require(terms.status_code == 200 and terms.json()["title"] == "이용약관", terms.text)

        created = await client.post(
            "/api/v1/auth/signup",
            json={"email": "member@nabom.test", "password": "password1", "nickname": "멤버"},
        )
        require(created.status_code == 200, created.text)
        member = created.json()
        member_headers = {"Authorization": f"Bearer {member['token']}"}

        denied = await client.get("/api/v1/admin/users", headers=member_headers)
        require(denied.status_code == 403, f"member admin: {denied.status_code} {denied.text}")
        require(denied.json()["detail"]["code"] == "ADMIN_REQUIRED", denied.json())

        admin = await client.post(
            "/api/v1/auth/signup",
            json={"email": "admin@nabom.test", "password": "password1", "nickname": "운영"},
        )
        require(admin.status_code == 200, admin.text)
        os.environ["NABOM_ADMIN_USER_IDS"] = admin.json()["user_id"]
        admin_headers = {"Authorization": f"Bearer {admin.json()['token']}"}

        await client.post(
            "/api/v1/living/entries",
            json={"date": "2026-08-12", "mood": 3, "energy": 3, "satisfaction": 3, "text": "비밀 일기 본문"},
            headers=member_headers,
        )
        await client.post(
            "/api/v1/living/journals",
            json={"date": "2026-08-12", "text": "관리자가 보면 안 되는 긴 일기입니다"},
            headers=member_headers,
        )

        listed = await client.get("/api/v1/admin/users", headers=admin_headers)
        require(listed.status_code == 200, listed.text)
        users = listed.json()["users"]
        require(any(item["email"] == "member@nabom.test" for item in users), users)
        leaked = str(listed.json())
        require("비밀 일기 본문" not in leaked, leaked)
        require("관리자가 보면 안 되는" not in leaked, leaked)
        member_row = next(item for item in users if item["email"] == "member@nabom.test")
        require(member_row["journal_count"] == 1, member_row)
        require("text" not in member_row, member_row)

        detail = await client.get(f"/api/v1/admin/users/{member['user_id']}", headers=admin_headers)
        require(detail.status_code == 200, detail.text)
        require("비밀 일기 본문" not in str(detail.json()), detail.json())

        for _ in range(5):
            bad = await client.post(
                "/api/v1/auth/login",
                json={"email": "brute@nabom.test", "password": "wrongpass"},
            )
            require(bad.status_code in {401, 429}, bad.status_code)
        limited = await client.post(
            "/api/v1/auth/login",
            json={"email": "brute@nabom.test", "password": "wrongpass"},
        )
        require(limited.status_code == 429, f"rate limit: {limited.status_code} {limited.text}")
        require(limited.json()["detail"]["code"] == "RATE_LIMITED", limited.json())


if __name__ == "__main__":
    asyncio.run(run())
    print("phase1-security: PASS")
