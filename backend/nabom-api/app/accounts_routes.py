"""Signup, login, and recovery routes."""

from __future__ import annotations

import os
import secrets
import threading

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from urllib.parse import urlencode

import accounts
import google_oauth
import store
import auth
import rate_limit

router = APIRouter()
_account_lock = threading.Lock()


def _invalid(message: str) -> HTTPException:
    return HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": message, "retryable": False})


def _unauthorized(message: str = "invalid credentials") -> HTTPException:
    return HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED", "message": message, "retryable": False})


class SignupRequest(BaseModel):
    email: str
    password: str
    nickname: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class RecoveryRequest(BaseModel):
    email: str


class RecoveryConfirmRequest(BaseModel):
    email: str
    token: str
    new_password: str


def _account_by_email(email: str) -> dict | None:
    index = store.default_store.get("accounts_by_email", email)
    if not index or not index.get("user_id"):
        return None
    return store.default_store.get("accounts", index["user_id"])


@router.post("/api/v1/auth/signup")
def signup(payload: SignupRequest, request: Request):
    rate_limit.enforce_auth(request, payload.email)
    device_id = _device_header(request)
    with _account_lock:
        try:
            account = accounts.build_account(payload.email, payload.password, payload.nickname)
        except accounts.AccountError as exc:
            raise _invalid(str(exc)) from exc
        if _account_by_email(account["email"]):
            raise _invalid("email_already_registered")
        # 이메일 확인 토큰 발급 + 발송 시도 (실패해도 가입은 성공)
        account["verify_email_token"] = secrets.token_urlsafe(24)
        account["email_verified"] = False
        store.default_store.set("accounts", account["user_id"], account)
        store.default_store.set("accounts_by_email", account["email"], {"user_id": account["user_id"]})
        account = _register_device_for_account(account, device_id)
        session = accounts.issue_session(account["user_id"], device_id)
        store.default_store.set("sessions", session["token"], session)
        _queue_notification(
            account,
            kind="verify_email",
            payload={"token": account["verify_email_token"]},
            email_subject="[나봄] 이메일 확인",
        )
        session_payload = accounts.public_session(account, session)
        session_payload["devices"] = [
            {k: d.get(k) for k in ("device_id", "label", "first_seen", "last_seen", "status")}
            for d in (account.get("devices") or [])
        ]
        session_payload["email_verified"] = False
        return session_payload


@router.post("/api/v1/auth/login")
def login(payload: LoginRequest, request: Request):
    rate_limit.enforce_auth(request, payload.email)
    device_id = _device_header(request)
    try:
        email = accounts.normalize_email(payload.email)
    except accounts.AccountError as exc:
        raise _invalid(str(exc)) from exc
    account = _account_by_email(email)
    if not account or account.get("status") == "deleted":
        raise _unauthorized()
    if not accounts.has_password(account):
        raise _unauthorized("google_account_requires_oauth")
    if not accounts.verify_password(payload.password, account["password_salt"], account["password_hash"]):
        raise _unauthorized()
    return _session_for(account, device_id)


@router.post("/api/v1/auth/recovery")
def request_recovery(payload: RecoveryRequest, request: Request):
    rate_limit.enforce_auth(request, payload.email)
    try:
        email = accounts.normalize_email(payload.email)
    except accounts.AccountError as exc:
        raise _invalid(str(exc)) from exc
    account = _account_by_email(email)
    if not account:
        return {"status": "accepted"}
    token = secrets.token_urlsafe(24)
    account["recovery_token"] = token
    store.default_store.set("accounts", account["user_id"], account)
    mailed = False
    try:
        import mailer

        mailer.send_recovery_mail(email, token)
        mailed = True
    except Exception:  # noqa: BLE001
        mailed = False
    payload_out = {"status": "accepted", "mailed": mailed}
    if os.environ.get("NABOM_RECOVERY_RETURN_TOKEN", "").strip().lower() in {"1", "true", "yes"}:
        payload_out["recovery_token"] = token
    return payload_out

@router.post("/api/v1/auth/recovery/confirm")
def confirm_recovery(payload: RecoveryConfirmRequest, request: Request):
    rate_limit.enforce_auth(request, payload.email)
    with _account_lock:
        try:
            email = accounts.normalize_email(payload.email)
            salt, digest = accounts.hash_password(payload.new_password)
        except accounts.AccountError as exc:
            raise _invalid(str(exc)) from exc
        account = _account_by_email(email)
        if not account or not account.get("recovery_token") or account["recovery_token"] != payload.token:
            raise _unauthorized("invalid recovery token")
        account["password_salt"] = salt
        account["password_hash"] = digest
        account["recovery_token"] = None
        providers = list(account.get("auth_providers") or [])
        if "password" not in providers:
            providers.append("password")
        account["auth_providers"] = providers
        store.default_store.set("accounts", account["user_id"], account)
        session = accounts.issue_session(account["user_id"])
        store.default_store.set("sessions", session["token"], session)
        return accounts.public_session(account, session)

