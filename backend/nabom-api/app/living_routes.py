"""Authenticated DailyEntry, journal, and Evidence facade routes."""

from __future__ import annotations

import threading
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import auth
import domain
import living
import relations_routes
import store

router = APIRouter()
_living_mutation_lock = threading.Lock()


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _invalid(message: str) -> HTTPException:
    return HTTPException(
        status_code=422,
        detail={"code": "INVALID_INPUT", "message": message, "retryable": False},
    )


def _missing(message: str = "record not found") -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "RESOURCE_NOT_FOUND", "message": message, "retryable": False},
    )


class DailyEntryRequest(BaseModel):
    date: str
    timezone: str = "Asia/Seoul"
    mood: int
    energy: int
    satisfaction: int
    text: str = ""
    tags: list[str] = Field(default_factory=list)


class JournalRequest(BaseModel):
    date: str
    timezone: str = "Asia/Seoul"
    text: str
    tags: list[str] = Field(default_factory=list)


class WeeklyMirrorRequest(BaseModel):
    period_from: str
    period_to: str
    timezone: str = "Asia/Seoul"

class EvidenceRequest(BaseModel):
    source_type: str
    source_record_id: str
    timezone: str = "Asia/Seoul"


def _is_active(record: dict | None) -> bool:
    return bool(record) and record.get("status") in {None, "active"}


def _owned_record(collection: str, record_id: str, user_id: str) -> dict:
    record = store.default_store.get(collection, record_id)
    if not record or record.get("user_id") != user_id or not _is_active(record):
        raise _missing()
    return record


def _list_owned(collection: str, user_id: str) -> list[dict]:
    records = []
    for record in store.default_store.list(collection):
        if record.get("user_id") == user_id and _is_active(record):
            records.append(record)
    return records


def _lookup_by_date(index_collection: str, user_id: str, record_date: str) -> dict | None:
    record_id = store.default_store.get(index_collection, f"{user_id}:{record_date}")
    if not record_id or not isinstance(record_id.get("record_id"), str):
        return None
    collection = "daily_entries" if index_collection == "daily_by_date" else "journals"
    record = store.default_store.get(collection, record_id["record_id"])
    if not record or record.get("user_id") != user_id or record.get("status") == "deleted":
        return None
    return record


# ── Growth Experiment (mirror에 포함된 단일 행동) ────────────────────────────

# 설계 §9: 한 번에 1개 권장, 최대 3개 활성 실험 (accepted/in_progress).
MAX_ACTIVE_EXPERIMENTS = 3


def _active_experiment_count(user_id: str) -> int:
    records = [
        record
        for record in store.default_store.list("experiments")
        if record.get("user_id") == user_id
        and record.get("status_record") != "deleted"
        and record.get("status") in {"accepted", "in_progress"}
    ]
    return len(records)


def store_experiments_from_mirror(user_id: str, mirror: dict) -> None:
    """full mirror가 만든 실험을 experiments 컬렉션에 최초 1회 저장한다 (append-only).

    활성 실험(accepted/in_progress)이 MAX_ACTIVE_EXPERIMENTS개 이상이면
    새 실험을 추가하지 않는다 (설계 §9 최대 3개).
    """
    experiment = mirror.get("growth_experiment")
    if not experiment:
        return
    experiment_id = experiment.get("experiment_id")
    if not experiment_id or store.default_store.get("experiments", experiment_id):
        return
    if _active_experiment_count(user_id) >= MAX_ACTIVE_EXPERIMENTS:
        return
    generated_at = mirror.get("generated_at") or _now_iso()
    store.default_store.set(
        "experiments",
        experiment_id,
        {
            "experiment_id": experiment_id,
            "user_id": user_id,
            "mirror_id": mirror.get("mirror_id"),
            "title": experiment["title"],
            "instruction": experiment["instruction"],
            "success_condition": experiment["success_condition"],
            "reversible": bool(experiment.get("reversible", True)),
            "status": "accepted",
            "user_result": None,
            "created_at": generated_at,
            "updated_at": generated_at,
            "status_record": "active",
        },
    )


