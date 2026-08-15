"""Email verification flow + notification queue records (no real SMTP)."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_MAIL_ENABLED"] = "0"  # SMTP 없이 큐 레코드만 검증
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-ntf-", suffix=".sqlite")[1]
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


saju_main = _load_module("ntf_saju_main", BACKEND / "saju-engine" / "app" / "main.py")
iching_main = _load_module("ntf_iching_main", BACKEND / "iching-engine" / "app" / "main.py")
nabom_main = _load_module("ntf_nabom_main", BACKEND / "nabom-api" / "app" / "main.py")
nabom_main.saju_transport = httpx.ASGITransport(app=saju_main.app)
nabom_main.iching_transport = httpx.ASGITransport(app=iching_main.app)
app = nabom_main.app
accounts_routes = _load_module("ntf_accounts_routes", BACKEND / "nabom-api" / "app" / "accounts_routes.py")


def require(condition, message):
    if not condition:
        raise SystemExit(message)


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        # 1) signup → verify_email 토큰 발급 + 알림 큐 레코드
        created = await client.post(
            "/api/v1/auth/signup",
            json={"email": "verify@nabom.test", "password": "password1", "nickname": "VERIFY"},
            headers={"X-Device-Id": "verify-dev"},
        )
        require(created.status_code == 200, f"signup: {created.status_code} {created.text}")
        require(created.json().get("email_verified") is False, created.json())
        token = created.json()["token"]

        import store

        account = store.default_store.get("accounts", created.json()["user_id"])
        vt = account.get("verify_email_token")
        require(vt and len(vt) >= 20, "verify token issued")

        ntf = [
            n for n in store.default_store.list("notifications")
            if n.get("user_id") == created.json()["user_id"] and n.get("kind") == "verify_email"
        ]
        require(len(ntf) == 1 and ntf[0]["status"] == "queued", ntf)

        # 2) verify-email 엔드포인트 → email_verified=True
        verified = await client.get(f"/api/v1/auth/verify-email?token={vt}")
        require(verified.status_code == 200, f"verify: {verified.status_code} {verified.text}")
        require(verified.json()["status"] == "verified", verified.json())
        account = store.default_store.get("accounts", created.json()["user_id"])
        require(account.get("email_verified") is True, account)
        require(account.get("verify_email_token") is None, account)

        # 3) 재사용 시도 → 401
        replay = await client.get(f"/api/v1/auth/verify-email?token={vt}")
        require(replay.status_code == 401, f"replay: {replay.status_code}")

        # 4) 주간 회고 생성 → weekly_mirror_ready 알림 큐 레코드
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
            headers={"Authorization": f"Bearer {token}", "X-Device-Id": "verify-dev"},
        )
        require(profile.status_code == 200, f"profile: {profile.status_code}")
        for i in range(5):
            day = f"2026-07-{10 + i:02d}"
            entry = await client.post(
                "/api/v1/living/entries",
                json={"date": day, "timezone": "Asia/Seoul", "mood": 4, "energy": 4, "satisfaction": 4, "text": f"알림 테스트 {i}", "tags": ["growth"]},
                headers={"Authorization": f"Bearer {token}", "X-Device-Id": "verify-dev"},
            )
            require(entry.status_code == 200, f"entry {i}")
        reflection = await client.post(
            "/api/v1/living/reflections",
            json={"period_from": "2026-07-10", "period_to": "2026-07-14", "timezone": "Asia/Seoul"},
            headers={"Authorization": f"Bearer {token}", "X-Device-Id": "verify-dev"},
        )
        require(reflection.status_code == 200, f"reflection: {reflection.status_code} {reflection.text[:120]}")

        ntf2 = [
            n for n in store.default_store.list("notifications")
            if n.get("user_id") == created.json()["user_id"] and n.get("kind") == "weekly_mirror_ready"
        ]
        require(len(ntf2) == 1, ntf2)
        require(ntf2[0]["status"] == "queued", ntf2[0])  # MAIL_ENABLED=0 → queued 유지

    print("notifications: PASS")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
