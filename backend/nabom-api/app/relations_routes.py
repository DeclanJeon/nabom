"""NABOM relationship / insight-group facade routes (wired to domain.py)."""

from __future__ import annotations

import math
import threading


from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import auth
import domain
import store
router = APIRouter()

# Relationship and group mutations must serialize each read/modify/save cycle.
# The store API intentionally exposes individual get/set operations, so without
# one process-wide critical section concurrent consent updates can lose grants.
_relationship_group_mutation_lock = threading.Lock()
# Keep the existing evidence lock name as an alias for compatibility while
# ensuring evidence mutations cannot deadlock against other mutations.
_relationship_evidence_lock = _relationship_group_mutation_lock


# SQLite-backed stores (store.py default_store 싱글턴)


def _load_relationship(rel_id: str):
    data = store.default_store.get("relationships", rel_id)
    return domain.Relationship.from_store(data) if data else None


def _save_relationship(rel: domain.Relationship):
    store.default_store.set("relationships", rel.id, rel.to_store())


def _load_group(group_id: str):
    data = store.default_store.get("groups", group_id)
    return domain.InsightGroup.from_store(data) if data else None


def _save_group(group: domain.InsightGroup):
    store.default_store.set("groups", group.id, group.to_store())

def _record_consent_audit(*, actor: str, subject_type: str, subject_id: str, action: str, scopes, reason: str, from_state: str, to_state: str) -> None:
    from datetime import datetime, timezone

    record = {
        "audit_id": domain.new_id("audit"),
        "actor": actor,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "action": action,
        "scopes": list(scopes) if scopes is not None else [],
        "policy_version": "consent-v1",
        "reason": reason,
        "from_state": from_state,
        "to_state": to_state,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }
    store.default_store.set("consent_audits", record["audit_id"], record)

def _require_user(user_id: str) -> str:
    return user_id



def _group_member_profiles(group):
    """Return profiles only for active members who explicitly consented."""
    profiles = []
    for user_id, member in group.members.items():
        if member.get("status") != "active" or member.get("consent_granted") is not True:
            continue
        profile = store.default_store.get("group_member_profiles", f"{group.id}:{user_id}")
        if profile:
            profiles.append(profile)
    return profiles

def _validate_profile_snapshot(snapshot: dict | None, label: str = "profile_snapshot") -> None:
    """Reject malformed aggregate inputs before they reach persistent storage."""
    if not isinstance(snapshot, dict):
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "message": f"{label} must be an object", "retryable": False},
        )
    ratio = snapshot.get("ratio")
    unsupported_fields = set(snapshot) - {"ratio"}
    if unsupported_fields:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "message": f"{label} contains unsupported fields", "retryable": False},
        )
    if not isinstance(ratio, dict):
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "message": f"{label}.ratio must be an object", "retryable": False},
        )

    required_elements = {"wood", "fire", "earth", "metal", "water"}
    if not ratio:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "message": f"{label}.ratio must not be empty", "retryable": False},
        )
    missing_elements = required_elements.difference(ratio)
    if missing_elements:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_INPUT",
                "message": f"{label}.ratio missing required elements",
                "retryable": False,
            },
        )
    for element, value in ratio.items():
        if (
            not isinstance(element, str)
            or not isinstance(value, (int, float))
            or isinstance(value, bool)
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INVALID_INPUT",
                    "message": f"{label}.ratio values must be finite numbers in the range [0, 1]",
                    "retryable": False,
                },
            )
        try:
            finite = math.isfinite(value)
        except (OverflowError, TypeError):
            finite = False
        if not finite or not 0 <= value <= 1:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INVALID_INPUT",
                    "message": f"{label}.ratio values must be finite numbers in the range [0, 1]",
                    "retryable": False,
                },
            )