def public_experiment(experiment: dict) -> dict:
    return {
        "experiment_id": experiment["experiment_id"],
        "mirror_id": experiment.get("mirror_id"),
        "title": experiment["title"],
        "instruction": experiment["instruction"],
        "success_condition": experiment["success_condition"],
        "reversible": bool(experiment.get("reversible", True)),
        "status": experiment["status"],
        "user_result": experiment.get("user_result"),
        "created_at": experiment.get("created_at"),
        "updated_at": experiment.get("updated_at"),
    }


class ExperimentUpdateRequest(BaseModel):
    status: str
    user_result: str | None = None


@router.post("/api/v1/living/entries")
def upsert_daily_entry(
    payload: DailyEntryRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    with _living_mutation_lock:
        try:
            existing = _lookup_by_date("daily_by_date", user_id, payload.date)
            entry = living.build_daily_entry(
                user_id,
                record_date=payload.date,
                timezone=payload.timezone,
                mood=payload.mood,
                energy=payload.energy,
                satisfaction=payload.satisfaction,
                text=payload.text,
                tags=payload.tags,
                existing=existing,
            )
        except living.LivingRecordError as exc:
            raise _invalid(str(exc)) from exc
        store.default_store.set("daily_entries", entry["entry_id"], entry)
        store.default_store.set("daily_by_date", f"{user_id}:{entry['date']}", {"record_id": entry["entry_id"]})
        return living.public_daily_entry(entry)


@router.get("/api/v1/living/entries")
def list_daily_entries(user_id: str = Depends(auth.get_authenticated_identity)):
    entries = sorted(_list_owned("daily_entries", user_id), key=lambda item: item["date"])
    return {"entries": [living.public_daily_entry(entry) for entry in entries]}


@router.get("/api/v1/living/entries/{entry_id}")
def get_daily_entry(entry_id: str, user_id: str = Depends(auth.get_authenticated_identity)):
    return living.public_daily_entry(_owned_record("daily_entries", entry_id, user_id))


@router.post("/api/v1/living/journals")
def upsert_journal(
    payload: JournalRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    with _living_mutation_lock:
        try:
            existing = _lookup_by_date("journal_by_date", user_id, payload.date)
            journal = living.build_journal(
                user_id,
                record_date=payload.date,
                timezone=payload.timezone,
                text=payload.text,
                tags=payload.tags,
                existing=existing,
            )
        except living.LivingRecordError as exc:
            raise _invalid(str(exc)) from exc
        store.default_store.set("journals", journal["journal_id"], journal)
        store.default_store.set("journal_by_date", f"{user_id}:{journal['date']}", {"record_id": journal["journal_id"]})
        return living.public_journal(journal)


@router.get("/api/v1/living/journals")
def list_journals(user_id: str = Depends(auth.get_authenticated_identity)):
    journals = sorted(_list_owned("journals", user_id), key=lambda item: item["date"])
    return {"journals": [living.public_journal(journal) for journal in journals]}


@router.get("/api/v1/living/journals/{journal_id}")
def get_journal(journal_id: str, user_id: str = Depends(auth.get_authenticated_identity)):
    return living.public_journal(_owned_record("journals", journal_id, user_id))


@router.post("/api/v1/living/evidence")
def create_evidence(
    payload: EvidenceRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    with _living_mutation_lock:
        source_collection = "daily_entries" if payload.source_type == "daily" else "journals"
        if payload.source_type not in living.EVIDENCE_SOURCE_TYPES:
            raise _invalid("source_type must be daily or journal")
        source = store.default_store.get(source_collection, payload.source_record_id)
        if not source or source.get("user_id") != user_id or source.get("status") == "deleted":
            raise _missing("source record not found")
        existing = None
        for record in _list_owned("evidence", user_id):
            if record.get("source_record_id") == payload.source_record_id and record.get("type") == payload.source_type:
                existing = record
                break
        try:
            evidence = living.build_evidence(
                user_id,
                source_type=payload.source_type,
                source=source,
                timezone=payload.timezone,
                existing=existing,
            )
        except living.LivingRecordError as exc:
            raise _invalid(str(exc)) from exc
        store.default_store.set("evidence", evidence["evidence_id"], evidence)
        return living.public_evidence(evidence)


@router.get("/api/v1/living/evidence")
def list_evidence(user_id: str = Depends(auth.get_authenticated_identity)):
    records = sorted(_list_owned("evidence", user_id), key=lambda item: item.get("occurred_at", ""))
    return {"evidence": [living.public_evidence(record) for record in records]}


@router.get("/api/v1/living/evidence/{evidence_id}")
def get_evidence(evidence_id: str, user_id: str = Depends(auth.get_authenticated_identity)):
    return living.public_evidence(_owned_record("evidence", evidence_id, user_id))


@router.post("/api/v1/living/mirrors")
def create_weekly_mirror(
    payload: WeeklyMirrorRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    with _living_mutation_lock:
        try:
            mirror = living.build_weekly_mirror(
                user_id,
                period_from=payload.period_from,
                period_to=payload.period_to,
                timezone=payload.timezone,
                entries=_list_owned("daily_entries", user_id),
                journals=_list_owned("journals", user_id),
                evidence=_list_owned("evidence", user_id),
                previous=_previous_mirror(user_id, payload.period_from),
            )
        except living.LivingRecordError as exc:
            raise _invalid(str(exc)) from exc
        store.default_store.set("weekly_mirrors", mirror["mirror_id"], mirror)
        store_experiments_from_mirror(user_id, mirror)
        return living.public_weekly_mirror(mirror)


def _previous_mirror(user_id: str, period_from: str) -> dict | None:
    """이번 주 이전에 생성된 가장 최근 미러 (changes 비교용)."""
    candidates = [
        item
        for item in _list_owned("weekly_mirrors", user_id)
        if str(item.get("generated_at", ""))[:10] < str(period_from)[:10]
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: str(item.get("generated_at", "")))


@router.get("/api/v1/living/experiments")
def list_experiments(user_id: str = Depends(auth.get_authenticated_identity)):
    records = [
        public_experiment(record)
        for record in store.default_store.list("experiments")
        if record.get("user_id") == user_id and record.get("status_record") != "deleted"
    ]
    records.sort(key=lambda item: str(item.get("created_at") or ""))
    return {"experiments": records}


@router.get("/api/v1/living/experiments/{experiment_id}")
def get_experiment(experiment_id: str, user_id: str = Depends(auth.get_authenticated_identity)):
    record = store.default_store.get("experiments", experiment_id)
    if not record or record.get("user_id") != user_id or record.get("status_record") == "deleted":
        raise _missing("experiment not found")
    return public_experiment(record)


@router.post("/api/v1/living/experiments/{experiment_id}")
def update_experiment(
    experiment_id: str,
    payload: ExperimentUpdateRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    if payload.status not in {"accepted", "in_progress", "completed", "declined"}:
        raise _invalid("status must be accepted|in_progress|completed|declined")
    with _living_mutation_lock:
        record = store.default_store.get("experiments", experiment_id)
        if not record or record.get("user_id") != user_id or record.get("status_record") == "deleted":
            raise _missing("experiment not found")
        record["status"] = payload.status
        if payload.status == "completed":
            record["user_result"] = (payload.user_result or "").strip() or None
        elif payload.status in {"accepted", "declined"}:
            record["user_result"] = None
        record["updated_at"] = _now_iso()
        store.default_store.set("experiments", experiment_id, record)
        return public_experiment(record)


@router.get("/api/v1/living/mirrors")
def list_weekly_mirrors(user_id: str = Depends(auth.get_authenticated_identity)):
    mirrors = sorted(_list_owned("weekly_mirrors", user_id), key=lambda item: item.get("generated_at", ""))
    return {"mirrors": [living.public_weekly_mirror(mirror) for mirror in mirrors]}


@router.get("/api/v1/living/mirrors/{mirror_id}")
def get_weekly_mirror(mirror_id: str, user_id: str = Depends(auth.get_authenticated_identity)):
    return living.public_weekly_mirror(_owned_record("weekly_mirrors", mirror_id, user_id))


def _tombstone(collection: str, record: dict) -> dict:
    record["status"] = "deleted"
    store.default_store.set(collection, record.get("entry_id") or record.get("journal_id") or record.get("evidence_id") or record.get("mirror_id"), record)
    return record

@router.delete("/api/v1/living/entries/{entry_id}")
def delete_daily_entry(entry_id: str, user_id: str = Depends(auth.get_authenticated_identity)):
    with _living_mutation_lock:
        entry = _owned_record("daily_entries", entry_id, user_id)
        _tombstone("daily_entries", entry)
        invalidated = 0
        for record in store.default_store.list("evidence"):
            if record.get("user_id") == user_id and record.get("source_record_id") == entry_id and record.get("status") != "deleted":
                record["status"] = "deleted"
                store.default_store.set("evidence", record["evidence_id"], record)
                invalidated += 1
        for record in store.default_store.list("weekly_mirrors"):
            if record.get("user_id") == user_id and record.get("status") == "active":
                record["status"] = "invalidated"
                store.default_store.set("weekly_mirrors", record["mirror_id"], record)
        return {"entry_id": entry_id, "status": "deleted", "invalidated_evidence": invalidated}


@router.delete("/api/v1/living/journals/{journal_id}")
def delete_journal(journal_id: str, user_id: str = Depends(auth.get_authenticated_identity)):
    with _living_mutation_lock:
        journal = _owned_record("journals", journal_id, user_id)
        _tombstone("journals", journal)
        invalidated = 0
        for record in store.default_store.list("evidence"):
            if record.get("user_id") == user_id and record.get("source_record_id") == journal_id and record.get("status") != "deleted":
                record["status"] = "deleted"
                store.default_store.set("evidence", record["evidence_id"], record)
                invalidated += 1
        for record in store.default_store.list("weekly_mirrors"):
            if record.get("user_id") == user_id and record.get("status") == "active":
                record["status"] = "invalidated"
                store.default_store.set("weekly_mirrors", record["mirror_id"], record)
        return {"journal_id": journal_id, "status": "deleted", "invalidated_evidence": invalidated}


@router.get("/api/v1/living/reports/21-day")
def get_21_day_report(user_id: str = Depends(auth.get_authenticated_identity)):
    entries = _list_owned("daily_entries", user_id)
    journals = _list_owned("journals", user_id)
    dates = {item["date"] for item in entries}
    dates.update(item["date"] for item in journals)
    days = len(dates)
    eligible = days >= 21
    moods = [item["mood"] for item in entries]
    return {
        "report_id": "r21",
        "distinct_recorded_days": days,
        "required_days": 21,
        "eligible": eligible,
        "entitlement": "full" if eligible else "preview",
        "status": "available" if eligible else "ineligible",
        "summary": (
            f"{days}개의 서로 다른 기록일이 있습니다. 숫자는 평가가 아니라 돌아보기 범위입니다."
            if days
            else "아직 기록일이 없어 21일 리포트를 열 수 없습니다."
        ),
        "observed_moods": moods[-7:],
        "journal_count": len(journals),
        "limits": ["평균으로 성격을 단정하지 않습니다", "의료·법률·재무 결론을 내지 않습니다"],
        "next_question": "이번 기록 중에서 다시 보고 싶은 하루는 언제인가요?",
    }


@router.get("/api/v1/privacy/export")
def export_account(user_id: str = Depends(auth.get_authenticated_identity)):
    payload = {
        "exported_at": living.local_calendar_date("UTC"),
        "user_id": user_id,
        "note": "소유한 서버 기록만 포함합니다. raw engine chart는 포함하지 않습니다.",
        "entries": _list_owned("daily_entries", user_id),
        "journals": _list_owned("journals", user_id),
        "evidence": _list_owned("evidence", user_id),
        "mirrors": _list_owned("weekly_mirrors", user_id),
        "profiles": [
            living.public_profile(record.get("profile") or {})
            for record in store.default_store.list("profiles")
            if record.get("user_id") == user_id and record.get("status") != "deleted"
        ],
    }
    return payload


def delete_living_records(user_id: str) -> dict:
    """일상 기록·증거·회고·실험만 tombstone 처리한다 (계정은 유지)."""
    with _living_mutation_lock:
        deleted = 0
        for collection, key_field in (
            ("daily_entries", "entry_id"),
            ("journals", "journal_id"),
            ("evidence", "evidence_id"),
            ("weekly_mirrors", "mirror_id"),
            ("experiments", "experiment_id"),
        ):
            for record in store.default_store.list(collection):
                if record.get("user_id") != user_id:
                    continue
                if record.get("status") == "deleted" or record.get("status_record") == "deleted":
                    continue
                if collection == "experiments":
                    record["status_record"] = "deleted"
                else:
                    record["status"] = "deleted"
                store.default_store.set(collection, record[key_field], record)
                deleted += 1
        for record in store.default_store.list("mirrors"):
            if record.get("user_id") != user_id or record.get("status") == "deleted":
                continue
            reflection = record.get("reflection") or {}
            if reflection.get("mode") != "record_reflection":
                continue
            record_id = reflection.get("reflection_id")
            record["status"] = "deleted"
            if record_id:
                store.default_store.set("mirrors", record_id, record)
                deleted += 1
        return {"user_id": user_id, "status": "deleted", "records_deleted": deleted}


@router.delete("/api/v1/living/records")
def delete_living_records_route(user_id: str = Depends(auth.get_authenticated_identity)):
    return delete_living_records(user_id)


def delete_account_records(user_id: str) -> dict:
    """모든 소유 기록을 tombstone 처리한다 (탈퇴/삭제 job)."""
    with _living_mutation_lock:
        deleted = 0
        for collection, key_field in (
            ("daily_entries", "entry_id"),
            ("journals", "journal_id"),
            ("evidence", "evidence_id"),
            ("weekly_mirrors", "mirror_id"),
            ("experiments", "experiment_id"),
        ):
            for record in store.default_store.list(collection):
                if record.get("user_id") == user_id and record.get("status") != "deleted" and record.get("status_record") != "deleted":
                    if collection == "experiments":
                        record["status_record"] = "deleted"
                    else:
                        record["status"] = "deleted"
                    store.default_store.set(collection, record[key_field], record)
                    deleted += 1
        for record in store.default_store.list("profiles"):
            if record.get("user_id") == user_id and record.get("status") != "deleted":
                profile_id = (record.get("profile") or {}).get("profile_version_id")
                record["status"] = "deleted"
                if profile_id:
                    store.default_store.set("profiles", profile_id, record)
                    deleted += 1
        for record in store.default_store.list("mirrors"):
            if record.get("user_id") == user_id and record.get("status") != "deleted":
                record_id = (record.get("mirror") or record.get("reflection") or {}).get("relationship_mirror_id") or (record.get("reflection") or {}).get("reflection_id") or (record.get("mirror") or {}).get("mirror_id")
                record["status"] = "deleted"
                if record_id:
                    store.default_store.set("mirrors", record_id, record)
        with relations_routes._relationship_group_mutation_lock:
            for data in store.default_store.list("relationships"):
                if user_id not in {data.get("initiator_user_id"), data.get("participant_user_id")}:
                    continue
                rel = domain.Relationship.from_store(data)
                previous = rel.state
                rel._birth_inputs = {}
                if rel.state != "revoked":
                    rel.revoke()
                store.default_store.set("relationships", rel.id, rel.to_store())
                relations_routes._record_consent_audit(
                    actor=user_id,
                    subject_type="relationship",
                    subject_id=rel.id,
                    action="revoke",
                    scopes=[],
                    reason="account_delete",
                    from_state=previous,
                    to_state=rel.state,
                )
                deleted += 1
        for record in store.default_store.list("nfc_tokens"):
            if record.get("owner_user_id") == user_id and record.get("status") != "revoked":
                record["status"] = "revoked"
                record["revoked_at"] = living.local_calendar_date("UTC")
                store.default_store.set("nfc_tokens", record["token"], record)
        return {"user_id": user_id, "status": "deleted", "records_deleted": deleted}


@router.post("/api/v1/privacy/delete-account")
def delete_account(user_id: str = Depends(auth.get_authenticated_identity)):
    return delete_account_records(user_id)
