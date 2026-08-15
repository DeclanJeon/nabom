"""NABOM API Facade — the only public surface for engine-backed living features.

Owns: auth, consent, ownership, persistence (in-memory v1 stub), user-facing
canonical mapping. Never exposes raw engine chart/reading JSON to clients.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import jsonschema
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))

import auth  # noqa: E402
from relations_routes import router as relations_router  # noqa: E402
from living_routes import router as living_router  # noqa: E402
from living_routes import (  # noqa: E402
    delete_account_records,
    store_experiments_from_mirror,
)
from nfc_routes import router as nfc_router  # noqa: E402
from accounts_routes import router as accounts_router  # noqa: E402
from admin_routes import router as admin_router  # noqa: E402
import living  # noqa: E402
from store import default_store as store  # noqa: E402
import character_visual  # noqa: E402
import character_state  # noqa: E402
import profile_lenses  # noqa: E402
import profile_refresh  # noqa: E402

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"


def _load_schema(name: str):
    return json.loads((CONTRACTS_DIR / name).read_text(encoding="utf-8"))


REFLECTION_SCHEMA = _load_schema("reflection.schema.json")

# ── Engine clients (private services) ──────────────────────────────────────

SAJU_ENGINE_URL = os.environ.get("SAJU_ENGINE_URL", "http://localhost:8001")
ICHING_ENGINE_URL = os.environ.get("ICHING_ENGINE_URL", "http://localhost:8002")
SERVICE_TOKEN = os.environ.get("SAJU_SERVICE_TOKEN", "")

# Test injection points: set to an httpx.Transport (e.g. ASGITransport) for offline tests
saju_transport: Optional[httpx.BaseTransport] = None
iching_transport: Optional[httpx.BaseTransport] = None


def _engine_headers(request_id: str):
    headers = {"X-Request-Id": request_id, "X-Contract-Version": "1.0"}
    if SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {SERVICE_TOKEN}"
    return headers


def _engine_response_error(response, request_id: str, fallback_message: str):
    """엔진 4xx는 그대로 전파(클라이언트 입력 오류), 5xx만 502로 매핑."""
    if 400 <= response.status_code < 500:
        try:
            detail = response.json().get("detail", {})
        except Exception:  # noqa: BLE001
            detail = {}
        raise HTTPException(status_code=response.status_code, detail=detail or {"code": "ENGINE_REJECTED", "message": fallback_message, "retryable": False, "request_id": request_id})
    raise HTTPException(status_code=502, detail={"code": "ENGINE_UNAVAILABLE", "message": fallback_message, "retryable": True, "request_id": request_id})


def _engine_transport_error(exc: httpx.TransportError, request_id: str, engine_name: str):
    """Map network failures to the facade's retryable engine error contract."""
    timed_out = isinstance(exc, httpx.TimeoutException)
    code = "ENGINE_TIMEOUT" if timed_out else "ENGINE_UNAVAILABLE"
    message = f"{engine_name} request timed out" if timed_out else f"{engine_name} unavailable"
    raise HTTPException(
        status_code=502,
        detail={"code": code, "message": message, "retryable": True, "request_id": request_id},
    ) from exc


async def call_saju_chart(birth_input: dict, quality_mode: str, request_id: str) -> dict:
    try:
        async with httpx.AsyncClient(base_url=SAJU_ENGINE_URL, transport=saju_transport) as client:
            response = await client.post(
                "/internal/v1/charts",
                json={"birth_input": birth_input, "calculation_policy": {"quality_mode": quality_mode}},
                headers=_engine_headers(request_id),
                timeout=5.0,
            )
    except httpx.TransportError as exc:
        _engine_transport_error(exc, request_id, "saju engine")
    if response.status_code >= 400:
        _engine_response_error(response, request_id, "saju engine rejected request")
    return response.json()


async def call_saju_compatibility(user: dict, partner: dict, context: str, request_id: str) -> dict:
    try:
        async with httpx.AsyncClient(base_url=SAJU_ENGINE_URL, transport=saju_transport) as client:
            response = await client.post(
                "/internal/v1/compatibility",
                json={"user": {"birth_input": user}, "partner": {"birth_input": partner}, "context": context},
                headers=_engine_headers(request_id),
                timeout=5.0,
            )
    except httpx.TransportError as exc:
        _engine_transport_error(exc, request_id, "saju compatibility engine")
    if response.status_code >= 400:
        _engine_response_error(response, request_id, "saju engine rejected compatibility request")
    return response.json()


async def call_saju_luck(birth_input: dict, year: int, month: int | None, request_id: str) -> dict:
    params = {"year": year}
    if month is not None:
        params["month"] = month
    try:
        async with httpx.AsyncClient(base_url=SAJU_ENGINE_URL, transport=saju_transport) as client:
            response = await client.post(
                "/internal/v1/luck",
                params=params,
                json={"birth_input": birth_input, "calculation_policy": {"quality_mode": "strict"}},
                headers=_engine_headers(request_id),
                timeout=5.0,
            )
    except httpx.TransportError as exc:
        _engine_transport_error(exc, request_id, "saju luck engine")
    if response.status_code >= 400:
        _engine_response_error(response, request_id, "saju engine rejected luck request")
    return response.json()


async def call_iching_reflection(reflection_context: dict, request_id: str) -> dict:
    try:
        async with httpx.AsyncClient(base_url=ICHING_ENGINE_URL, transport=iching_transport) as client:
            response = await client.post(
                "/internal/v1/reflections",
                json={"mode": "record_reflection", "reflection_context": reflection_context},
                headers=_engine_headers(request_id),
                timeout=5.0,
            )
    except httpx.TransportError as exc:
        _engine_transport_error(exc, request_id, "iching engine")
    if response.status_code >= 400:
        _engine_response_error(response, request_id, "iching engine rejected reflection request")
    return response.json()




# ── App ────────────────────────────────────────────────────────────────────

