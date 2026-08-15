"""NFC/QR resolve, claim, revoke, and replace routes."""

from __future__ import annotations

import threading

from fastapi import APIRouter, Depends, Header, HTTPException, Query

import auth
import nfc
import store

router = APIRouter()
_nfc_lock = threading.Lock()


def _invalid(message: str) -> HTTPException:
    return HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": message, "retryable": False})


def _missing() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "token not found", "retryable": False})


def _forbidden(message: str) -> HTTPException:
    return HTTPException(status_code=403, detail={"code": "CONSENT_REQUIRED", "message": message, "retryable": False})


def _load(token: str) -> dict | None:
    return store.default_store.get("nfc_tokens", token)


def _save(record: dict) -> None:
    store.default_store.set("nfc_tokens", record["token"], record)


def _map_error(exc: nfc.NfcError) -> HTTPException:
    message = str(exc)
    if message == "token_not_found":
        return _missing()
    if message in {"token_claimed_by_other", "token_not_owned"}:
        return _forbidden("token is linked to another account")
    return _invalid(message)


@router.post("/api/v1/nfc/tokens")
def issue_nfc_token(user_id: str = Depends(auth.get_authenticated_identity), source: str = Query(default="nfc")):
    try:
        record = nfc.issue_token(source)
    except nfc.NfcError as exc:
        raise _map_error(exc) from exc
    _save(record)
    return nfc.public_token(record, user_id)


def optional_identity(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> str | None:
    try:
        return auth.get_authenticated_identity(authorization=authorization, x_user_id=x_user_id)
    except HTTPException as exc:
        if exc.status_code == 401:
            return None
        raise


@router.get("/api/v1/nfc/resolve/{token}")
def resolve_nfc_token(
    token: str,
    source: str = Query(default="nfc"),
    user_id: str | None = Depends(optional_identity),
):
    try:
        return nfc.resolve_token(_load(token), user_id, source)
    except nfc.NfcError as exc:
        raise _map_error(exc) from exc

@router.post("/api/v1/nfc/tokens/{token}/claim")
def claim_nfc_token(token: str, user_id: str = Depends(auth.get_authenticated_identity)):
    with _nfc_lock:
        record = _load(token)
        if not record:
            raise _missing()
        try:
            claimed = nfc.claim_token(record, user_id)
        except nfc.NfcError as exc:
            raise _map_error(exc) from exc
        _save(claimed)
        return nfc.public_token(claimed, user_id)


@router.post("/api/v1/nfc/tokens/{token}/revoke")
def revoke_nfc_token(token: str, user_id: str = Depends(auth.get_authenticated_identity)):
    with _nfc_lock:
        record = _load(token)
        if not record:
            raise _missing()
        try:
            revoked = nfc.revoke_token(record, user_id)
        except nfc.NfcError as exc:
            raise _map_error(exc) from exc
        _save(revoked)
        return nfc.public_token(revoked, user_id)


@router.post("/api/v1/nfc/tokens/{token}/replace")
def replace_nfc_token(token: str, user_id: str = Depends(auth.get_authenticated_identity), source: str = Query(default="nfc")):
    with _nfc_lock:
        record = _load(token)
        if not record:
            raise _missing()
        try:
            old, new = nfc.replace_token(record, user_id, source)
        except nfc.NfcError as exc:
            raise _map_error(exc) from exc
        _save(old)
        _save(new)
        return {"revoked": nfc.public_token(old, user_id), "replacement": nfc.public_token(new, user_id)}
