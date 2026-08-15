"""Authentication boundary for relationship and insight-group routes.

The prototype deliberately has no implicit user identity. Production-like mode
accepts only configured bearer tokens; the legacy X-User-Id header is available
only when an operator explicitly enables development authentication.
"""

from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException


def _authentication_required() -> None:
    raise HTTPException(
        status_code=401,
        detail={
            "code": "AUTHENTICATION_REQUIRED",
            "message": "authenticated identity required",
            "retryable": False,
        },
    )


def _device_mismatch() -> None:
    raise HTTPException(
        status_code=401,
        detail={
            "code": "DEVICE_MISMATCH",
            "message": "이 기기에서 사용할 수 있는 세션이 아니에요. 다시 로그인해주세요.",
            "retryable": False,
        },
    )


def _development_mode() -> bool:
    mode = os.getenv("NABOM_AUTH_MODE", "").strip().lower()
    enabled = os.getenv("NABOM_DEV_AUTH", "").strip().lower()
    return mode in {"development", "dev", "test"} or enabled in {"1", "true", "yes"}


def _configured_identity(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    if not token:
        return None

    configured: list[tuple[str, str]] = []
    for item in os.getenv("NABOM_AUTH_TOKENS", "").split(","):
        item = item.strip()
        if not item:
            continue
        separator = "=" if "=" in item else ":"
        token_value, separator, identity = item.partition(separator)
        if separator and token_value.strip() and identity.strip():
            configured.append((token_value.strip(), identity.strip()))

    single_token = os.getenv("NABOM_AUTH_TOKEN", "").strip()
    single_identity = os.getenv("NABOM_AUTH_USER_ID", "").strip()
    if single_token and single_identity:
        configured.append((single_token, single_identity))

    for expected_token, identity in configured:
        if secrets.compare_digest(token, expected_token):
            return identity
    return None


def _session_identity(token: str, x_device_id: str | None) -> str | None:
    """세션 토큰으로 사용자를 확인하고, 세션이 기기에 바인딩되어 있으면 헤더와 대조한다.

    - 세션에 device_id가 없으면(레거시/비바인딩 발급) 그대로 허용한다.
    - 세션에 device_id가 있으면 헤더의 X-Device-Id가 반드시 일치해야 한다.
      헤더 누락 또는 불일치 → DEVICE_MISMATCH.
    """
    import store

    session = store.default_store.get("sessions", token)
    if not session or session.get("status") != "active" or not session.get("user_id"):
        return None
    bound_device = session.get("device_id")
    if bound_device:
        header_device = (x_device_id or "").strip()
        if not header_device:
            _device_mismatch()
        try:
            import accounts

            normalized = accounts.normalize_device_id(header_device)
        except Exception:  # noqa: BLE001
            _device_mismatch()
        if normalized != bound_device:
            _device_mismatch()
    return session["user_id"]


def get_authenticated_identity(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_device_id: str | None = Header(default=None),
) -> str:
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        if token:
            identity = _session_identity(token, x_device_id)
            if identity:
                return identity
        identity = _configured_identity(authorization)
        if identity:
            return identity

    if _development_mode():
        identity = (x_user_id or "").strip()
        if identity:
            return identity

    identity = _configured_identity(authorization)
    if identity:
        return identity
    _authentication_required()
    raise AssertionError("unreachable")