app = FastAPI(title="NABOM API Facade", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(relations_router)
app.include_router(living_router)
app.include_router(nfc_router)
app.include_router(accounts_router)
app.include_router(admin_router)

# v1 persistence: SQLite-backed KV (store.py default_store)

# Each key gets its own async lock, so an in-flight build for one request does
# not block unrelated idempotency keys. The small threading lock protects the
# map itself while references are acquired/released and is never held across
# an await.
_idempotency_locks: dict[str, tuple[asyncio.Lock, int]] = {}
_idempotency_locks_guard = threading.Lock()


def _acquire_idempotency_lock(record_key: str) -> asyncio.Lock:
    with _idempotency_locks_guard:
        entry = _idempotency_locks.get(record_key)
        if entry is None:
            lock = asyncio.Lock()
            references = 0
        else:
            lock, references = entry
        _idempotency_locks[record_key] = (lock, references + 1)
        return lock


def _release_idempotency_lock(record_key: str, lock: asyncio.Lock) -> None:
    with _idempotency_locks_guard:
        entry = _idempotency_locks.get(record_key)
        if entry is None or entry[0] is not lock:
            return
        if entry[1] == 1:
            del _idempotency_locks[record_key]
        else:
            _idempotency_locks[record_key] = (lock, entry[1] - 1)


def _request_id(x_request_id: str | None) -> str:
    return x_request_id or str(uuid.uuid4())


async def _facade_idempotency(key: str | None, user_id: str, fingerprint_source: str, build):
    """facade Idempotency-Key: SQLite 영속. 같은 키+body → 동일 응답, 다른 body → 409."""
    import hashlib
    import inspect

    async def _run():
        result = build()
        return await result if inspect.iscoroutine(result) else result

    if not key:
        return await _run()
    record_key = f"{user_id}:{key}"
    fingerprint = hashlib.sha256(f"{key}:{fingerprint_source}".encode()).hexdigest()
    lock = _acquire_idempotency_lock(record_key)
    try:
        async with lock:
            existing = store.get("idempotency", record_key)
            if existing:
                if existing.get("fingerprint") != fingerprint:
                    raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_CONFLICT", "message": "same Idempotency-Key used with different request body", "retryable": False})
                return existing["response"]
            response = await _run()
            store.set("idempotency", record_key, {"fingerprint": fingerprint, "response": response})
            return response
    finally:
        _release_idempotency_lock(record_key, lock)


def _consent_check(
    x_user_id: str | None,
    x_consent: str | None,
    subject: str,
    *,
    authorization: str | None = None,
    authenticated_identity: str | None = None,
):
    """Resolve the authenticated identity before applying consent checks.

    ``authenticated_identity`` is supplied by FastAPI's strict auth
    dependency on public routes.  Direct callers (including the legacy
    compatibility surface) still pass headers and are resolved through the
    same dependency, so ``X-User-Id`` is accepted only in explicit dev mode.
    """
    user = (
        authenticated_identity
        if authenticated_identity is not None
        else auth.get_authenticated_identity(authorization=authorization, x_user_id=x_user_id)
    )
    if subject == "relationship" and x_consent != "granted":
        raise HTTPException(status_code=403, detail={"code": "CONSENT_REQUIRED", "message": "relationship consent not granted", "retryable": False})
    return user


class Location(BaseModel):
    label: str | None = None
    timezone: str | None = None
    lat: float | None = None
    lon: float | None = None


class BirthInput(BaseModel):
    calendar: str = "solar"
    date: str
    time: str = ""
    time_precision: str = "exact"
    time_window: str | None = None
    is_lunar_leap_month: bool | None = None
    location: Location | None = None
    gender: str = "unknown"


class InitialProfileRequest(BaseModel):
    birth_input: BirthInput
    current_priorities: list[str] = Field(default_factory=list)
    change_goal: str = ""
    current_goal: str = ""


class ReflectionRequest(BaseModel):
    period_from: str
    period_to: str
    timezone: str = "Asia/Seoul"


class RelationshipMirrorRequest(BaseModel):
    context: str = "friend"
    partner_birth_input: dict | None = None
    user_birth_input: dict | None = None


class ProfileFeedbackRequest(BaseModel):
    target_type: str = "trait"  # trait | overall
    target_key: str
    rating: str  # correct | mostly_correct | situational | unsure | incorrect
    comment: str = ""


# ── Trait mapping (Step 5): element analysis → birth-hypothesis traits ─────
# Phase 1 SSOT trait pool: 탐색/실행/지속/연결/회복/구조/표현 (NABOM_P1 설계 §3.2)

PHASE1_TRAIT_POOL = {
    "exploration": "탐색",
    "execution": "실행",
    "persistence": "지속",
    "connection": "연결",
    "recovery": "회복",
    "structure": "구조",
    "expression": "표현",
}

# 오행 → Phase 1 trait (CharacterMapper와 함께 사용)
TRAIT_BY_ELEMENT = {
    "wood": "exploration",
    "fire": "expression",
    "earth": "structure",
    "metal": "execution",
    "water": "recovery",
}

# 오행 → 사용자-facing 성향 언어. 명리 용어는 밖으로 나가지 않는다.
TRAIT_VOICE = {
    "exploration": {
        "noun": "호기심",
        "adjective": "호기심 많은",
        "tone": "새로운 걸 열어보는 힘",
    },
    "execution": {
        "noun": "추진력",
        "adjective": "활동적인",
        "tone": "일을 밀어내는 힘",
    },
    "persistence": {
        "noun": "꾸준함",
        "adjective": "꾸준한",
        "tone": "오래 이어가는 힘",
    },
    "connection": {
        "noun": "친밀함",
        "adjective": "따뜻한",
        "tone": "사람과 맞추는 힘",
    },
    "recovery": {
        "noun": "회복력",
        "adjective": "차분한",
        "tone": "숨 고르고 다시 서는 힘",
    },
    "structure": {
        "noun": "안정감",
        "adjective": "차분하고 단단한",
        "tone": "자리를 지키는 힘",
    },
    "expression": {
        "noun": "명랑함",
        "adjective": "명랑한",
        "tone": "감정을 밖으로 드러내는 힘",
    },
}
STRENGTH_VOICE = {
    "shingang": "에너지가 바깥으로 잘 퍼지는 편",
    "shinyak": "에너지를 아끼며 안쪽으로 모으는 편",
    "junghwa": "바깥으로 쓰는 힘과 안쪽으로 모으는 힘이 비슷한 편",
}
GROWTH_VOICE = {
    "wood": ("새 시도를 열어보기", "배움이나 만남을 작게라도 시작해 보기"),
    "fire": ("감정을 밖으로 꺼내보기", "생각난 말을 짧게라도 적어 보거나 전해 보기"),
    "earth": ("하루를 정리해 보기", "공간이나 일정을 10분만 정돈해 보기"),
    "metal": ("기준을 세워 줄여보기", "꼭 할 일만 남기고 나머지는 미뤄 보기"),
    "water": ("숨 고르며 돌아보기", "정보와 감정을 잠깐 적고 몸을 움직여 보기"),
}
def _trait_voice(trait: str) -> dict:
    return TRAIT_VOICE.get(trait, {"noun": "성향", "adjective": "자신만의", "tone": "지금의 흐름"})


def _growth_voice(element: str) -> tuple[str, str]:
    return GROWTH_VOICE.get(element, ("작게 시도해 보기", "부담 없는 한 가지를 이어 보기"))


# 본괘 id → 사용자-facing 국면 (괘명·원문을 노출하지 않는다)
SITUATION_BY_HEXAGRAM = {
    1: ("beginning_with_strength", "힘이 모이기 시작하는 흐름"),
    2: ("holding_and_receiving", "받아들이며 자리를 잡는 흐름"),
    3: ("starting_with_friction", "시작과 함께 막힘이 있는 흐름"),
    4: ("learning_in_fog", "아직 안개가 걷히지 않은 배움의 흐름"),
    5: ("waiting_with_patience", "결과를 기다리며 숨을 고르는 흐름"),
    6: ("tension_in_words", "말과 입장 사이에 긴장이 있는 흐름"),
    7: ("organizing_effort", "힘을 모아 정돈하는 흐름"),
    8: ("seeking_alliance", "곁을 찾고 연결을 확인하는 흐름"),
    9: ("small_accumulation", "작은 힘이 조금씩 쌓이는 흐름"),
    10: ("careful_steps", "발걸음을 조심히 옮기는 흐름"),
    11: ("opening_and_ease", "막혔던 길이 열리는 흐름"),
    12: ("blocked_exchange", "주고받음이 막혀 있는 흐름"),
    13: ("shared_purpose", "같은 방향을 찾는 흐름"),
    14: ("holding_plenty", "가진 것을 다루는 흐름"),
    15: ("staying_modest", "낮추고 균형 잡는 흐름"),
    16: ("rising_excitement", "기대가 커지는 흐름"),
    17: ("following_a_lead", "흐름을 따라가 보는 시기"),
    18: ("repairing_decay", "오래된 것을 손보는 흐름"),
    19: ("approaching_change", "변화가 가까이 온 흐름"),
    20: ("watching_quietly", "한 발 물러나 바라보는 흐름"),
    21: ("biting_through", "막힌 것을 끊어내는 흐름"),
    22: ("surface_and_form", "겉모습이 눈에 띄는 흐름"),
    23: ("peeling_away", "불필요한 것이 떨어져 나가는 흐름"),
    24: ("returning_inward", "다시 중심으로 돌아오는 흐름"),
    25: ("unforced_honesty", "꾸미지 않고 가는 흐름"),
    26: ("holding_back_power", "힘을 아끼며 모으는 흐름"),
    27: ("nourishing_well", "무엇을 먹이고 키울지 보는 흐름"),
    28: ("too_much_weight", "감당이 커진 흐름"),
    29: ("repeating_depth", "같은 깊이를 반복해서 지나가는 흐름"),
    30: ("holding_the_light", "밝음을 붙들고 가는 흐름"),
    31: ("feeling_drawn", "마음이 끌리는 흐름"),
    32: ("staying_the_course", "오래 이어가려는 흐름"),
    33: ("stepping_back", "한 걸음 물러서는 흐름"),
    34: ("great_strength", "힘이 크게 드러나는 흐름"),
    35: ("moving_forward", "앞으로 나아가는 흐름"),
    36: ("hiding_the_light", "빛을 잠시 감추는 흐름"),
    37: ("home_and_roles", "가까운 관계의 역할이 드러나는 흐름"),
    38: ("seeing_apart", "서로 다르게 보는 흐름"),
    39: ("meeting_obstacle", "장애를 마주한 흐름"),
    40: ("releasing_tension", "묶였던 것이 풀리는 흐름"),
    41: ("reducing_load", "덜어내며 가벼워지는 흐름"),
    42: ("adding_support", "보탬이 생기는 흐름"),
    43: ("decisive_break", "결정을 내야 하는 흐름"),
    44: ("unexpected_encounter", "예상 밖 만남이 있는 흐름"),
    45: ("gathering_together", "사람들이 모이는 흐름"),
    46: ("slow_ascent", "천천히 올라가는 흐름"),
    47: ("feeling_constrained", "숨이 막히는 듯한 흐름"),
    48: ("drawing_from_well", "이미 있는 우물에서 길어 올리는 흐름"),
    49: ("shedding_old_skin", "낡은 껍질을 벗는 흐름"),
    50: ("transforming_vessel", "담긴 것이 바뀌는 흐름"),
    51: ("sudden_shock", "갑자기 흔들리는 흐름"),
    52: ("keeping_still", "멈추고 자리를 지키는 흐름"),
    53: ("gradual_progress", "조금씩 자리를 잡는 흐름"),
    54: ("uneven_beginning", "시작의 조건이 고르지 않은 흐름"),
    55: ("fullness_now", "지금이 가장 가득 찬 흐름"),
    56: ("traveling_light", "잠시 머물며 지나가는 흐름"),
    57: ("gentle_penetration", "부드럽게 스며드는 흐름"),
    58: ("open_exchange", "마음이 열리는 흐름"),
    59: ("dispersing_knots", "뭉친 것이 흩어지는 흐름"),
    60: ("setting_limits", "경계를 분명히 하는 흐름"),
    61: ("inner_sincerity", "안쪽의 진심이 드러나는 흐름"),
    62: ("small_excess", "작은 일에 힘이 쏠리는 흐름"),
    63: ("after_completion", "일단 끝난 뒤의 흐름"),
    64: ("before_completion", "아직 끝나지 않은 흐름"),
}


def map_to_trait_candidates(analysis: dict) -> list[dict]:
    """오행 균형·일간 강약을 Phase 1 trait 풀로 매핑한 저신뢰 초기 가설.

    방향/값은 엔진 계산값 그대로 두고, 사용자 노출 전에 value는 0.05~0.95로
    clamp하며 confidence는 birth_hypothesis(가장 낮은 우선순위 소스) 한도로 낮춘다.
    """
    balance = analysis["element_balance"]
    strength = analysis["day_master_strength"]
    candidates = []

    def add(trait: str, direction: str, value: float, confidence: float, reason_refs: list[str]) -> None:
        candidates.append(
            {
                "trait": trait,
                "direction": direction,
                "strength": round(max(0.05, min(0.95, value)), 3),
                "confidence": round(max(0.05, min(0.4, confidence)), 3),
                "source": "birth_hypothesis",
                "reason_refs": reason_refs,
                "status": "hypothesis",
            }
        )

    dominant = balance["dominant"]
    deficient = balance["deficient"]
    add(TRAIT_BY_ELEMENT[dominant], "high", balance["ratio"][dominant], 0.25, ["element_balance"])
    add(TRAIT_BY_ELEMENT[deficient], "low", balance["ratio"][deficient], 0.25, ["element_balance", "growth_direction"])
    verdict = strength["verdict"]
    if verdict == "shingang":
        add("persistence", "high", strength["score"], strength["confidence"], ["day_master_strength"])
    elif verdict == "shinyak":
        add("recovery", "high", strength["score"], strength["confidence"], ["day_master_strength"])
    else:
        add("connection", "high", strength["score"], strength["confidence"], ["day_master_strength"])

    merged: dict[str, dict] = {}
    for candidate in candidates:
        trait = candidate["trait"]
        if trait not in merged or candidate["strength"] > merged[trait]["strength"]:
            merged[trait] = candidate
    return list(merged.values())


def canonical_character_profile(
    analysis: dict,
    profile_version_id: str,
    gender: str | None = None,
    recorded_days: int = 0,
    condition_state: str = "steady",
) -> dict:
    """엔진 분석은 사람마다 다르다. 일상어 시각 스펙으로만 노출하고, 같은 키면 다시 그리지 않는다.

    기록일수(recorded_days)가 많을수록 성장 단계(stage 1~10)가 올라간다.
    카탈로그가 준비되면 생성 없이 정적 이미지를 쓴다.
    """
    spec = character_visual.build_character_visual(analysis, gender, recorded_days, condition_state)
    generated = character_visual.generate_character_image(spec)
    return {
        "character_profile_id": f"cp_{uuid.uuid4().hex[:8]}",
        "profile_version_id": profile_version_id,
        "day_stem": spec["tone"],
        "representative_element": spec["element"],
        "guardian_beast": {
            "code": spec["code"],
            "label_ko": spec["label_ko"],
            "source": "day_stem_element",
        },
        "visual_key": spec["visual_key"],
        "catalog_key": spec.get("catalog_key"),
        "state_catalog_key": spec.get("state_catalog_key"),
        "stage": spec.get("stage", 1),
        "stage_name": spec.get("stage_name", "처음"),
        "condition_state": condition_state,
        "condition_label": character_state.STATE_LABELS.get(condition_state, character_state.STATE_LABELS["steady"]),
        "appearance_seed": character_state.appearance_seed(
            profile_version_id, profile_version_id, spec.get("stage", 1), condition_state
        ),
        "image_url": generated["image_url"],
        "image_gif_url": generated.get("image_gif_url") or generated["image_url"],
        "image_status": generated["status"],
        "user_editable": True,
        "status": "active",
    }


def canonical_traits(candidates: list[dict]) -> list[dict]:
    return [
        {
            "trait": candidate["trait"],
            "label_ko": _trait_voice(candidate["trait"])["noun"],
            "value": candidate["strength"],
            "confidence": candidate["confidence"],
            "source_counts": {"birth_hypothesis": 1},
        }
        for candidate in candidates
    ]


def build_identity_sentence(analysis: dict) -> str:
    day = analysis["day_master_strength"]["day_master"]
    character = character_visual.character_voice(day["element"])
    theme, _ = _growth_voice((analysis.get("growth_direction") or {}).get("deficient_element") or "earth")
    return (
        f"지금은 {character['tone']} 쪽으로 읽히는 초기 가설이에요. "
        f"기록이 쌓이면 '{theme}' 방향이 더 선명해져요."
    )


def build_strengths(analysis: dict, birth: dict) -> list[str]:
    balance = analysis["element_balance"]
    strength = analysis["day_master_strength"]
    dominant_voice = _trait_voice(TRAIT_BY_ELEMENT[balance["dominant"]])
    verdict = STRENGTH_VOICE.get(strength.get("verdict"), "에너지가 오가는 방식이 조금씩 보이는 편")
    theme, _ = _growth_voice((analysis.get("growth_direction") or {}).get("deficient_element") or "earth")
    return [
        f"{dominant_voice['tone']}이 가장 두드러지는 편이에요 (초기 가설)",
        f"{verdict}이에요 (초기 가설)",
        f"지금은 '{theme}' 쪽이 성장 포인트로 보여요",
    ]


def build_watch_patterns(analysis: dict, birth: dict) -> list[str]:
    growth = analysis["growth_direction"]
    deficient = growth.get("deficient_element")
    dominant = growth.get("dominant_element")
    patterns = []
    if deficient == "metal":
        patterns.append("판단이 날카로워질 때는 말투를 한 톤 부드럽게 바꿔보기")
    elif deficient == "wood":
        patterns.append("계획만 쌓이지 않게, 작은 실행까지 연결해 보기")
    elif deficient == "fire":
        patterns.append("마음이 달아오르면 잠깐 쉬고 수면을 먼저 챙기기")
    elif deficient == "earth":
        patterns.append("완벽보다, 매일 반복할 수 있는 작은 기준을 두기")
    elif deficient == "water":
        patterns.append("생각이 깊어질수록 몸을 움직여 순환시키기")
    else:
        patterns.append("한쪽으로 쏠릴 때 반대쪽을 의식적으로 채워보기")
    if dominant == "water":
        patterns.append("생각이 많아지면 몸을 움직여 순환시키기")
    elif dominant == "fire":
        patterns.append("열정이 과해지면 휴식과 수면으로 균형 잡기")
    elif dominant == "wood":
        patterns.append("새 시작이 많아지면 하나를 끝까지 남겨보기")
    elif dominant == "metal":
        patterns.append("기준이 날카로워지면 표현을 부드럽게 다듬기")
    elif dominant == "earth":
        patterns.append("안정을 지키려다 변화가 막히지 않게 보기")
    if birth.get("time_precision") != "exact" or not birth.get("time"):
        patterns.append("태어난 시간을 몰라서, 지금 보이는 건 아주 느슨한 가설이에요")
    return patterns[:3]


def build_growth_theme(analysis: dict) -> str:
    theme, _ = _growth_voice((analysis.get("growth_direction") or {}).get("deficient_element") or "earth")
    return theme


PUBLIC_PROFILE_KEYS = living.PUBLIC_PROFILE_KEYS
public_profile = living.public_profile


@app.get("/healthz")
def healthz():
    driver = type(store).__name__.replace("Store", "").lower()
    return {"status": "ok", "service": "nabom-api", "store_driver": driver, "profile_count": store.count("profiles"), "mirror_count": store.count("mirrors")}


@app.post("/api/v1/living/profiles/initial")
async def create_initial_profile(
    payload: InitialProfileRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    request_id = _request_id(x_request_id)
    user = _consent_check(x_user_id, None, "self", authenticated_identity=user_id)
    birth = payload.birth_input.model_dump()
    if birth["location"] is None:
        birth["location"] = {"timezone": "Asia/Seoul"}

    async def _build():
        engine = await call_saju_chart(birth, "strict", request_id)
        analysis = engine["element_analysis"]
        profile_id = f"pv_{uuid.uuid4().hex[:8]}"
        trait_candidates = map_to_trait_candidates(analysis)
        created_at = datetime.now(tz=timezone.utc).isoformat()
        profile = {
            "profile_version_id": profile_id,
            "number": 1,
            "created_at": created_at,
            "identity_sentence": build_identity_sentence(analysis),
            "traits": canonical_traits(trait_candidates),
            "strengths": build_strengths(analysis, birth),
            "watch_patterns": build_watch_patterns(analysis, birth),
            "growth_theme": build_growth_theme(analysis),
            "lenses": profile_lenses.build_lenses(analysis),
            "evidence_cutoff": birth["date"],
            "character_profile": canonical_character_profile(analysis, profile_id, birth.get("gender"), recorded_days=0),
            "trait_candidates": trait_candidates,
            "growth_direction": analysis["growth_direction"],
            "use_god_candidates": analysis["use_god_candidates"],
            "precision": engine["quality"],
            "narrative": engine.get("narrative", {}),
            "analysis": analysis,  # 감사용 raw — public 응답에서는 제외
            "birth_input": birth,
        }
        store.set("profiles", profile_id, {"user_id": user, "profile": profile})
        return {"profile_version_id": profile_id, "profile": public_profile(profile), "request_id": request_id}

    return await _facade_idempotency(idempotency_key, user, payload.model_dump_json(), _build)


@app.post("/api/v1/living/profiles/refresh")
async def refresh_profile(
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """기록이 충분히 쌓이면 evidence 기반 새 ProfileVersion(002, 003, ...)을 만든다.

    설계 §8: Monthly/충분한 Evidence → Profile Update Proposal → 새 ProfileVersion.
    character_profile의 visual_key가 바뀌면 새 캐릭터 이미지를 생성한다.
    """
    request_id = _request_id(x_request_id)
    user = _consent_check(x_user_id, None, "self", authenticated_identity=user_id)

    records = [
        record
        for record in store.list("profiles")
        if record.get("user_id") == user and record.get("status") != "deleted"
    ]
    if not records:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "no profile yet", "retryable": False})
    latest_record = max(records, key=lambda record: (record.get("profile") or {}).get("number", 0))
    latest = dict(latest_record["profile"])

    evidence = [
        item
        for item in store.list("evidence")
        if item.get("user_id") == user and item.get("status") in {None, "active"}
    ]
    entries = [
        item
        for item in store.list("daily_entries")
        if item.get("user_id") == user and item.get("status") in {None, "active"}
    ]
    journals = [
        item
        for item in store.list("journals")
        if item.get("user_id") == user and item.get("status") in {None, "active"}
    ]
    recorded_days = {item["date"] for item in entries} | {item["date"] for item in journals}
    previous_condition = (latest.get("character_profile") or {}).get("condition_state")
    current_condition = character_state.derive_condition_state(
        entries,
        journals,
        evidence,
        previous_state=previous_condition,
    )

    record_count = len(entries) + len(journals)
    if not profile_refresh.should_propose_refresh(len(recorded_days), record_count):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "INSUFFICIENT_EVIDENCE",
                "message": f"아직 기록이 충분하지 않아요. 최소 28일 동안의 기록이 필요해요. (현재 {len(recorded_days)}일 / {record_count}건)",
                "retryable": False,
            },
        )

    async def _build():
        analysis = latest.get("analysis") or {}
        birth = latest.get("birth_input") or {}
        refreshed = profile_refresh.refresh_candidates(analysis, latest.get("trait_candidates") or [], entries, journals)
        next_number = int(latest.get("number") or 1) + 1
        profile_id = profile_refresh.new_profile_version_id()
        created_at = profile_refresh.utcnow()
        # 캐릭터: 기록일수가 많아지면 성장 단계가 올라가 카탈로그 이미지가 바뀐다.
        character_profile = canonical_character_profile(
            analysis,
            profile_id,
            birth.get("gender"),
            recorded_days=len(recorded_days),
            condition_state=current_condition["state"],
        )
        profile = {
            "profile_version_id": profile_id,
            "number": next_number,
            "created_at": created_at,
            "identity_sentence": build_identity_sentence(analysis),
            "traits": canonical_traits(refreshed),
            "strengths": build_strengths(analysis, birth),
            "watch_patterns": build_watch_patterns(analysis, birth),
            "growth_theme": build_growth_theme(analysis),
            "lenses": profile_lenses.build_lenses(analysis),
            "evidence_cutoff": created_at[:10],
            "character_profile": character_profile,
            "trait_candidates": refreshed,
            "growth_direction": analysis.get("growth_direction", {}),
            "use_god_candidates": analysis.get("use_god_candidates", {}),
            "precision": latest.get("precision"),
            "narrative": latest.get("narrative", {}),
            "analysis": analysis,
            "birth_input": birth,
            "refresh": {
                "recorded_days": len(recorded_days),
                "evidence_count": len(evidence),
                "condition_state": current_condition["state"],
                "source": "evidence_blend",
                "previous_version": latest["profile_version_id"],
            },
        }
        store.set("profiles", profile_id, {"user_id": user, "profile": profile})
        return {
            "profile_version_id": profile_id,
            "profile": public_profile(profile),
            "refresh": profile["refresh"],
            "request_id": request_id,
        }

    # refresh는 body가 없으므로 fingerprint는 상수다. 같은 Idempotency-Key면
    # 첫 응답을 재사용한다 (최신 version이 바뀌어도 동일 키 = 동일 요청).
    return await _facade_idempotency(idempotency_key, user, "refresh", _build)