def _validate_birth_dict(birth: dict, label: str):
    """관계 생성 시 출생 입력을 fail-fast로 구조 검증 (엔진 검증과 이중 안전)."""
    from datetime import datetime

    if not isinstance(birth, dict):
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "message": f"{label} must be an object", "retryable": False},
        )
    calendar = birth.get("calendar", "solar")
    if calendar not in {"solar", "lunar"}:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "message": f"{label} calendar must be solar or lunar", "retryable": False},
        )
    time_precision = birth.get("time_precision", "exact")
    if time_precision not in {"exact", "approximate", "unknown"}:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "message": f"{label} invalid time_precision", "retryable": False},
        )
    try:
        parsed = datetime.strptime(birth.get("date", ""), "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": f"{label} date must be YYYY-MM-DD", "retryable": False}) from exc
    if not (1900 <= parsed.year <= 2100):
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": f"{label} birth year must be 1900-2100", "retryable": False})
    if parsed.date() > datetime.now().date():
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": f"{label} birth date cannot be in the future", "retryable": False})
    raw_time = birth.get("time", "")
    if raw_time is None:
        raw_time = ""
    time_parts = [part.strip() for part in raw_time.split("-")] if isinstance(raw_time, str) and raw_time else []
    if (
        not isinstance(raw_time, str)
        or len(time_parts) > 2
        or (time_precision == "exact" and raw_time and len(time_parts) != 1)
        or (time_precision == "unknown" and raw_time)
    ):
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "message": f"{label} invalid time", "retryable": False},
        )
    try:
        for time_part in time_parts:
            datetime.strptime(time_part, "%H:%M")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": f"{label} invalid time", "retryable": False}) from exc
    location = birth.get("location", {})
    if not isinstance(location, dict):
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "message": f"{label} location must be an object", "retryable": False},
        )
    tz = location.get("timezone") or "Asia/Seoul"
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(tz)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": f"{label} invalid timezone", "retryable": False}) from exc


def _require_member(group, user_id: str):
    member = group.members.get(user_id)
    if not member or member.get("status") != "active" or member.get("consent_granted") is not True:
        raise HTTPException(status_code=403, detail={"code": "CONSENT_REQUIRED", "message": "active consented group member only", "retryable": False})


def _require_participant(rel, user_id: str):
    if user_id not in rel.participants():
        raise HTTPException(status_code=403, detail={"code": "CONSENT_REQUIRED", "message": "participant only", "retryable": False})


def _require_relationship_evidence_consent(rel):
    if rel.state != "active":
        raise HTTPException(
            status_code=403,
            detail={"code": "CONSENT_REQUIRED", "message": "active relationship required", "retryable": False},
        )
    if any("relationship_evidence" not in rel.active_scope(user_id) for user_id in rel.participants()):
        raise HTTPException(
            status_code=403,
            detail={"code": "CONSENT_REQUIRED", "message": "bilateral relationship evidence consent required", "retryable": False},
        )


class CreateRelationshipRequest(BaseModel):
    participant_user_id: str
    context: str = "friend"
    user_birth_input: dict | None = None
    participant_birth_input: dict | None = None


class ConsentRequest(BaseModel):
    scopes: list[str] = Field(default_factory=lambda: list(domain.DEFAULT_SCOPE))


class EvidenceRequest(BaseModel):
    content: str
    observations: list[str] = Field(default_factory=list)
    consent_scope: str = "relationship_evidence"


class MirrorRequest(BaseModel):
    partner_birth_input: dict
    user_birth_input: dict | None = None


class CreateGroupRequest(BaseModel):
    name: str
    owner_profile_snapshot: dict | None = None


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "member"
    visibility_scope: str = "character_only"
    profile_snapshot: dict | None = None  # element_balance.ratio 스냅샷 (개인 raw 불포함)


class MemberConsentRequest(BaseModel):
    granted: bool = True


# ── Relationship ────────────────────────────────────────────────────────────

@router.get("/api/v1/relationships")
def list_relationships(user_id: str = Depends(auth.get_authenticated_identity)):
    user = _require_user(user_id)
    items = []
    for data in store.default_store.list("relationships"):
        rel = domain.Relationship.from_store(data)
        if user in rel.participants() and rel.state != "deleted":
            items.append(rel.to_dict())
    return {"relationships": items}


