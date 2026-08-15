"""Google OAuth start/callback/id-token login without hitting Google."""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_STORE_PATH"] = tempfile.mkstemp(prefix="nabom-oauth-", suffix=".sqlite")[1]
os.environ["NABOM_GOOGLE_CLIENT_ID"] = "nabom-google-client.apps.googleusercontent.com"
os.environ["NABOM_GOOGLE_CLIENT_SECRET"] = "nabom-google-secret"
os.environ["NABOM_PUBLIC_APP_URL"] = "http://localhost:3000"
os.environ["NABOM_PUBLIC_API_URL"] = "http://nabom"
os.environ["NABOM_AUTH_RATE_LIMIT"] = "50"
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


nabom_main = _load_module("oauth_nabom_main", BACKEND / "nabom-api" / "app" / "main.py")
import accounts_routes  # noqa: E402
import google_oauth  # noqa: E402

app = nabom_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom", follow_redirects=False) as client:
        started = await client.get("/api/v1/auth/google/start")
        require(started.status_code == 200, f"start: {started.status_code} {started.text}")
        url = started.json()["authorization_url"]
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        require(parsed.netloc == "accounts.google.com", url)
        require(query["client_id"] == ["nabom-google-client.apps.googleusercontent.com"], query)
        require(query["redirect_uri"] == ["http://nabom/api/v1/auth/google/callback"], query)
        require("openid" in query["scope"][0], query)
        state = started.json()["state"]
        require(state and state == query["state"][0], started.json())

        denied = await client.get("/api/v1/auth/google/callback", params={"error": "access_denied"})
        require(denied.status_code in {302, 307}, denied.status_code)
        require("oauth=error" in denied.headers["location"], denied.headers["location"])

        bad_state = await client.get("/api/v1/auth/google/callback", params={"code": "x", "state": "nope"})
        require("OAUTH_STATE_INVALID" in bad_state.headers["location"], bad_state.headers["location"])

        def fake_exchange(code: str):
            require(code == "good-code", code)
            return {"email": "oauth@nabom.test", "subject": "sub-1", "nickname": "봄이"}

        accounts_routes.google_oauth.exchange_code = fake_exchange
        created = await client.get("/api/v1/auth/google/callback", params={"code": "good-code", "state": state})
        require(created.status_code in {302, 307}, created.text)
        location = created.headers["location"]
        require(location.startswith("http://localhost:3000/?"), location)
        loc_q = parse_qs(urlparse(location).query)
        require(loc_q["oauth"] == ["ok"], loc_q)
        token = loc_q["token"][0]
        me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        require(me.status_code == 200, me.text)
        require(me.json()["email"] == "oauth@nabom.test", me.json())
        require(me.json()["nickname"] == "봄이", me.json())

        replay = await client.get("/api/v1/auth/google/callback", params={"code": "good-code", "state": state})
        require("OAUTH_STATE_INVALID" in replay.headers["location"], replay.headers["location"])

        password = await client.post(
            "/api/v1/auth/login",
            json={"email": "oauth@nabom.test", "password": "password1"},
        )
        require(password.status_code == 401, password.text)

        def fake_verify(id_token: str):
            require(id_token == "id-token-2", id_token)
            return {"email": "oauth@nabom.test", "subject": "sub-1", "nickname": "봄이"}

        accounts_routes.google_oauth.verify_id_token = fake_verify
        again = await client.post("/api/v1/auth/google", json={"id_token": "id-token-2"})
        require(again.status_code == 200, again.text)
        require(again.json()["email"] == "oauth@nabom.test", again.json())
        require(again.json()["user_id"] == me.json()["user_id"], again.json())

        signed = await client.post(
            "/api/v1/auth/signup",
            json={"email": "linked@nabom.test", "password": "password1", "nickname": "연결"},
        )
        require(signed.status_code == 200, signed.text)
        user_id = signed.json()["user_id"]

        def fake_verify_link(_id_token: str):
            return {"email": "linked@nabom.test", "subject": "sub-link", "nickname": "연결"}

        accounts_routes.google_oauth.verify_id_token = fake_verify_link
        linked = await client.post("/api/v1/auth/google", json={"id_token": "link"})
        require(linked.status_code == 200, linked.text)
        require(linked.json()["user_id"] == user_id, linked.json())

        still = await client.post(
            "/api/v1/auth/login",
            json={"email": "linked@nabom.test", "password": "password1"},
        )
        require(still.status_code == 200, still.text)

        def boom(_id_token: str):
            raise google_oauth.GoogleOAuthError("GOOGLE_TOKEN_INVALID", "bad")

        accounts_routes.google_oauth.verify_id_token = boom
        bad_token = await client.post("/api/v1/auth/google", json={"id_token": "bad"})
        require(bad_token.status_code == 401, bad_token.text)
        require(bad_token.json()["detail"]["code"] == "GOOGLE_TOKEN_INVALID", bad_token.json())


if __name__ == "__main__":
    asyncio.run(run())
    print("google-oauth: PASS")