@app.post("/api/v1/living/reflections")
async def create_reflection(
    payload: ReflectionRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    request_id = _request_id(x_request_id)
    user = _consent_check(x_user_id, None, "self", authenticated_identity=user_id)
    entries = [item for item in store.list("daily_entries") if item.get("user_id") == user]
    journals = [item for item in store.list("journals") if item.get("user_id") == user]
    evidence = [item for item in store.list("evidence") if item.get("user_id") == user]
    try:
        mirror = living.build_weekly_mirror(
            user,
            period_from=payload.period_from,
            period_to=payload.period_to,
            timezone=payload.timezone,
            entries=entries,
            journals=journals,
            evidence=evidence,
            previous=_previous_mirror_record(user, payload.period_from),
        )
        ctx = living.stored_reflection_context(
            period_from=payload.period_from,
            period_to=payload.period_to,
            timezone=payload.timezone,
            entries=entries,
            journals=journals,
            evidence=evidence,
        )
    except living.LivingRecordError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": str(exc), "retryable": False}) from exc

    async def _build():
        engine = await call_iching_reflection(ctx, request_id)
        reflection = build_canonical_reflection(engine, mirror, ctx["evidence_refs"], request_id)
        jsonschema.validate(reflection, REFLECTION_SCHEMA)
        store.set("weekly_mirrors", mirror["mirror_id"], mirror)
        store_experiments_from_mirror(user, mirror)
        store.set(
            "mirrors",
            reflection["reflection_id"],
            {
                "user_id": user,
                "reflection": reflection,
                "period": {"from": payload.period_from, "to": payload.period_to},
                "mirror_id": mirror["mirror_id"],
                "status": "active",
                "created_at": mirror["generated_at"],
                "audit": {
                    "resolver_version": engine["resolver"]["version"],
                    "resolver_input_hash": engine["resolver"].get("input_hash"),
                    "cast_mapping_version": engine["resolver"]["version"],
                    "raw_reading_internal_ref": engine.get("raw_reading_internal_ref"),
                    "classical_source_refs": engine.get("source_refs", []),
                    "generated_at": mirror["generated_at"],
                },
            },
        )
        store.set(
            "reflections_by_period",
            f"{user}:{payload.period_from}:{payload.period_to}",
            {"reflection_id": reflection["reflection_id"], "mirror_id": mirror["mirror_id"]},
        )
        _queue_weekly_mirror_notification(user)
        return {
            "mirror": living.public_weekly_mirror(mirror),
            "reflection": _public_reflection(reflection),
            "request_id": request_id,
        }

    return await _facade_idempotency(idempotency_key, user, payload.model_dump_json(), _build)


def _queue_weekly_mirror_notification(user_id: str) -> None:
    """주간 회고 준비 알림을 큐에 기록한다 (메일 발송은 mailer 게이트)."""
    import mailer

    account = store.get("accounts", user_id)
    if not account:
        return
    import secrets as _secrets

    notification_id = f"nt_{_secrets.token_hex(6)}"
    notification = {
        "notification_id": notification_id,
        "user_id": user_id,
        "kind": "weekly_mirror_ready",
        "channel": "email",
        "payload": {},
        "status": "queued",
        "created_at": profile_refresh.utcnow(),
    }
    store.set("notifications", notification_id, notification)
    try:
        if mailer.mail_enabled():
            mailer.send_weekly_mirror_ready_mail(account.get("email", ""), account.get("nickname") or "")
            notification["status"] = "sent"
        else:
            notification["status"] = "queued"
        store.set("notifications", notification_id, notification)
    except Exception:  # noqa: BLE001
        notification["status"] = "queued"
        store.set("notifications", notification_id, notification)


def _previous_mirror_record(user_id: str, period_from: str) -> dict | None:
    candidates = [
        item
        for item in store.list("weekly_mirrors")
        if item.get("user_id") == user_id
        and item.get("status") == "active"
        and str(item.get("generated_at", ""))[:10] < str(period_from)[:10]
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: str(item.get("generated_at", "")))


def _everyday_lens(raw_lens: str) -> str:
    """Vault 주제별 해석 렌즈를 사용자-facing 일상어로 정제한다.

    렌즈 데이터는 "괘명(卦名, N) — 일상어 해석" 형태가 기준이지만,
    일부 괘는 "—" 뒤에 고전 원문(彖傳·大象·한문)이 이어진다. 규칙:
    - 괘명 프리픽스("—" 앞)는 항상 제거
    - 한문(U+4E00~U+9FFF)이 남으면 사용자 노출 금지 → 빈 문자열
    - 80자 초과는 고전 원문/장문으로 보고 노출 금지
    - "·", "-" 분리 후 괘명만 남은 경우도 빈 문자열
    """
    import re

    text = (raw_lens or "").strip()
    for sep in ("—", "-", "·"):
        if sep in text:
            _, _, rest = text.partition(sep)
            text = rest.strip()
            break
    if not text:
        return ""
    if len(text) > 80:
        # 장문은 첫 문장까지만 취한다. 여전히 길면(첫 문장도 80자+) 노출 금지.
        first_sentence = re.split(r"(?<=[.!?])\s+", text)[0].strip()
        if len(first_sentence) <= 80:
            text = first_sentence
        else:
            return ""
    if re.search(r"[\u4e00-\u9fff]", text):
        return ""
    # 괘명 한자/영문 코드 잔여물 검사
    if re.search(r"[\u4e00-\u9fff]|^[0-9]+[괘]?$", text):
        return ""
    return text


def build_canonical_reflection(engine: dict, mirror: dict, evidence_refs: list[str], request_id: str) -> dict:
    """주역 raw 괘를 사용자-facing Canonical Reflection으로 변환한다.

    raw 괘 데이터(judgment_text/name_zh 등)는 외부에 노출하지 않는다.
    현재 국면·관찰 초점·조심 신호·단일 가역 행동만 구조화해 반환한다.
    """
    primary = engine["primary_hexagram"]
    coverage = mirror.get("coverage") or {}
    days = int(coverage.get("days_recorded") or 0)
    mode = coverage.get("mode") or "light"
    metrics = mirror.get("metrics") or {}
    hexagram_id = primary.get("hexagram_id")
    try:
        hexagram_id = int(hexagram_id)
    except (TypeError, ValueError):
        hexagram_id = None
    situation_code, situation_label = SITUATION_BY_HEXAGRAM.get(
        hexagram_id, ("shifting_current", "변화의 흐름")
    )
    situation = {
        "code": situation_code,
        "label_ko": situation_label,
        "confidence": round(min(0.8, 0.4 + 0.06 * days), 2),
    }
    # Vault 주제별 해석(05_주제별_해석) 렌즈를 일상어로 노출한다.
    # 괘명·고전 원문·한문이 섞인 렌즈는 걸러내고 일상어 해석만 남긴다.
    engine_themes = engine.get("themes") or []
    if engine_themes:
        lens_text = _everyday_lens(engine_themes[0].get("lens") or "")
        if lens_text:
            situation["theme_topic"] = engine_themes[0].get("topic") or ""
            situation["theme_lens"] = lens_text
    if mode == "light":
        observation_focus = [
            "감정 변화를 하루 한 번 짧게 남겨보기",
            "에너지가 오르내리는 순간을 관찰하기",
        ]
    else:
        observation_focus = ["변화가 시작되는 순간의 첫 반응을 관찰하기"]
        avg_mood = metrics.get("average_mood")
        avg_energy = metrics.get("average_energy")
        if avg_mood is not None and avg_mood <= 2.5:
            observation_focus.append("기분이 낮았던 날에 무엇이 있었는지 살펴보기")
        if avg_energy is not None and avg_energy >= 3.5:
            observation_focus.append("에너지가 높았던 날의 공통점을 기록으로 남겨보기")
    caution_signals = []
    if mode != "full":
        caution_signals.append("기록이 적은 주라 한 주 전체를 단정하지 않기")
    caution_signals.append("여러 일을 동시에 시작하면 에너지가 분산될 수 있어요")
    experiment = mirror.get("growth_experiment")
    if experiment:
        recommended_action = {
            "title": experiment["title"],
            "instruction": experiment["instruction"],
            "success_condition": experiment["success_condition"],
            "reversible": True,
        }
    else:
        recommended_action = {
            "title": "하루 한 번, 감정 한 줄 적기",
            "instruction": "하루를 마무리하며 오늘 느낀 감정을 한 줄로 남깁니다.",
            "success_condition": "7일 안에 3회 이상 기록",
            "reversible": True,
        }
    return {
        "reflection_id": f"rf_{uuid.uuid4().hex[:8]}",
        "mode": "record_reflection",
        "resolver_version": engine["resolver"]["version"],
        "resolver_input_hash": engine["resolver"].get("input_hash"),
        "situation": situation,
        "observation_focus": observation_focus,
        "caution_signals": caution_signals,
        "recommended_action": recommended_action,
        "evidence_refs": evidence_refs,
        "request_id": request_id,
    }


def _ensure_character_gif(profile: dict) -> dict:
    """저장된 프로필의 캐릭터에 GIF가 없으면 생성해서 채운다 (기존 프로필 보강)."""
    cp = profile.get("character_profile") or {}
    if not cp or not cp.get("visual_key"):
        return profile
    condition_state = (profile.get("refresh") or {}).get("condition_state") or cp.get("condition_state") or "steady"
    # 카탈로그 자산이 준비됐다면 레거시 visual_key PNG를 catalog로 업그레이드한다.
    # catalog_key가 없거나 image_url이 아직 레거시 경로면 재해석한다.
    legacy_image = not str(cp.get("image_url") or "").startswith("/characters/stage/")
    needs_upgrade = not cp.get("catalog_key") or legacy_image
    if cp.get("image_gif_url") and not needs_upgrade:
        cp = dict(cp)
        cp["condition_state"] = condition_state
        cp["condition_label"] = character_state.STATE_LABELS.get(
            condition_state, character_state.STATE_LABELS["steady"]
        )
        profile["character_profile"] = cp
        return profile
    try:
        analysis = profile.get("analysis") or {}
        birth = profile.get("birth_input") or {}
        # 기록일수는 프로필의 recorded_days 혹은 기본 0 (기존 저장 프로필 보강)
        recorded_days = int((profile.get("refresh") or {}).get("recorded_days") or 0)
        spec = character_visual.build_character_visual(
            analysis, birth.get("gender"), recorded_days, condition_state
        )
        if spec["visual_key"] != cp["visual_key"]:
            return profile  # 키가 다르면 저장 시점 스펙과 불일치 — 건드리지 않는다
        generated = character_visual.generate_character_image(spec)
        cp = dict(cp)
        cp["image_url"] = generated.get("image_url") or cp.get("image_url")
        cp["image_gif_url"] = generated.get("image_gif_url") or cp.get("image_url")
        cp["catalog_key"] = spec.get("catalog_key")
        cp["state_catalog_key"] = spec.get("state_catalog_key")
        cp["stage"] = spec.get("stage", cp.get("stage", 1))
        cp["stage_name"] = spec.get("stage_name", cp.get("stage_name", "처음"))
        cp["condition_state"] = condition_state
        cp["condition_label"] = character_state.STATE_LABELS.get(
            condition_state, character_state.STATE_LABELS["steady"]
        )
        profile["character_profile"] = cp
    except (ValueError, KeyError):
        return profile
    return profile


def _active_traits(profile: dict, user_id: str):
    """거절(incorrect)된 가설을 활성 Trait 후보에서 제외한다. 거절 이력은 보존한다."""
    feedbacks = store.get("feedback", f"{user_id}:{profile['profile_version_id']}") or []
    rejected = {fb.get("target_key") for fb in feedbacks if fb.get("rating") == "incorrect"}
    return [c for c in profile["trait_candidates"] if c["trait"] not in rejected]


@app.get("/api/v1/living/profiles")
async def list_profiles(
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
):
    user = _consent_check(x_user_id, None, "self", authenticated_identity=user_id)
    items = []
    for record in store.list("profiles"):
        if record.get("user_id") != user or record.get("status") == "deleted":
            continue
        profile = dict(record.get("profile") or {})
        if profile.get("trait_candidates"):
            profile["trait_candidates"] = _active_traits(profile, user)
        profile = _ensure_character_gif(profile)
        items.append({"profile_version_id": profile.get("profile_version_id"), "profile": public_profile(profile)})
    return {"profiles": items}


@app.get("/api/v1/living/profiles/current")
async def get_current_profile(
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
):
    user = _consent_check(x_user_id, None, "self", authenticated_identity=user_id)
    records = [
        record
        for record in store.list("profiles")
        if record.get("user_id") == user and record.get("status") != "deleted"
    ]
    if not records:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "no profile yet", "retryable": False})
    latest = max(records, key=lambda record: (record.get("profile") or {}).get("number", 0))
    profile = dict(latest["profile"])
    profile["trait_candidates"] = _active_traits(profile, user)
    profile = _ensure_character_gif(profile)
    profile = public_profile(profile)
    return {
        "profile_version_id": profile["profile_version_id"],
        "profile": profile,
        "character_profile": profile.get("character_profile"),
    }


