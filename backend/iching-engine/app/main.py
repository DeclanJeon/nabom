"""NABOM I Ching Engine private API service."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

ENGINE_DIR = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE_DIR))

from iching import resolve_casts  # noqa: E402
from reflection_resolver import build_reflection_request  # noqa: E402

import jsonschema  # noqa: E402

_CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"
READING_SCHEMA = json.loads((_CONTRACTS_DIR / "reading.schema.json").read_text(encoding="utf-8"))


def _validate_contract(response: dict, request_id: str):
    try:
        jsonschema.validate(response, READING_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise HTTPException(status_code=500, detail={"code": "CONTRACT_VIOLATION", "message": f"engine response violates contract: {exc.message}", "retryable": False, "request_id": request_id}) from exc

app = FastAPI(title="NABOM I Ching Engine", version="1.0.0")

SERVICE_TOKEN = os.environ.get("SAJU_SERVICE_TOKEN", "")

_IDEMPOTENCY: dict[str, tuple[str, dict]] = {}


def _idempotency_guard(key: str | None, fingerprint_source: str, build):
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
    """회전 overlap 지원: SAJU_SERVICE_TOKENS(쉼표 구분) + SAJU_SERVICE_TOKEN 병합."""
    tokens = [t for t in os.environ.get("SAJU_SERVICE_TOKENS", "").split(",") if t.strip()]
    if SERVICE_TOKEN:
        tokens.append(SERVICE_TOKEN)
    return set(tokens)


class ResolverMeta(BaseModel):
    version: str = "iching-reflection-v1"
    input_hash: str | None = None


class CastRequest(BaseModel):
    mode: str = "record_reflection"
    casts: list[int]
    resolver: ResolverMeta | None = None


class Period(BaseModel):
    model_config = {"populate_by_name": True}
    from_: str = Field(alias="from")
    to: str


class ReflectionContext(BaseModel):
    mode: str = "record_reflection"
    period: Period
    days_recorded: int | None = None
    mood: dict | None = None
    energy: dict | None = None
    tag_counts: dict | None = None
    goal_actions: dict | None = None
    relationship_event_count: int | None = None
    evidence_refs: list[str] = []


class ReflectionRequest(BaseModel):
    mode: str = "record_reflection"
    reflection_context: ReflectionContext
    resolver_version: str = "iching-reflection-v1"


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


def _headers(x_request_id: str | None, x_contract_version: str | None):
    if not x_request_id:
        raise HTTPException(status_code=400, detail={"code": "INVALID_INPUT", "message": "X-Request-Id is required", "retryable": False})
    if x_contract_version not in {None, "1.0"}:
        raise HTTPException(status_code=400, detail={"code": "INVALID_INPUT", "message": "unsupported X-Contract-Version", "retryable": False})


def _reading_response(reading, mode: str, request_id: str, resolver_hash: str | None = None):
    primary = reading["primary_hexagram"]
    resulting = reading["resulting_hexagram"]
    return {
        "contract_version": "iching-reading-v1",
        "engine_version": "iching-engine-v1",
        "mode": mode,
        "primary_hexagram": {
            "hexagram_id": primary["hexagram_id"],
            "name_zh": primary["name_zh"],
            "name_ko": primary.get("name_ko", ""),
            "judgment_text": primary.get("judgment_text", ""),
        },
        "changing_lines": [
            {
                "line_label": line["line_label"],
                "position": line["line_position"],
                "classical_text": line.get("classical_text", ""),
            }
            for line in reading.get("changing_lines", [])
        ],
        "resulting_hexagram": {
            "hexagram_id": resulting["hexagram_id"],
            "name_zh": resulting["name_zh"],
            "name_ko": resulting.get("name_ko", ""),
            "judgment_text": resulting.get("judgment_text", ""),
        },
        "interpretation_focus": {
            "policy": reading["interpretation"]["policy"],
            "rule": reading["interpretation"]["rule"],
        },
        "themes": reading.get("themes", []),
        "source_refs": [
            "https://zh.wikisource.org/wiki/周易",
            "https://ko.wikisource.org/wiki/역경",
        ],
        "resolver": {"version": "iching-reflection-v1", "input_hash": resolver_hash},
        "raw_reading_internal_ref": f"reading_{request_id}",
        "request_id": request_id,
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok", "engine": "iching", "uptime_seconds": round(time.time() - _START, 2)}


@app.get("/readyz")
def readyz():
    try:
        from iching import load_dataset, validate_dataset
        dataset = load_dataset()
        validate_dataset(dataset)
        reading = resolve_casts([7, 8, 9, 7, 6, 8])
        ok = reading["primary_hexagram"]["hexagram_id"] == 55
    except Exception as exc:  # noqa: BLE001
        return {"ready": False, "checks": {"dataset": {"status": "error", "message": str(exc)}}}
    return {"ready": ok, "checks": {"dataset": {"status": "ok", "hexagrams": 64}, "sample_cast": {"status": "ok", "primary": 55}}}


@app.post("/internal/v1/readings/cast")
def create_cast(
    payload: CastRequest,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    x_contract_version: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    _service_token_header(authorization, x_api_key)
    _headers(x_request_id, x_contract_version)
    request_id = x_request_id or str(uuid.uuid4())
    if payload.mode not in {"record_reflection", "live_cast"}:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "mode must be record_reflection or live_cast", "retryable": False})

    def _build():
        try:
            reading = resolve_casts(payload.casts)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": str(exc), "retryable": False}) from exc
        response = _reading_response(reading, payload.mode, request_id, payload.resolver.input_hash if payload.resolver else None)
        _validate_contract(response, request_id)
        return response

    return _idempotency_guard(idempotency_key, payload.model_dump_json(), _build)


@app.post("/internal/v1/reflections")
def create_reflection(
    payload: ReflectionRequest,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    x_contract_version: str | None = Header(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    _service_token_header(authorization, x_api_key)
    _headers(x_request_id, x_contract_version)
    request_id = x_request_id or str(uuid.uuid4())
    ctx = payload.reflection_context
    period = f"{ctx.period.from_}/{ctx.period.to}"

    def _build():
        try:
            req = build_reflection_request(ctx.evidence_refs, period, payload.resolver_version)
            reading = resolve_casts(req["casts"])
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": str(exc), "retryable": False}) from exc
        response = _reading_response(reading, "record_reflection", request_id, req["resolver"]["input_hash"])
        response["deterministic"] = True
        response["resolver"] = {"version": payload.resolver_version, "input_hash": req["resolver"]["input_hash"]}
        response["raw_reading_internal_ref"] = f"reading_{request_id}"
        _validate_contract(response, request_id)
        return response

    return _idempotency_guard(idempotency_key, payload.model_dump_json(), _build)


_START = time.time()
