"""Google OAuth for NABOM accounts.

Uses GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET from the operator environment.
Never invents a local Google fallback.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO = "https://oauth2.googleapis.com/tokeninfo"


class GoogleOAuthError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def client_id() -> str:
    return (os.environ.get("NABOM_GOOGLE_CLIENT_ID") or os.environ.get("GOOGLE_CLIENT_ID") or "").strip()


def client_secret() -> str:
    return (os.environ.get("NABOM_GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()


def public_api_url() -> str:
    return (os.environ.get("NABOM_PUBLIC_API_URL") or "http://localhost:8080").rstrip("/")


def public_app_url() -> str:
    return (os.environ.get("NABOM_PUBLIC_APP_URL") or "http://localhost:3000").rstrip("/")


def redirect_uri() -> str:
    return (os.environ.get("NABOM_GOOGLE_REDIRECT_URI") or f"{public_api_url()}/api/v1/auth/google/callback").strip()


def configured() -> bool:
    return bool(client_id())


def code_flow_ready() -> bool:
    return bool(client_id() and client_secret())


def authorization_url(state: str) -> str:
    if not configured():
        raise GoogleOAuthError("GOOGLE_AUTH_NOT_CONFIGURED", "Google 로그인이 설정되지 않았습니다.")
    params = {
        "client_id": client_id(),
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "include_granted_scopes": "true",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH}?{urllib.parse.urlencode(params)}"


def _http_json(url: str, data: dict | None = None, timeout: int = 10) -> dict:
    body = None if data is None else urllib.parse.urlencode(data).encode()
    request = urllib.request.Request(url, data=body, method="GET" if data is None else "POST")
    if data is not None:
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() if exc.fp else ""
        raise GoogleOAuthError("GOOGLE_TOKEN_INVALID", "Google 인증에 실패했습니다.") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GoogleOAuthError("GOOGLE_UNAVAILABLE", "Google에 연결할 수 없습니다.") from exc
    if not isinstance(payload, dict):
        raise GoogleOAuthError("GOOGLE_TOKEN_INVALID", "Google 인증에 실패했습니다.")
    return payload


def exchange_code(code: str) -> dict:
    if not code_flow_ready():
        raise GoogleOAuthError("GOOGLE_AUTH_NOT_CONFIGURED", "Google 로그인이 설정되지 않았습니다.")
    payload = _http_json(
        GOOGLE_TOKEN,
        {
            "code": code,
            "client_id": client_id(),
            "client_secret": client_secret(),
            "redirect_uri": redirect_uri(),
            "grant_type": "authorization_code",
        },
    )
    id_token = str(payload.get("id_token") or "")
    if not id_token:
        raise GoogleOAuthError("GOOGLE_TOKEN_INVALID", "Google 인증에 실패했습니다.")
    return verify_id_token(id_token)


def verify_id_token(id_token: str) -> dict:
    if not configured():
        raise GoogleOAuthError("GOOGLE_AUTH_NOT_CONFIGURED", "Google 로그인이 설정되지 않았습니다.")
    if not id_token or not isinstance(id_token, str):
        raise GoogleOAuthError("GOOGLE_TOKEN_INVALID", "Google 인증에 실패했습니다.")
    payload = _http_json(f"{GOOGLE_TOKENINFO}?{urllib.parse.urlencode({'id_token': id_token})}")
    audience = str(payload.get("aud") or "")
    if audience != client_id():
        raise GoogleOAuthError("GOOGLE_AUDIENCE_MISMATCH", "Google 클라이언트가 일치하지 않습니다.")
    email = str(payload.get("email") or "").strip().lower()
    subject = str(payload.get("sub") or "").strip()
    verified = str(payload.get("email_verified") or "").lower() in {"true", "1"}
    if not email or not subject or not verified:
        raise GoogleOAuthError("GOOGLE_EMAIL_UNVERIFIED", "인증된 Google 이메일이 필요합니다.")
    nickname = str(payload.get("name") or payload.get("given_name") or email.split("@", 1)[0])[:40]
    return {"email": email, "subject": subject, "nickname": nickname}


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def expired(iso: str, seconds: int) -> bool:
    try:
        created = datetime.fromisoformat(iso)
    except ValueError:
        return True
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return utcnow() - created > timedelta(seconds=seconds)