@app.get("/api/v1/living/profiles/{profile_id}")
async def get_profile(
    profile_id: str,
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
):
    user = _consent_check(x_user_id, None, "self", authenticated_identity=user_id)
    record = store.get("profiles", profile_id)
    if not record or record["user_id"] != user or record.get("status") == "deleted":
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "profile not found", "retryable": False})
    profile = dict(record["profile"])
    profile["trait_candidates"] = _active_traits(profile, user)
    profile = _ensure_character_gif(profile)
    return {"profile_version_id": profile_id, "profile": public_profile(profile)}


@app.get("/api/v1/living/profiles/{profile_id}/feedback")
async def list_profile_feedback(
    profile_id: str,
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
):
    user = _consent_check(x_user_id, None, "self", authenticated_identity=user_id)
    record = store.get("profiles", profile_id)
    if not record or record["user_id"] != user or record.get("status") == "deleted":
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "profile not found", "retryable": False})
    return {"profile_version_id": profile_id, "feedback": store.get("feedback", f"{user}:{profile_id}") or []}


@app.post("/api/v1/living/profiles/{profile_id}/feedback")
async def create_profile_feedback(
    profile_id: str,
    payload: ProfileFeedbackRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
):
    user = _consent_check(x_user_id, None, "self", authenticated_identity=user_id)
    record = store.get("profiles", profile_id)
    if not record or record["user_id"] != user or record.get("status") == "deleted":
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "profile not found", "retryable": False})
    if payload.rating not in {"correct", "mostly_correct", "situational", "unsure", "incorrect"}:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "rating must be correct|mostly_correct|situational|unsure|incorrect", "retryable": False})
    if payload.target_type not in {"trait", "overall"}:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "target_type must be trait|overall", "retryable": False})
    if payload.target_type == "trait" and payload.target_key not in PHASE1_TRAIT_POOL:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "unknown trait key", "retryable": False})
    feedback = {
        "feedback_id": f"pf_{uuid.uuid4().hex[:8]}",
        "profile_version_id": profile_id,
        "target_type": payload.target_type,
        "target_key": payload.target_key,
        "rating": payload.rating,
        "comment": payload.comment,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    key = f"{user}:{profile_id}"
    existing = store.get("feedback", key) or []
    store.set("feedback", key, existing + [feedback])
    return {"profile_version_id": profile_id, "feedback": feedback}


@app.post("/api/v1/living/luck")
async def create_luck_outlook(
    payload: InitialProfileRequest,
    year: int,
    month: int | None = None,
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
):
    request_id = _request_id(x_request_id)
    _consent_check(x_user_id, None, "self", authenticated_identity=user_id)
    birth = payload.birth_input.model_dump()
    if birth["location"] is None:
        birth["location"] = {"timezone": "Asia/Seoul"}
    engine = await call_saju_luck(birth, year, month, request_id)
    outlook = engine["luck_outlook"]
    # 사용자-facing: 대운은 기존 계약 그대로, 연운/월운은 canonical 요약으로
    return {
        "annual": outlook["annual"],
        "monthly": outlook["monthly"],
        "decade": {
            "start_age_years": outlook["decade"].get("start_age_years"),
            "direction": outlook["decade"].get("direction"),
            "cycles": [{"start_age_years": c["start_age_years"], "pillar_ko": c["pillar"]["ko"], "pillar_hanja": c["pillar"]["hanja"]} for c in outlook["decade"].get("decade_cycles", [])[:10]],
        },
        "policy": outlook["policy"],
        "request_id": request_id,
    }


_HANJA_RE = re.compile(r"[\u4e00-\u9fff]")


def _strip_hanja(value: str) -> str:
    """사용자-facing 문자열에서 한자(U+4E00~9FFF)를 제거한다.

    실패 시 빈 문자열 대신 '…'로 남겨 문장 흐름이 끊기지 않게 한다.
    """
    return _HANJA_RE.sub("…", value or "")


def _public_reflection(reflection: dict) -> dict:
    """사용자-facing 회고. 괘 코드·내부 해시·한자는 노출하지 않는다.

    저장본에는 감사용으로 code/resolver_input_hash를 유지하고,
    응답에서는 label_ko(일상어) 중심으로만 남긴다.
    """
    public = dict(reflection)
    situation = dict(public.get("situation") or {})
    situation.pop("code", None)
    for key in ("label_ko", "theme_topic", "theme_lens"):
        if isinstance(situation.get(key), str):
            situation[key] = _strip_hanja(situation[key])
    public["situation"] = situation
    public.pop("resolver_input_hash", None)
    return public


@app.get("/api/v1/living/reflections/latest")
async def get_latest_reflection(
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
):
    user = _consent_check(x_user_id, None, "self", authenticated_identity=user_id)
    records = [
        record
        for record in store.list("mirrors")
        if record.get("user_id") == user
        and record.get("status") == "active"
        and (record.get("reflection") or {}).get("mode") == "record_reflection"
    ]
    if not records:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "no reflection yet", "retryable": False})
    latest = max(records, key=lambda record: str(record.get("created_at") or ""))
    mirror = None
    period = latest.get("period") or {}
    link = store.get("reflections_by_period", f"{user}:{period.get('from')}:{period.get('to')}")
    if link and link.get("mirror_id"):
        mirror_record = store.get("weekly_mirrors", link["mirror_id"])
        if mirror_record and mirror_record.get("user_id") == user and mirror_record.get("status") == "active":
            mirror = living.public_weekly_mirror(mirror_record)
    return {
        "reflection": _public_reflection(latest["reflection"]),
        "mirror": mirror,
        "request_id": _request_id(None),
    }