@router.get("/api/v1/relationships/{relationship_id}")
def get_relationship(relationship_id: str, user_id: str = Depends(auth.get_authenticated_identity)):
    user = _require_user(user_id)
    rel = _load_relationship(relationship_id)
    if not rel:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "relationship not found", "retryable": False})
    _require_participant(rel, user)
    return rel.to_dict()


@router.get("/api/v1/insight-groups")
def list_groups(user_id: str = Depends(auth.get_authenticated_identity)):
    user = _require_user(user_id)
    items = []
    for data in store.default_store.list("groups"):
        group = domain.InsightGroup.from_store(data)
        if user == group.owner or user in group.members:
            items.append({"group_id": group.id, "name": group.name, "owner": group.owner, "status": group.state, "members": group.members})
    return {"groups": items}

@router.post("/api/v1/relationships")
def create_relationship(
    payload: CreateRelationshipRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    with _relationship_group_mutation_lock:
        initiator = _require_user(user_id)
        if payload.participant_user_id == initiator:
            raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "self relationship is not allowed", "retryable": False})
        try:
            rel = domain.Relationship(domain.new_id("rel"), initiator, payload.participant_user_id, payload.context)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": str(exc), "retryable": False}) from exc
        if payload.user_birth_input is not None:
            _validate_birth_dict(payload.user_birth_input, "user")
            rel.set_birth_input(initiator, payload.user_birth_input)
        if payload.participant_birth_input is not None:
            _validate_birth_dict(payload.participant_birth_input, "participant")
            rel.set_birth_input(payload.participant_user_id, payload.participant_birth_input)
        _save_relationship(rel)
        return rel.to_dict()



@router.post("/api/v1/relationships/{relationship_id}/consent")
def grant_relationship_consent(
    relationship_id: str,
    payload: ConsentRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    with _relationship_group_mutation_lock:
        user = _require_user(user_id)
        rel = _load_relationship(relationship_id)
        if not rel:
            raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "relationship not found", "retryable": False})
        _require_participant(rel, user)
        previous = rel.state
        try:
            rel.grant_consent(user, payload.scopes)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": str(exc), "retryable": False}) from exc
        _save_relationship(rel)
        _record_consent_audit(actor=user, subject_type="relationship", subject_id=rel.id, action="grant", scopes=payload.scopes, reason="participant_grant", from_state=previous, to_state=rel.state)
        return rel.to_dict()



@router.post("/api/v1/relationships/{relationship_id}/revoke")
def revoke_relationship(relationship_id: str, user_id: str = Depends(auth.get_authenticated_identity)):
    with _relationship_group_mutation_lock:
        user = _require_user(user_id)
        rel = _load_relationship(relationship_id)
        if not rel:
            raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "relationship not found", "retryable": False})
        _require_participant(rel, user)
        previous = rel.state
        rel.revoke()
        _save_relationship(rel)
        _record_consent_audit(actor=user, subject_type="relationship", subject_id=rel.id, action="revoke", scopes=[], reason="participant_revoke", from_state=previous, to_state=rel.state)
        return rel.to_dict()



@router.post("/api/v1/relationships/{relationship_id}/evidence")
def add_relationship_evidence(
    relationship_id: str,
    payload: EvidenceRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    author = _require_user(user_id)
    with _relationship_evidence_lock:
        rel = _load_relationship(relationship_id)
        if not rel:
            raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "relationship not found", "retryable": False})
        _require_participant(rel, author)
        _require_relationship_evidence_consent(rel)
        try:
            event = rel.add_evidence(author, payload.content, payload.observations, payload.consent_scope)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": str(exc), "retryable": False}) from exc
        _save_relationship(rel)
        return event