@router.get("/api/v1/auth/me")
def current_session(user_id: str = Depends(auth.get_authenticated_identity)):
    account = store.default_store.get("accounts", user_id)
    if not account or account.get("status") == "deleted":
        raise _unauthorized("session expired")
    return {
        "user_id": account["user_id"],
        "email": account["email"],
        "nickname": account.get("nickname") or "",
    }

def _oauth_error(exc: google_oauth.GoogleOAuthError) -> HTTPException:
    status = 503 if exc.code in {"GOOGLE_AUTH_NOT_CONFIGURED", "GOOGLE_UNAVAILABLE"} else 401
    return HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message, "retryable": False})


def _account_by_google_sub(subject: str) -> dict | None:
    index = store.default_store.get("accounts_by_google_sub", subject)
    if not index or not index.get("user_id"):
        return None
    return store.default_store.get("accounts", index["user_id"])


def _attach_google(account: dict, subject: str) -> dict:
    providers = list(account.get("auth_providers") or [])
    if "google" not in providers:
        providers.append("google")
    account["auth_providers"] = providers
    account["google_sub"] = subject
    store.default_store.set("accounts", account["user_id"], account)
    store.default_store.set("accounts_by_google_sub", subject, {"user_id": account["user_id"]})
    return account


def _device_header(request: Request) -> str | None:
    value = request.headers.get("x-device-id") or request.headers.get("X-Device-Id")
    return value.strip() if value else None


def _queue_notification(account: dict, *, kind: str, payload: dict, email_subject: str = "") -> None:
    """알림 큐에 레코드 추가 + 메일 발송 시도(활성화 시). 실패는 조용히 무시한다."""
    import mailer

    notification = {
        "notification_id": f"nt_{secrets.token_hex(6)}",
        "user_id": account["user_id"],
        "kind": kind,
        "channel": "email",
        "payload": payload,
        "status": "queued",
        "created_at": accounts.utcnow(),
    }
    store.default_store.set("notifications", notification["notification_id"], notification)
    try:
        if kind == "verify_email":
            mailer.send_verify_email_mail(account["email"], payload.get("token", ""))
        elif kind == "weekly_mirror_ready":
            mailer.send_weekly_mirror_ready_mail(account["email"], account.get("nickname") or "")
        elif kind == "password_reset":
            mailer.send_recovery_mail(account["email"], payload.get("token", ""))
        notification["status"] = "sent"
        store.default_store.set("notifications", notification["notification_id"], notification)
    except Exception:  # noqa: BLE001
        notification["status"] = "queued"  # 메일 미발송 환경에서도 큐 레코드는 유지
        store.default_store.set("notifications", notification["notification_id"], notification)


@router.get("/api/v1/auth/verify-email")
def verify_email(token: str, request: Request):
    """이메일 확인 토큰으로 계정을 검증한다."""
    rate_limit.enforce_auth(request, "verify_email")
    with _account_lock:
        for account in store.default_store.list("accounts"):
            if account.get("verify_email_token") == token and account.get("status") != "deleted":
                account["email_verified"] = True
                account["verify_email_token"] = None
                store.default_store.set("accounts", account["user_id"], account)
                return {"status": "verified", "email": account["email"]}
        raise _unauthorized("invalid or expired verification token")


def _register_device_for_account(account: dict, device_id: str | None, label: str = "") -> dict:
    """기기를 등록하고 계정을 저장한다. 한도 초과 시 403 DEVICE_LIMIT_REACHED."""
    if not device_id:
        return account
    try:
        accounts.register_device(account, device_id, label=label)
    except accounts.AccountError as exc:
        if getattr(exc, "args", ()) and exc.args and exc.args[0] == "device_limit_reached":
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "DEVICE_LIMIT_REACHED",
                    "message": f"등록 가능한 기기는 계정당 {accounts.MAX_DEVICES}대까지예요. 설정에서 기기 관리를 확인해주세요.",
                    "retryable": False,
                },
            ) from exc
        raise _invalid(str(exc)) from exc
    store.default_store.set("accounts", account["user_id"], account)
    return account


def _session_for(account: dict, device_id: str | None = None) -> dict:
    if device_id:
        account = _register_device_for_account(account, device_id)
    session = accounts.issue_session(account["user_id"], device_id)
    store.default_store.set("sessions", session["token"], session)
    session_payload = accounts.public_session(account, session)
    session_payload["devices"] = [
        {k: d.get(k) for k in ("device_id", "label", "first_seen", "last_seen", "status")}
        for d in (account.get("devices") or [])
    ]
    return session_payload


def login_or_create_google(identity: dict, device_id: str | None = None) -> dict:
    with _account_lock:
        account = _account_by_google_sub(identity["subject"]) or _account_by_email(identity["email"])
        if account and account.get("status") == "deleted":
            raise _unauthorized("account deleted")
        if account:
            if account.get("google_sub") and account["google_sub"] != identity["subject"]:
                raise _unauthorized("google subject mismatch")
            return _session_for(_attach_google(account, identity["subject"]), device_id)
        account = accounts.build_oauth_account(
            identity["email"],
            identity["nickname"],
            provider="google",
            subject=identity["subject"],
        )
        store.default_store.set("accounts", account["user_id"], account)
        store.default_store.set("accounts_by_email", account["email"], {"user_id": account["user_id"]})
        store.default_store.set("accounts_by_google_sub", identity["subject"], {"user_id": account["user_id"]})
        return _session_for(account, device_id)


