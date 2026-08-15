"""Opaque NFC/QR token domain.

Tokens never embed user IDs. Resolve reports only unlinked, owner,
other_account, or revoked. Replacement issues a new token and revokes the old
one without deleting account data.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

TOKEN_SOURCES = {"nfc", "qr"}
TOKEN_STATES = {"unlinked", "claimed", "revoked"}


class NfcError(ValueError):
    """Typed NFC token failure."""


def new_token() -> str:
    return secrets.token_urlsafe(24)


def utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def issue_token(source: str = "nfc") -> dict:
    if source not in TOKEN_SOURCES:
        raise NfcError("source must be nfc or qr")
    token = new_token()
    return {
        "token": token,
        "source": source,
        "status": "unlinked",
        "owner_user_id": None,
        "created_at": utcnow(),
        "claimed_at": None,
        "revoked_at": None,
        "replaced_by": None,
        "replaces": None,
    }


def resolve_token(record: dict | None, requester: str | None, source: str = "nfc") -> dict:
    if source not in TOKEN_SOURCES:
        raise NfcError("source must be nfc or qr")
    if not record:
        raise NfcError("token_not_found")
    status = record.get("status")
    owner = record.get("owner_user_id")
    if status == "revoked":
        visibility = "revoked"
    elif status == "unlinked" or not owner:
        visibility = "unlinked"
    elif requester and owner == requester:
        visibility = "owner"
    elif requester:
        visibility = "other_account"
    else:
        visibility = "login_required"
    return {
        "token": record["token"],
        "source": source,
        "status": visibility,
        "destination": _destination(visibility),
        "analysis_result_included": False,
    }

def _destination(visibility: str) -> str:
    if visibility == "owner":
        return "/today"
    if visibility == "login_required":
        return "/login"
    return "/k"

def claim_token(record: dict, user_id: str) -> dict:
    if record.get("status") == "revoked":
        raise NfcError("token_revoked")
    owner = record.get("owner_user_id")
    if owner and owner != user_id:
        raise NfcError("token_claimed_by_other")
    if owner == user_id:
        return record
    record["status"] = "claimed"
    record["owner_user_id"] = user_id
    record["claimed_at"] = utcnow()
    return record


def revoke_token(record: dict, user_id: str) -> dict:
    owner = record.get("owner_user_id")
    if owner and owner != user_id:
        raise NfcError("token_not_owned")
    if not owner:
        raise NfcError("token_unlinked")
    if record.get("status") == "revoked":
        return record
    record["status"] = "revoked"
    record["revoked_at"] = utcnow()
    return record


def replace_token(record: dict, user_id: str, source: str = "nfc") -> tuple[dict, dict]:
    revoke_token(record, user_id)
    replacement = issue_token(source=source)
    replacement["status"] = "claimed"
    replacement["owner_user_id"] = user_id
    replacement["claimed_at"] = utcnow()
    replacement["replaces"] = record["token"]
    record["replaced_by"] = replacement["token"]
    return record, replacement


def public_token(record: dict, requester: str) -> dict:
    owner = record.get("owner_user_id")
    return {
        "token": record["token"],
        "source": record.get("source", "nfc"),
        "status": record.get("status"),
        "owned_by_requester": owner == requester,
        "created_at": record.get("created_at"),
        "claimed_at": record.get("claimed_at"),
        "revoked_at": record.get("revoked_at"),
        "replaced_by": record.get("replaced_by"),
    }
