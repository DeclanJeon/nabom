"""Email/password accounts issued as opaque bearer tokens."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timezone

from domain import new_id

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AccountError(ValueError):
    """Typed account failure."""


def utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def normalize_email(email: str) -> str:
    value = str(email or "").strip().lower()
    if not EMAIL_RE.match(value):
        raise AccountError("invalid_email")
    return value


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if not isinstance(password, str) or len(password) < 8:
        raise AccountError("password_too_short")
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return salt, digest


def verify_password(password: str, salt: str, expected: str) -> bool:
    _, digest = hash_password(password, salt)
    return hmac.compare_digest(digest, expected)


def build_account(email: str, password: str, nickname: str = "") -> dict:
    normalized = normalize_email(email)
    salt, password_hash = hash_password(password)
    return {
        "user_id": new_id("usr"),
        "email": normalized,
        "nickname": str(nickname or normalized.split("@", 1)[0])[:40],
        "password_salt": salt,
        "password_hash": password_hash,
        "auth_providers": ["password"],
        "google_sub": None,
        "recovery_token": None,
        "verify_email_token": None,
        "email_verified": False,
        "created_at": utcnow(),
        "status": "active",
    }


def build_oauth_account(email: str, nickname: str, *, provider: str, subject: str) -> dict:
    normalized = normalize_email(email)
    return {
        "user_id": new_id("usr"),
        "email": normalized,
        "nickname": str(nickname or normalized.split("@", 1)[0])[:40],
        "password_salt": None,
        "password_hash": None,
        "auth_providers": [provider],
        "google_sub": subject if provider == "google" else None,
        "recovery_token": None,
        "verify_email_token": None,
        # OAuth 공급자(Google)는 이메일 소유권을 이미 검증했다.
        "email_verified": True if provider == "google" else False,
        "created_at": utcnow(),
        "status": "active",
    }


def has_password(account: dict) -> bool:
    return bool(account.get("password_salt") and account.get("password_hash"))


def issue_session(user_id: str, device_id: str | None = None) -> dict:
    token = secrets.token_urlsafe(32)
    session = {
        "token": token,
        "user_id": user_id,
        "created_at": utcnow(),
        "status": "active",
    }
    if device_id:
        session["device_id"] = normalize_device_id(device_id)
    return session


MAX_DEVICES = 5


def normalize_device_id(raw: str | None) -> str:
    """기기 ID는 클라이언트가 만든 안전한 토큰이다."""
    value = str(raw or "").strip()
    if not value or len(value) > 128:
        raise AccountError("invalid_device_id")
    if not all(ch.isalnum() or ch in "-_" for ch in value):
        raise AccountError("invalid_device_id")
    return value


def register_device(account: dict, device_id: str, *, label: str = "") -> dict:
    """기기를 계정에 등록한다. 최대 MAX_DEVICES개.

    이미 등록된 기기면 last_seen만 갱신한다. 새 기기가 한도를 넘으면
    DEVICE_LIMIT_REACHED를 나타내는 AccountError를 던진다.
    """
    normalized = normalize_device_id(device_id)
    devices = list(account.get("devices") or [])
    now = utcnow()
    for device in devices:
        if device.get("device_id") == normalized:
            device["last_seen"] = now
            if label:
                device["label"] = label
            account["devices"] = devices
            return device
    if len(devices) >= MAX_DEVICES:
        raise AccountError("device_limit_reached")
    device = {
        "device_id": normalized,
        "label": str(label or "알 수 없는 기기")[:40],
        "first_seen": now,
        "last_seen": now,
        "status": "active",
    }
    devices.append(device)
    account["devices"] = devices
    return device


def revoke_device(account: dict, device_id: str) -> bool:
    """기기 등록을 해제한다. 있으면 True, 없으면 False."""
    normalized = normalize_device_id(device_id)
    devices = [d for d in (account.get("devices") or []) if d.get("device_id") != normalized]
    if len(devices) == len(account.get("devices") or []):
        return False
    account["devices"] = devices
    return True


def public_session(account: dict, session: dict) -> dict:
    return {
        "user_id": account["user_id"],
        "email": account["email"],
        "nickname": account.get("nickname") or "",
        "token": session["token"],
        "token_type": "bearer",
    }