class GoogleTokenRequest(BaseModel):
    id_token: str


@router.get("/api/v1/auth/google/start")
def start_google(request: Request, device_id: str | None = None):
    rate_limit.enforce_auth(request, "google")
    if not google_oauth.code_flow_ready():
        raise HTTPException(
            status_code=503,
            detail={"code": "GOOGLE_AUTH_NOT_CONFIGURED", "message": "Google 로그인이 설정되지 않았습니다.", "retryable": False},
        )
    state = secrets.token_urlsafe(24)
    try:
        normalized = accounts.normalize_device_id(device_id) if device_id else None
    except accounts.AccountError as exc:
        raise _invalid(str(exc)) from exc
    store.default_store.set(
        "oauth_states",
        state,
        {"provider": "google", "created_at": accounts.utcnow(), "status": "pending", "device_id": normalized},
    )
    return {"authorization_url": google_oauth.authorization_url(state), "state": state}


@router.get("/api/v1/auth/google/callback")
@router.get("/api/v1/auth/callback/google")
def google_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    app_url = google_oauth.public_app_url()
    if error or not code or not state:
        return RedirectResponse(f"{app_url}/?{urlencode({'oauth': 'error', 'code': error or 'GOOGLE_DENIED'})}")
    pending = store.default_store.get("oauth_states", state)
    if not pending or pending.get("provider") != "google" or pending.get("status") != "pending":
        return RedirectResponse(f"{app_url}/?{urlencode({'oauth': 'error', 'code': 'OAUTH_STATE_INVALID'})}")
    if google_oauth.expired(pending.get("created_at", ""), 600):
        pending["status"] = "expired"
        store.default_store.set("oauth_states", state, pending)
        return RedirectResponse(f"{app_url}/?{urlencode({'oauth': 'error', 'code': 'OAUTH_STATE_EXPIRED'})}")
    try:
        identity = google_oauth.exchange_code(code)
        session = login_or_create_google(identity, pending.get("device_id"))
    except google_oauth.GoogleOAuthError as exc:
        pending["status"] = "failed"
        store.default_store.set("oauth_states", state, pending)
        return RedirectResponse(f"{app_url}/?{urlencode({'oauth': 'error', 'code': exc.code})}")
    except HTTPException as exc:
        pending["status"] = "failed"
        store.default_store.set("oauth_states", state, pending)
        code = exc.detail.get("code") if isinstance(exc.detail, dict) else "DEVICE_LIMIT_REACHED"
        return RedirectResponse(f"{app_url}/?{urlencode({'oauth': 'error', 'code': code})}")
    pending["status"] = "used"
    store.default_store.set("oauth_states", state, pending)
    return RedirectResponse(f"{app_url}/?{urlencode({'oauth': 'ok', 'token': session['token']})}")


@router.post("/api/v1/auth/google")
def google_id_token_login(payload: GoogleTokenRequest, request: Request):
    rate_limit.enforce_auth(request, "google")
    try:
        identity = google_oauth.verify_id_token(payload.id_token)
        return login_or_create_google(identity, _device_header(request))
    except google_oauth.GoogleOAuthError as exc:
        raise _oauth_error(exc) from exc


@router.get("/api/v1/auth/devices")
def list_devices(user_id: str = Depends(auth.get_authenticated_identity)):
    account = store.default_store.get("accounts", user_id)
    if not account or account.get("status") == "deleted":
        raise _unauthorized("session expired")
    devices = account.get("devices") or []
    return {
        "devices": [
            {k: d.get(k) for k in ("device_id", "label", "first_seen", "last_seen", "status")}
            for d in devices
        ],
        "limit": accounts.MAX_DEVICES,
    }


class DeviceRegisterRequest(BaseModel):
    device_id: str
    label: str = ""


@router.post("/api/v1/auth/devices")
def register_device_route(
    payload: DeviceRegisterRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    with _account_lock:
        account = store.default_store.get("accounts", user_id)
        if not account or account.get("status") == "deleted":
            raise _unauthorized("session expired")
        account = _register_device_for_account(account, payload.device_id, label=payload.label)
        device = next((d for d in (account.get("devices") or []) if d.get("device_id") == payload.device_id), None)
        return {"device": device}


@router.delete("/api/v1/auth/devices/{device_id}")
def revoke_device_route(
    device_id: str,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    with _account_lock:
        account = store.default_store.get("accounts", user_id)
        if not account or account.get("status") == "deleted":
            raise _unauthorized("session expired")
        if not accounts.revoke_device(account, device_id):
            raise HTTPException(status_code=404, detail={"code": "DEVICE_NOT_FOUND", "message": "기기를 찾을 수 없어요.", "retryable": False})
        store.default_store.set("accounts", account["user_id"], account)
        return {"status": "revoked", "device_id": device_id}