@router.get("/api/v1/relationships/{relationship_id}/evidence")
def list_relationship_evidence(relationship_id: str, user_id: str = Depends(auth.get_authenticated_identity)):
    user = _require_user(user_id)
    rel = _load_relationship(relationship_id)
    if not rel:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "relationship not found", "retryable": False})
    _require_participant(rel, user)
    _require_relationship_evidence_consent(rel)
    try:
        evidence = rel.list_evidence(user)
    except ValueError as exc:
        if str(exc) == "relationship_not_active":
            raise HTTPException(
                status_code=403,
                detail={"code": "CONSENT_REQUIRED", "message": "bilateral relationship evidence consent required", "retryable": False},
            ) from exc
        raise
    return {"relationship_id": relationship_id, "evidence": evidence}


# ── InsightGroup ────────────────────────────────────────────────────────────

@router.post("/api/v1/insight-groups")
def create_group(payload: CreateGroupRequest, user_id: str = Depends(auth.get_authenticated_identity)):
    with _relationship_group_mutation_lock:
        owner = _require_user(user_id)
        group = domain.InsightGroup(domain.new_id("ig"), owner, payload.name)
        group.add_owner()
        if payload.owner_profile_snapshot is not None:
            _validate_profile_snapshot(payload.owner_profile_snapshot, "owner_profile_snapshot")
            store.default_store.set("group_member_profiles", f"{group.id}:{owner}", payload.owner_profile_snapshot)
        _save_group(group)
        return {"group_id": group.id, "name": group.name, "owner": owner, "status": group.state}



@router.post("/api/v1/insight-groups/{group_id}/members")
def add_group_member(
    group_id: str,
    payload: AddMemberRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    with _relationship_group_mutation_lock:
        actor = _require_user(user_id)
        group = _load_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "group not found", "retryable": False})
        if actor != group.owner:
            raise HTTPException(status_code=403, detail={"code": "CONSENT_REQUIRED", "message": "group owner only", "retryable": False})
        try:
            group.add_member(payload.user_id, role=payload.role, visibility_scope=payload.visibility_scope)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": str(exc), "retryable": False}) from exc
        if payload.profile_snapshot is not None:
            _validate_profile_snapshot(payload.profile_snapshot)
            store.default_store.set("group_member_pending_profiles", f"{group_id}:{payload.user_id}", payload.profile_snapshot)
        _save_group(group)
        return {"group_id": group_id, "members": group.members, "status": group.state}



@router.post("/api/v1/insight-groups/{group_id}/members/consent")
def grant_group_member_consent(
    group_id: str,
    payload: MemberConsentRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    with _relationship_group_mutation_lock:
        member_id = _require_user(user_id)
        group = _load_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "group not found", "retryable": False})
        if member_id not in group.members:
            raise HTTPException(status_code=403, detail={"code": "CONSENT_REQUIRED", "message": "invited member only", "retryable": False})
        previous = group.state
        try:
            if payload.granted:
                group.grant_member_consent(member_id)
                pending_key = f"{group_id}:{member_id}"
                pending = store.default_store.get("group_member_pending_profiles", pending_key)
                if pending:
                    store.default_store.set("group_member_profiles", pending_key, pending)
            else:
                group.decline_member_consent(member_id)
                snapshot_key = f"{group_id}:{member_id}"
                store.default_store.delete("group_member_pending_profiles", snapshot_key)
                store.default_store.delete("group_member_profiles", snapshot_key)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": str(exc), "retryable": False}) from exc
        _save_group(group)
        _record_consent_audit(
            actor=member_id,
            subject_type="insight_group",
            subject_id=group.id,
            action="grant" if payload.granted else "decline",
            scopes=["character_only"],
            reason="group_member_consent",
            from_state=previous,
            to_state=group.state,
        )
        return {"group_id": group_id, "members": group.members, "status": group.state}


@router.get("/api/v1/insight-groups/{group_id}/profile")
def get_group_profile(group_id: str, user_id: str = Depends(auth.get_authenticated_identity)):
    user = _require_user(user_id)
    group = _load_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "group not found", "retryable": False})
    _require_member(group, user)
    return group.aggregate_profile(_group_member_profiles(group))


