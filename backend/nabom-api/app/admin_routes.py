"""Operator admin surface. Raw journals are never included."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException

import auth
import store

router = APIRouter()

POLICY_VERSION = "nabom-privacy-v1"
TERMS_VERSION = "nabom-terms-v1"


def _forbidden(message: str = "admin role required") -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": "ADMIN_REQUIRED", "message": message, "retryable": False},
    )


def _admin_ids() -> set[str]:
    raw = os.environ.get("NABOM_ADMIN_USER_IDS", "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def require_admin(user_id: str = Depends(auth.get_authenticated_identity)) -> str:
    if user_id not in _admin_ids():
        raise _forbidden()
    return user_id


def _owned(collection: str, user_id: str) -> list[dict]:
    records = []
    for record in store.default_store.list(collection):
        if record.get("user_id") != user_id:
            continue
        if record.get("status") == "deleted" or record.get("status_record") == "deleted":
            continue
        records.append(record)
    return records


def public_user_summary(account: dict) -> dict:
    user_id = account["user_id"]
    entries = _owned("daily_entries", user_id)
    journals = _owned("journals", user_id)
    mirrors = _owned("weekly_mirrors", user_id)
    experiments = [
        record
        for record in store.default_store.list("experiments")
        if record.get("user_id") == user_id and record.get("status_record") != "deleted"
    ]
    profiles = [
        record
        for record in store.default_store.list("profiles")
        if record.get("user_id") == user_id and record.get("status") != "deleted"
    ]
    recorded_days = {item.get("date") for item in entries} | {item.get("date") for item in journals}
    latest_mirror = max(mirrors, key=lambda item: str(item.get("generated_at") or ""), default=None)
    latest_profile = max(
        profiles,
        key=lambda item: (item.get("profile") or {}).get("number", 0),
        default=None,
    )
    profile = (latest_profile or {}).get("profile") or {}
    return {
        "user_id": user_id,
        "email": account.get("email"),
        "nickname": account.get("nickname") or "",
        "status": account.get("status") or "active",
        "created_at": account.get("created_at"),
        "profile_status": "active" if profile else "none",
        "profile_number": profile.get("number"),
        "entry_count": len(entries),
        "journal_count": len(journals),
        "recorded_days": len(recorded_days),
        "weekly_status": (latest_mirror or {}).get("coverage", {}).get("mode") or "none",
        "experiment_count": len(experiments),
    }


@router.get("/api/v1/admin/users")
def list_users(_admin_id: str = Depends(require_admin)):
    users = []
    for account in store.default_store.list("accounts"):
        if account.get("status") == "deleted":
            continue
        users.append(public_user_summary(account))
    users.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return {"users": users}


@router.get("/api/v1/admin/users/{user_id}")
def get_user(user_id: str, _admin_id: str = Depends(require_admin)):
    account = store.default_store.get("accounts", user_id)
    if not account or account.get("status") == "deleted":
        raise HTTPException(
            status_code=404,
            detail={"code": "RESOURCE_NOT_FOUND", "message": "user not found", "retryable": False},
        )
    return public_user_summary(account)


@router.get("/api/v1/admin/summary")
def admin_summary(_admin_id: str = Depends(require_admin)):
    """운영 대시보드 요약: 사용자·기록·회고·기기 현황 (raw journal 미포함)."""
    accounts = [a for a in store.default_store.list("accounts") if a.get("status") != "deleted"]
    active = [a for a in accounts if a.get("status") == "active"]
    entries = [r for r in store.default_store.list("daily_entries") if r.get("status") in {None, "active"}]
    journals = [r for r in store.default_store.list("journals") if r.get("status") in {None, "active"}]
    mirrors = [r for r in store.default_store.list("weekly_mirrors") if r.get("status") in {None, "active"}]
    profiles = [r for r in store.default_store.list("profiles") if r.get("status") != "deleted"]
    devices = sum(len(a.get("devices") or []) for a in accounts)
    return {
        "accounts": {"total": len(accounts), "active": len(active)},
        "records": {
            "daily_entries": len(entries),
            "journals": len(journals),
            "total_recorded_days": len({r.get("date") for r in entries} | {r.get("date") for r in journals}),
        },
        "living": {
            "weekly_mirrors": len(mirrors),
            "profiles": len(profiles),
        },
        "devices": devices,
    }


@router.get("/api/v1/legal/privacy")
def privacy_policy():
    return {
        "document": "privacy",
        "version": POLICY_VERSION,
        "title": "개인정보처리방침",
        "updated_at": "2026-08-13",
        "sections": [
            {
                "heading": "수집하는 정보",
                "body": "이메일, 닉네임, 출생정보, 기분·에너지·만족도, 일기, 프로필 피드백을 서비스 제공을 위해 수집합니다.",
            },
            {
                "heading": "이용 목적",
                "body": "초기 가설 프로필, 주간 거울, 성장 실험, 계정 복구에만 사용합니다. 광고나 외부 학습에는 쓰지 않습니다.",
            },
            {
                "heading": "보관과 삭제",
                "body": "계정 또는 개별 기록을 삭제하면 분석 근거에서도 제외됩니다. 삭제는 tombstone 후 운영 잡으로 정리합니다.",
            },
            {
                "heading": "내보내기",
                "body": "설정에서 내 데이터를 JSON으로 내보낼 수 있습니다. raw 엔진 차트는 포함하지 않습니다.",
            },
        ],
    }


@router.get("/api/v1/legal/terms")
def terms_of_use():
    return {
        "document": "terms",
        "version": TERMS_VERSION,
        "title": "이용약관",
        "updated_at": "2026-08-13",
        "sections": [
            {
                "heading": "서비스 성격",
                "body": "나봄은 성격 진단이나 운세가 아닙니다. 기록과 초기 가설을 바탕으로 관찰을 돕는 도구입니다.",
            },
            {
                "heading": "금지되는 기대",
                "body": "의료, 법률, 재정, 관계 단절 같은 고위험 결정을 대신하지 않습니다.",
            },
            {
                "heading": "이용자의 권리",
                "body": "기록 열람, 내보내기, 개별 삭제, 계정 탈퇴를 언제든 요청할 수 있습니다.",
            },
        ],
    }
