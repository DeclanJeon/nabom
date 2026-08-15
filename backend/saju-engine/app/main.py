"""NABOM Saju Engine private API service."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

ENGINE_DIR = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE_DIR))

# 기본 provider: 환경변수가 없으면 번들 provider 사용 (정밀 절기 fail-closed 정책)
DEFAULT_PROVIDER = Path(__file__).resolve().parents[1] / "data" / "solar-term-provider-naoj-1899-2101.csv"
if not os.environ.get("SAJU_SOLAR_TERM_PROVIDER_CSV") and DEFAULT_PROVIDER.exists():
    os.environ["SAJU_SOLAR_TERM_PROVIDER_CSV"] = str(DEFAULT_PROVIDER)

from manse_engine import LunarLeapMonthAmbiguous, calculate_chart, load_tables  # noqa: E402
from compatibility_engine import calculate_compatibility_from_charts  # noqa: E402
from element_analysis import analyze_chart  # noqa: E402
from luck_analysis import luck_outlook  # noqa: E402
from classical_analysis import analyze_classical  # noqa: E402
from report_copy import build_narrative  # noqa: E402

import jsonschema  # noqa: E402

_CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"


def _contract_schema(name: str):
    return json.loads((_CONTRACTS_DIR / name).read_text(encoding="utf-8"))


CHART_SCHEMA = _contract_schema("chart.schema.json")


def _validate_contract(response: dict, schema: dict, request_id: str):
    try:
        jsonschema.validate(response, schema)
    except jsonschema.ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "CONTRACT_VIOLATION", "message": f"engine response violates contract: {exc.message}", "retryable": False, "request_id": request_id},
        ) from exc

app = FastAPI(title="NABOM Saju Engine", version="1.0.0")

SERVICE_TOKEN = os.environ.get("SAJU_SERVICE_TOKEN", "")


# 프로세스 내 idempotency 캐시: key → (fingerprint, response)
_IDEMPOTENCY: dict[str, tuple[str, dict]] = {}


def _idempotency_guard(key: str | None, fingerprint_source: str, build):
    """Idempotency-Key 재전송 시 동일 응답 반환, 다른 body면 409."""
    if not key:
        return build()
    fingerprint = hashlib.sha256(f"{key}:{fingerprint_source}".encode()).hexdigest()
    if key in _IDEMPOTENCY:
        old_fp, old_response = _IDEMPOTENCY[key]
        if old_fp != fingerprint:
            raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_CONFLICT", "message": "same Idempotency-Key used with different request body", "retryable": False})
        return old_response
    response = build()
    _IDEMPOTENCY[key] = (fingerprint, response)
    return response


def _service_tokens():
    """회전 overlap 지원: SAJU_SERVICE_TOKENS(쉼표 구분) + SAJU_SERVICE_TOKEN 병합. 매 요청마다 읽는다."""
    tokens = [t for t in os.environ.get("SAJU_SERVICE_TOKENS", "").split(",") if t.strip()]
    if SERVICE_TOKEN:
        tokens.append(SERVICE_TOKEN)
    return set(tokens)


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
    is_lunar_leap_month: bool | None = None
    location: Location | None = None
    gender: str = "unknown"


class CalculationPolicy(BaseModel):
    allow_unconverted_lunar: bool = False
    quality_mode: str = "standard"  # standard | strict


class ChartRequest(BaseModel):
    birth_input: BirthInput
    calculation_policy: CalculationPolicy = CalculationPolicy()


class UserBirthInput(BaseModel):
    birth_input: BirthInput
    calculation_policy: CalculationPolicy = CalculationPolicy()


class CompatibilityRequest(BaseModel):
    user: UserBirthInput
    partner: UserBirthInput
    context: str = "friend"


def _service_token_header(authorization: str | None, x_api_key: str | None):
    tokens = _service_tokens()
    if not tokens:
        return
    provided = ""
    if authorization and authorization.startswith("Bearer "):
        provided = authorization[len("Bearer "):]
    elif x_api_key:
        provided = x_api_key
    if provided not in tokens:
        raise HTTPException(status_code=401, detail={"code": "SERVICE_UNAUTHORIZED", "message": "invalid service token", "retryable": False})


def _check_headers(request: Request, x_request_id: str | None, x_contract_version: str | None):
    if not x_request_id:
        raise HTTPException(status_code=400, detail={"code": "INVALID_INPUT", "message": "X-Request-Id is required", "retryable": False})
    if x_contract_version not in {None, "1.0"}:
        raise HTTPException(status_code=400, detail={"code": "INVALID_INPUT", "message": "unsupported X-Contract-Version", "retryable": False})


from datetime import date as _date

BIRTH_YEAR_MIN = 1900
BIRTH_YEAR_MAX = 2100


def _validate_birth_input(birth: BirthInput):
    """엔진 호출 전 fail-fast 입력 검증 (API-SPEC 입력 계약)."""
    if birth.calendar not in {"solar", "lunar"}:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "calendar must be solar or lunar", "retryable": False})
    if birth.time_precision not in {"exact", "approximate", "unknown"}:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "time_precision must be exact|approximate|unknown", "retryable": False})
    try:
        parsed = datetime.strptime(birth.date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "date must be YYYY-MM-DD and valid", "retryable": False}) from exc
    if not (BIRTH_YEAR_MIN <= parsed.year <= BIRTH_YEAR_MAX):
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": f"birth year must be {BIRTH_YEAR_MIN}-{BIRTH_YEAR_MAX}", "retryable": False})
    if parsed > _date.today():
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "birth date cannot be in the future", "retryable": False})
    if birth.time:
        for part in birth.time.split("-"):
            try:
                datetime.strptime(part.strip(), "%H:%M")
            except ValueError as exc:
                raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "time must be HH:MM or HH:MM-HH:MM", "retryable": False}) from exc
    if birth.time_precision == "unknown" and birth.time:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "unknown time_precision cannot include a clock time", "retryable": False})
    tz = birth.location.timezone if birth.location and birth.location.timezone else "Asia/Seoul"
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(tz)
    except Exception as exc:  # noqa: BLE001  (ZoneInfoNotFoundError는 KeyError 계열)
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": f"invalid timezone: {tz}", "retryable": False}) from exc


def _to_birth_kwargs(birth: BirthInput):
    loc = birth.location
    birth_time = "" if birth.time_precision == "unknown" else birth.time
    return {
        "birth_date": birth.date,
        "birth_time": birth_time,
        "gender": birth.gender,
        "birth_place": loc.label if loc else "",
        "timezone": loc.timezone if loc and loc.timezone else "Asia/Seoul",
        "calendar_type": birth.calendar,
        "allow_unconverted_lunar": False,
        "is_lunar_leap_month": birth.is_lunar_leap_month,
    }


def _engine_error(exc: Exception, request_id: str):
    if isinstance(exc, LunarLeapMonthAmbiguous):
        return {
            "code": "LUNAR_LEAP_MONTH_AMBIGUOUS",
            "message": "같은 음력 달에 평달과 윤달이 있습니다. 어느 쪽인지 골라 주세요.",
            "retryable": False,
            "request_id": request_id,
            "candidates": exc.candidates,
        }
    code = "ENGINE_UNAVAILABLE"
    retryable = True
    message = str(exc)
    if "verified solar terms required" in message:
        code, retryable = "APPROXIMATE_SOLAR_TERMS_BLOCKED", False
        message = "검증된 절기 데이터가 필요합니다. 관리자에게 문의하세요."
    elif "lunar" in message.lower():
        code, retryable = "LUNAR_CONVERSION_UNAVAILABLE", False
        message = "음력 변환을 사용할 수 없습니다."
    return {"code": code, "message": message, "retryable": retryable, "request_id": request_id}


@app.get("/healthz")
def healthz():
    return {"status": "ok", "engine": "saju", "uptime_seconds": round(time.time() - _START, 2)}


@app.get("/readyz")
def readyz():
    try:
        tables = load_tables()
        chart = calculate_chart(birth_date="1992-03-01", birth_time="07:20", gender="male", tables=tables, require_verified_solar_terms=True)
        ok = chart["precision_policy"]["level"] == "precision_open"
    except Exception as exc:  # noqa: BLE001
        return {"ready": False, "checks": {"sample_calculation": {"status": "error", "message": str(exc)}}}
    return {
        "ready": ok,
        "checks": {
            "knowledge_files": {"status": "ok"},
            "provider": {"status": "ok" if ok else "missing", "path": os.environ.get("SAJU_SOLAR_TERM_PROVIDER_CSV")},
            "sample_calculation": {"status": "ok", "precision": chart["precision_policy"]["level"]},
        },
    }


@app.post("/internal/v1/charts")
def create_chart(
    payload: ChartRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    x_contract_version: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    _service_token_header(authorization, x_api_key)
    _check_headers(request, x_request_id, x_contract_version)
    _validate_birth_input(payload.birth_input)
    request_id = x_request_id or str(uuid.uuid4())
    strict = payload.calculation_policy.quality_mode == "strict"

    def _build():
        try:
            chart = calculate_chart(
                **_to_birth_kwargs(payload.birth_input),
                tables=load_tables(),
                require_verified_solar_terms=strict,
            )
            analysis = analyze_chart(chart)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=_engine_error(exc, request_id)) from exc
        classical = analyze_classical(chart)
        narrative = build_narrative(analysis, classical)
        response = {
            "contract_version": "saju-chart-v1",
            "engine_version": chart["engine_metadata"]["engine_version"],
            "chart": chart,
            "character_profile": {},
            "element_analysis": analysis,
            "narrative": narrative,
            "quality": {
                "flags": chart["quality_flags"],
                "confidence_band": chart["solar_term_quality"]["confidence_band"],
                "exact_claims_allowed": chart["precision_policy"]["exact_claims_allowed"],
            },
            "evidence_refs": chart["solar_term_quality"]["evidence_refs"],
            "request_id": request_id,
        }
        _validate_contract(response, CHART_SCHEMA, request_id)
        return response

    return _idempotency_guard(idempotency_key, payload.model_dump_json(), _build)


@app.post("/internal/v1/compatibility")
def create_compatibility(
    payload: CompatibilityRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    x_contract_version: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    _service_token_header(authorization, x_api_key)
    _check_headers(request, x_request_id, x_contract_version)
    _validate_birth_input(payload.user.birth_input)
    _validate_birth_input(payload.partner.birth_input)
    request_id = x_request_id or str(uuid.uuid4())

    def _build():
        try:
            user_chart = calculate_chart(**_to_birth_kwargs(payload.user.birth_input), tables=load_tables())
            partner_chart = calculate_chart(**_to_birth_kwargs(payload.partner.birth_input), tables=load_tables())
            result = calculate_compatibility_from_charts(user_chart, partner_chart)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=_engine_error(exc, request_id)) from exc
        return {
            "contract_version": "saju-compatibility-v1",
            "engine_version": result["engine_metadata"]["engine"],
            "feature_scores": result["feature_scores"],
            "good_points": result["good_points"],
            "caution_points": result["caution_points"],
            "quality": {
                "flags": result["quality_flags"],
                "score_band": result["score_band"],
                "exact_score_allowed": result["exact_score_allowed"],
            },
            "evidence_refs": ["compatibility-scoring-model.md", "compatibility-feature-weights.csv"],
            "request_id": request_id,
        }

    return _idempotency_guard(idempotency_key, payload.model_dump_json(), _build)


LUCK_YEAR_MIN = 1900
LUCK_YEAR_MAX = 2100


def _validate_luck_params(year: int, month: int | None):
    if not (LUCK_YEAR_MIN <= year <= LUCK_YEAR_MAX):
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": f"year must be {LUCK_YEAR_MIN}-{LUCK_YEAR_MAX}", "retryable": False})
    if month is not None and not (1 <= month <= 12):
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "month must be 1-12", "retryable": False})



@app.post("/internal/v1/luck")
def create_luck_outlook(
    payload: ChartRequest,
    year: int,
    month: int | None = None,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    x_contract_version: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    _service_token_header(authorization, x_api_key)
    _check_headers(request=None, x_request_id=x_request_id, x_contract_version=x_contract_version)
    _validate_birth_input(payload.birth_input)
    _validate_luck_params(year, month)
    request_id = x_request_id or str(uuid.uuid4())

    def _build():
        try:
            chart = calculate_chart(**_to_birth_kwargs(payload.birth_input), tables=load_tables())
            chart["_tzinfo"] = _chart_tzinfo(payload.birth_input)
            tables = load_tables()
            outlook = luck_outlook(chart, tables, reference_year=year, month=month)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=_engine_error(exc, request_id)) from exc
        response = {
            "contract_version": "saju-luck-v1",
            "engine_version": chart["engine_metadata"]["engine_version"],
            "luck_outlook": outlook,
            "request_id": request_id,
        }
        return response

    return _idempotency_guard(idempotency_key, payload.model_dump_json(), _build)


def _chart_tzinfo(birth: BirthInput):
    from zoneinfo import ZoneInfo
    tz = (birth.location.timezone if birth.location and birth.location.timezone else "Asia/Seoul")
    try:
        return ZoneInfo(tz)
    except Exception:  # noqa: BLE001
        return ZoneInfo("Asia/Seoul")


_START = time.time()