@app.get("/api/v1/living/journey")
async def get_journey(
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
):
    user = _consent_check(x_user_id, None, "self", authenticated_identity=user_id)
    profiles = []
    for record in store.list("profiles"):
        if record.get("user_id") != user or record.get("status") == "deleted":
            continue
        profile = dict(record.get("profile") or {})
        profile["trait_candidates"] = _active_traits(profile, user)
        profiles.append(public_profile(profile))
    profiles.sort(key=lambda profile: profile.get("number", 0))
    entry_dates = {
        item["date"]
        for item in store.list("daily_entries")
        if item.get("user_id") == user and item.get("status") != "deleted"
    }
    journal_dates = {
        item["date"]
        for item in store.list("journals")
        if item.get("user_id") == user and item.get("status") != "deleted"
    }
    recorded_days = entry_dates | journal_dates
    first_profile = profiles[0] if profiles else None
    return {
        "profiles": profiles,
        "summary": {
            "profile_count": len(profiles),
            "recorded_days": len(recorded_days),
            "first_profile_at": first_profile.get("created_at") if first_profile else None,
            "long_term_ready": len(recorded_days) >= 28,
            "note": "4주 이상의 기록이 쌓이면 장기 변화 요약이 가능해집니다.",
        },
        "request_id": _request_id(None),
    }