@router.post("/api/v1/insight-groups/{group_a_id}/relationship-insights")
def create_group_insight(
    group_a_id: str,
    payload: dict,
    user_id: str = Depends(auth.get_authenticated_identity),
):
    """payload: {"group_b_id": "..."} — 그룹 간 aggregate-only 분석"""
    user = _require_user(user_id)
    group_b_id = payload.get("group_b_id") if isinstance(payload, dict) else None
    if not isinstance(group_b_id, str) or not group_b_id.strip():
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "group_b_id must be a non-empty string", "retryable": False})
    group_a = _load_group(group_a_id)
    if group_a_id == group_b_id:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "group_a_id and group_b_id must differ", "retryable": False})
    group_b = _load_group(group_b_id)
    if not group_a or not group_b:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "group not found", "retryable": False})
    if not (
        (group_a.members.get(user, {}).get("status") == "active" and group_a.members.get(user, {}).get("consent_granted") is True)
        or (group_b.members.get(user, {}).get("status") == "active" and group_b.members.get(user, {}).get("consent_granted") is True)
    ):
        raise HTTPException(status_code=403, detail={"code": "CONSENT_REQUIRED", "message": "must be an active consented member of one of the groups", "retryable": False})
    prof_a = group_a.aggregate_profile(_group_member_profiles(group_a))
    prof_b = group_b.aggregate_profile(_group_member_profiles(group_b))
    try:
        return domain.group_to_group_insight(prof_a, prof_b)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": str(exc), "retryable": False}) from exc


def resolve_mirror_from_engine(engine: dict, rel: domain.Relationship, user_id: str) -> dict:
    """engine compatibility 결과 → 방향성 RelationshipMirror (scope enforcement 포함)."""
    if rel.state != "active":
        raise HTTPException(status_code=403, detail={"code": "CONSENT_REQUIRED", "message": "bilateral consent required", "retryable": False})
    if not isinstance(engine, dict) or "feature_scores" not in engine:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "feature_scores is required", "retryable": False})
    feature_scores = engine["feature_scores"]
    if not isinstance(feature_scores, list) or not feature_scores:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "feature_scores is malformed", "retryable": False})
    participant_scopes = [rel.active_scope(uid) for uid in rel.participants()]
    mutual_scopes = set.intersection(*participant_scopes)
    allowed: set[str] = set()
    for scope in mutual_scopes:
        allowed |= domain.SCOPE_FEATURES.get(scope, set())
    try:
        decomposed = domain.decompose_mirror(feature_scores, allowed)
    except (TypeError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "feature_scores is malformed", "retryable": False}) from exc
    quality = engine.get("quality") if isinstance(engine.get("quality"), dict) else {}
    raw_band = quality.get("score_band", quality.get("confidence_band"))
    allowed_quality_bands = {"high", "medium", "limited", "low"}
    evidence_consent_granted = all(
        "relationship_evidence" in rel.active_scope(uid) for uid in rel.participants()
    )
    evidence_refs = []
    if evidence_consent_granted:
        evidence_refs = [
            evidence.get("evidence_id")
            for evidence in rel.evidence
            if isinstance(evidence, dict) and isinstance(evidence.get("evidence_id"), str)
        ]
    # Engine quality is not evidence confidence unless both participants have
    # opted into relationship evidence and at least one event is stored.
    confidence_band = (
        raw_band if raw_band in allowed_quality_bands and evidence_refs else "low"
    )
    return {
        "relationship_mirror_id": domain.new_id("rm"),
        "relationship_id": rel.id,
        "source_priority": ["relationship_evidence", "mutual_feedback", "public_trait_state", "birth_hypothesis"],
        "contributions_a_to_b": decomposed["a_to_b"],
        "contributions_b_to_a": decomposed["b_to_a"],
        "shared_growth_areas": decomposed["shared"],
        "tensions": decomposed["tensions"],
        "evidence_count": len(rel.evidence) if evidence_consent_granted else 0,
        "confidence": confidence_band,
        "evidence_refs": evidence_refs,
        "status": "hypothesis",
    }
