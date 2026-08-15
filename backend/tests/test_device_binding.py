"""Device-bound sessions: token unusable from another device."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-bind-", suffix=".sqlite")[1]
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


nabom_main = _load_module("bind_nabom_main", BACKEND / "nabom-api" / "app" / "main.py")
app = nabom_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        # signup bound to device A
        created = await client.post(
            "/api/v1/auth/signup",
            json={"email": "bind@nabom.test", "password": "password1", "nickname": "BIND"},
            headers={"X-Device-Id": "device-a"},
        )
        require(created.status_code == 200, f"signup: {created.status_code} {created.text}")
        token = created.json()["token"]

        # 1) same device works
        ok = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}", "X-Device-Id": "device-a"},
        )
        require(ok.status_code == 200, f"same device: {ok.status_code} {ok.text}")

        # 2) missing device header → 401 DEVICE_MISMATCH
        missing = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        require(missing.status_code == 401, f"missing device: {missing.status_code}")
        require(missing.json()["detail"]["code"] == "DEVICE_MISMATCH", missing.json())

        # 3) different device → 401 DEVICE_MISMATCH
        other = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}", "X-Device-Id": "device-b"},
        )
        require(other.status_code == 401, f"other device: {other.status_code}")
        require(other.json()["detail"]["code"] == "DEVICE_MISMATCH", other.json())

        # 4) malformed device id → 401 (not a valid bound match)
        bad = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}", "X-Device-Id": "../evil"},
        )
        require(bad.status_code == 401, f"bad device: {bad.status_code}")

        # 5) protected living route also bound (profiles/current → no profile yet 404 vs 401)
        route = await client.get(
            "/api/v1/living/profiles/current",
            headers={"Authorization": f"Bearer {token}", "X-Device-Id": "device-a"},
        )
        require(route.status_code == 404, f"bound living route: {route.status_code} {route.text[:80]}")
        route_other = await client.get(
            "/api/v1/living/profiles/current",
            headers={"Authorization": f"Bearer {token}", "X-Device-Id": "device-b"},
        )
        require(route_other.status_code == 401, f"unbound living route: {route_other.status_code}")

        # 6) unbound session (no X-Device-Id at login) stays compatible
        unbound = await client.post(
            "/api/v1/auth/signup",
            json={"email": "unbound@nabom.test", "password": "password1", "nickname": "UB"},
        )
        require(unbound.status_code == 200, f"unbound signup: {unbound.status_code}")
        ub_token = unbound.json()["token"]
        ub_ok = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {ub_token}"},
        )
        require(ub_ok.status_code == 200, f"unbound session: {ub_ok.status_code} {ub_ok.text}")

        # 7) revoke device then bound session rejected? Revoke removes registration,
        #    but the session is still bound by device_id equality — revoking must not
        #    leave the bound token usable from a *different* id, and same id remains
        #    technically usable until re-login (documented behavior).
        revoked = await client.delete(
            "/api/v1/auth/devices/device-a",
            headers={"Authorization": f"Bearer {token}", "X-Device-Id": "device-a"},
        )
        require(revoked.status_code == 200, f"revoke: {revoked.status_code}")
        # after revoke, registering a new device under same token still requires the bound id
        new_dev = await client.post(
            "/api/v1/auth/devices",
            json={"device_id": "device-c"},
            headers={"Authorization": f"Bearer {token}", "X-Device-Id": "device-a"},
        )
        require(new_dev.status_code == 200, f"new device via bound session: {new_dev.status_code} {new_dev.text[:80]}")
        new_dev_other = await client.post(
            "/api/v1/auth/devices",
            json={"device_id": "device-d"},
            headers={"Authorization": f"Bearer {token}", "X-Device-Id": "device-c"},
        )
        require(new_dev_other.status_code == 401, f"new device wrong id: {new_dev_other.status_code}")

    print("device-binding: PASS")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