@app.delete("/api/v1/account")
async def delete_account(
    user_id: str = Depends(auth.get_authenticated_identity),
    x_user_id: str | None = Header(default=None),
):
    user = _consent_check(x_user_id, None, "self", authenticated_identity=user_id)
    result = delete_account_records(user)
    account = store.get("accounts", user)
    if account:
        account["status"] = "deleted"
        account["deleted_at"] = living.local_calendar_date("UTC")
        store.set("accounts", user, account)
    for session in store.list("sessions"):
        if session.get("user_id") == user and session.get("status") == "active":
            session["status"] = "revoked"
            store.set("sessions", session["token"], session)
    return result


@app.post("/api/v1/relationships/{relationship_id}/mirror")
async def create_relationship_mirror(
    relationship_id: str,
    payload: RelationshipMirrorRequest,
    user_id: str = Depends(auth.get_authenticated_identity),
    x_request_id: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    from relations_routes import _load_relationship, resolve_mirror_from_engine

    request_id = _request_id(x_request_id)
    user = user_id
    rel = _load_relationship(relationship_id)
    if not rel:
        raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "relationship not found", "retryable": False})
    if user not in rel.participants():
        raise HTTPException(status_code=403, detail={"code": "CONSENT_REQUIRED", "message": "participant only", "retryable": False})
    if rel.state != "active":
        raise HTTPException(status_code=403, detail={"code": "CONSENT_REQUIRED", "message": "relationship is not active (bilateral consent required)", "retryable": False})
    if any("birth_hypothesis" not in rel.active_scope(uid) for uid in rel.participants()):
        raise HTTPException(status_code=403, detail={"code": "CONSENT_REQUIRED", "message": "bilateral birth hypothesis consent required", "retryable": False})

    # 관계 생성 시 저장된 양쪽 출생 입력 사용 (동의 범위만 엔진에 전달)
    user_birth = rel._birth_inputs.get(rel.initiator)
    partner_birth = rel._birth_inputs.get(rel.participant)
    if not user_birth or not partner_birth:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "birth inputs missing on relationship", "retryable": False})

    async def _build():
        engine = await call_saju_compatibility(user_birth, partner_birth, rel.context, request_id)
        mirror = resolve_mirror_from_engine(engine, rel, user_id)
        mirror["request_id"] = request_id
        store.set("mirrors", mirror["relationship_mirror_id"], {"user_id": user, "mirror": mirror})
        return mirror

    return await _facade_idempotency(idempotency_key, user, payload.model_dump_json(), _build)
