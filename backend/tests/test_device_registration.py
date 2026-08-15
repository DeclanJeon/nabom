"""Device registration: max 5 per account, revoke, and limit enforcement."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-dev-", suffix=".sqlite")[1]
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


nabom_main = _load_module("dev_nabom_main", BACKEND / "nabom-api" / "app" / "main.py")
app = nabom_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        # 1) signup with device → devices list has 1
        created = await client.post(
            "/api/v1/auth/signup",
            json={"email": "dev@nabom.test", "password": "password1", "nickname": "DEV"},
            headers={"X-Device-Id": "dev-browser-001"},
        )
        require(created.status_code == 200, f"signup: {created.status_code} {created.text}")
        token = created.json()["token"]
        devices = created.json().get("devices") or []
        require(len(devices) == 1 and devices[0]["device_id"] == "dev-browser-001", devices)

        # 세션이 dev-browser-001에 바인딩됐으므로 이후 요청에도 같은 기기 헤더를 보낸다.
        headers = {"Authorization": f"Bearer {token}", "X-Device-Id": "dev-browser-001"}

        # 2) add up to 5 devices
        for i in range(2, 6):
            res = await client.post(
                "/api/v1/auth/devices",
                json={"device_id": f"dev-browser-{i:03d}", "label": f"기기 {i}"},
                headers=headers,
            )
            require(res.status_code == 200, f"register {i}: {res.status_code} {res.text}")

        listed = await client.get("/api/v1/auth/devices", headers=headers)
        require(listed.status_code == 200 and len(listed.json()["devices"]) == 5, listed.json())
        require(listed.json()["limit"] == 5, listed.json())

        # 3) 6th device → 403 DEVICE_LIMIT_REACHED
        sixth = await client.post(
            "/api/v1/auth/devices",
            json={"device_id": "dev-browser-006", "label": "6번째"},
            headers=headers,
        )
        require(sixth.status_code == 403, f"6th: {sixth.status_code} {sixth.text}")
        require(sixth.json()["detail"]["code"] == "DEVICE_LIMIT_REACHED", sixth.json())

        # 4) revoke one → can register again
        revoked = await client.delete("/api/v1/auth/devices/dev-browser-003", headers=headers)
        require(revoked.status_code == 200, f"revoke: {revoked.status_code} {revoked.text}")
        again = await client.post(
            "/api/v1/auth/devices",
            json={"device_id": "dev-browser-006", "label": "6번째"},
            headers=headers,
        )
        require(again.status_code == 200, f"after revoke: {again.status_code} {again.text}")

        # 5) revoke unknown → 404
        missing = await client.delete("/api/v1/auth/devices/dev-unknown", headers=headers)
        require(missing.status_code == 404, f"unknown revoke: {missing.status_code}")

        # 6) login re-registers known device without bumping count
        relogin = await client.post(
            "/api/v1/auth/login",
            json={"email": "dev@nabom.test", "password": "password1"},
            headers={"X-Device-Id": "dev-browser-001"},
        )
        require(relogin.status_code == 200, f"relogin: {relogin.status_code} {relogin.text}")
        after_relogin = relogin.json().get("devices") or []
        require(len(after_relogin) == 5, after_relogin)

        # 7) invalid device id → 422
        bad = await client.post(
            "/api/v1/auth/devices",
            json={"device_id": "../etc/passwd"},
            headers=headers,
        )
        require(bad.status_code == 422, f"bad device id: {bad.status_code} {bad.text}")

    print("device-registration: PASS")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
