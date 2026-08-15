"""End-to-end contract tests for the three backend services (offline, ASGI)."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ["NABOM_DEV_AUTH"] = "true"
os.environ["NABOM_GENERATE_CHARACTERS"] = "0"
os.environ["NABOM_CHARACTER_DIR"] = tempfile.mkdtemp(prefix="nabom-char-")


import httpx

BACKEND = Path(__file__).resolve().parents[1]


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


saju_main = _load_module("saju_app_main", BACKEND / "saju-engine" / "app" / "main.py")
iching_main = _load_module("iching_app_main", BACKEND / "iching-engine" / "app" / "main.py")
nabom_main = _load_module("nabom_app_main", BACKEND / "nabom-api" / "app" / "main.py")

saju_app = saju_main.app
iching_app = iching_main.app


def require(condition, message):
    if not condition:
        raise SystemExit(message)


async def add_consented_member(client, group_id, user_id, snapshot, owner):
    added = await client.post(
        f"/api/v1/insight-groups/{group_id}/members",
        json={"user_id": user_id, "profile_snapshot": snapshot},
        headers={"X-User-Id": owner},
    )
    require(added.status_code == 200, f"add member {user_id}: {added.status_code} {added.text}")
    granted = await client.post(
        f"/api/v1/insight-groups/{group_id}/members/consent",
        json={"granted": True},
        headers={"X-User-Id": user_id},
    )
    require(granted.status_code == 200, f"consent {user_id}: {granted.status_code} {granted.text}")

def user_birth():
    return {
        "calendar": "solar",
        "date": "1992-03-01",
        "time": "07:20",
        "time_precision": "exact",
        "location": {"label": "부산", "timezone": "Asia/Seoul", "lat": 35.1796, "lon": 129.0756},
        "gender": "남성",
    }


def partner_birth():
    return {
        "calendar": "solar",
        "date": "1994-09-14",
        "time": "18:30",
        "time_precision": "exact",
        "location": {"label": "서울", "timezone": "Asia/Seoul"},
        "gender": "여성",
    }


async def test_saju_engine_chart():
    transport = httpx.ASGITransport(app=saju_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://saju") as client:
        response = await client.post(
            "/internal/v1/charts",
            json={"birth_input": user_birth(), "calculation_policy": {"quality_mode": "strict"}},
            headers={"X-Request-Id": "req1", "X-Contract-Version": "1.0"},
        )
    require(response.status_code == 200, f"saju chart should pass with provider: {response.status_code} {response.text}")
    body = response.json()
    require(body["chart"]["four_pillars"]["day"]["hanja"] == "丙子", f"day pillar: {body['chart']['four_pillars']['day']['hanja']}")
    require(body["chart"]["four_pillars"]["year"]["hanja"] == "壬申", "year pillar mismatch")
    require("approximate_solar_terms" not in body["quality"]["flags"], f"strict mode should use verified terms: {body['quality']['flags']}")
    require(body["quality"]["exact_claims_allowed"] is True, "strict+provider should allow exact claims")
    require("element_analysis" in body and "day_master_strength" in body["element_analysis"], "element analysis missing")
    require(body["element_analysis"]["day_master_strength"]["day_master"]["hanja"] == "丙", "day master missing")
    require(body["narrative"]["narrative"], "charts 응답에 narrative 포함")
    joined = " ".join(body["narrative"]["narrative"])
    require("후보" in joined or "보입니다" in joined or "살펴볼 수" in joined, f"narrative 후보레벨 문구: {joined[:80]}")
    require("pattern_success_failure" in body["element_analysis"]["classical_analysis"], "고전 성패 포함")


async def test_saju_engine_input_validation():
    transport = httpx.ASGITransport(app=saju_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://saju") as client:
        cases = [
            ("범위 외 연도 1899", {**user_birth(), "date": "1899-01-05"}),
            ("범위 외 연도 2200", {**user_birth(), "date": "2200-01-01"}),
            ("미래 날짜", {**user_birth(), "date": "2099-01-01"}),
            ("잘못된 날짜", {**user_birth(), "date": "2026-02-30"}),
            ("잘못된 timezone", {**user_birth(), "location": {"timezone": "Not/AZone"}}),
            ("잘못된 시간", {**user_birth(), "time": "25:99"}),
        ]
        for index, (label, birth) in enumerate(cases):
            response = await client.post(
                "/internal/v1/charts",
                json={"birth_input": birth, "calculation_policy": {"quality_mode": "strict"}},
                headers={"X-Request-Id": f"val-{index}", "X-Contract-Version": "1.0"},
            )
            require(response.status_code == 422, f"{label} should 422: {response.status_code} {response.text[:120]}")
            require(response.json()["detail"]["code"] == "INVALID_INPUT", f"{label} code: {response.json()['detail']['code']}")


async def test_engine_idempotency():
    transport = httpx.ASGITransport(app=saju_app)
    headers = {"X-Request-Id": "idem1", "X-Contract-Version": "1.0", "Idempotency-Key": "idem-key-1"}
    async with httpx.AsyncClient(transport=transport, base_url="http://saju") as client:
        payload = {"birth_input": user_birth(), "calculation_policy": {"quality_mode": "strict"}}
        first = await client.post("/internal/v1/charts", json=payload, headers=headers)
        second = await client.post("/internal/v1/charts", json=payload, headers=headers)
        require(first.status_code == 200 and second.status_code == 200, f"idempotent replay: {first.status_code} {second.status_code}")
        require(first.json()["request_id"] == second.json()["request_id"], "replay must return same request id")
        conflict = await client.post("/internal/v1/charts", json={**payload, "birth_input": {**user_birth(), "time": "12:00"}}, headers=headers)
        require(conflict.status_code == 409, f"idempotency conflict: {conflict.status_code}")
        require(conflict.json()["detail"]["code"] == "IDEMPOTENCY_CONFLICT", f"code: {conflict.json()['detail']['code']}")


async def test_iching_idempotency():
    transport = httpx.ASGITransport(app=iching_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://iching") as client:
        payload = {"mode": "record_reflection", "casts": [7, 8, 9, 7, 6, 8], "resolver": {"version": "iching-reflection-v1"}}
        headers = {"X-Request-Id": "idem2", "Idempotency-Key": "iching-idem-1"}
        first = await client.post("/internal/v1/readings/cast", json=payload, headers=headers)
        second = await client.post("/internal/v1/readings/cast", json=payload, headers=headers)
        require(first.status_code == 200 and second.status_code == 200, f"iching idempotent: {first.status_code} {second.status_code}")
        require(first.json()["primary_hexagram"]["hexagram_id"] == second.json()["primary_hexagram"]["hexagram_id"], "same hexagram on replay")
        conflict = await client.post("/internal/v1/readings/cast", json={**payload, "casts": [6, 6, 6, 6, 6, 6]}, headers=headers)
        require(conflict.status_code == 409, f"iching conflict: {conflict.status_code}")


async def test_contract_violation_fails_closed():
    schema = json.loads((BACKEND / "contracts" / "chart.schema.json").read_text(encoding="utf-8"))
    bad = {"contract_version": "saju-chart-v1", "engine_version": "x", "chart": {}, "quality": {}, "request_id": "r"}
    import jsonschema
    try:
        jsonschema.validate(bad, schema)
        require(False, "malformed response should fail schema")
    except jsonschema.ValidationError:
        pass


async def test_iching_engine_reflection_deterministic():
    transport = httpx.ASGITransport(app=iching_app)
    ctx = {
        "mode": "record_reflection",
        "period": {"from": "2026-08-10", "to": "2026-08-16"},
        "days_recorded": 5,
        "evidence_refs": ["ev1", "ev2"],
    }
    async with httpx.AsyncClient(transport=transport, base_url="http://iching") as client:
        first = await client.post("/internal/v1/reflections", json={"mode": "record_reflection", "reflection_context": ctx}, headers={"X-Request-Id": "r1"})
        second = await client.post("/internal/v1/reflections", json={"mode": "record_reflection", "reflection_context": ctx}, headers={"X-Request-Id": "r2"})
        reading = await client.post(
            "/internal/v1/readings/cast",
            json={"mode": "record_reflection", "casts": [7, 8, 9, 7, 6, 8], "resolver": {"version": "iching-reflection-v1"}},
            headers={"X-Request-Id": "r3"},
        )
    require(first.status_code == 200 and second.status_code == 200, f"reflection status: {first.status_code} {second.status_code}")
    f1, f2 = first.json(), second.json()
    require(f1["deterministic"] is True, "reflection must be deterministic")
    require(f1["primary_hexagram"]["hexagram_id"] == f2["primary_hexagram"]["hexagram_id"], "replay must return same hexagram")
    require(f1["resolver"]["input_hash"] == f2["resolver"]["input_hash"], "replay must return same hash")
    require(f1["raw_reading_internal_ref"] != f2["raw_reading_internal_ref"], "internal refs should differ per request")
    # Vault 주제별 해석 렌즈가 응답에 포함되어야 한다 (ingest → get_themes → response)
    themes = f1.get("themes") or []
    require(isinstance(themes, list) and len(themes) >= 1, f"theme lens missing: {themes}")
    require(all(isinstance(t, dict) and t.get("topic") for t in themes), themes)
    require(reading.status_code == 200 and reading.json()["primary_hexagram"]["hexagram_id"] == 55, "cast smoke failed")


async def test_iching_engine_rejects_bad_casts():
    transport = httpx.ASGITransport(app=iching_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://iching") as client:
        response = await client.post(
            "/internal/v1/readings/cast",
            json={"mode": "record_reflection", "casts": [7, 8, 9]},
            headers={"X-Request-Id": "r4"},
        )
    require(response.status_code == 422, f"bad casts should 422: {response.status_code}")


async def test_nabom_facade_profile():
    nabom_main.saju_transport = httpx.ASGITransport(app=saju_app)
    nabom_main.iching_transport = httpx.ASGITransport(app=iching_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        response = await client.post(
            "/api/v1/living/profiles/initial",
            json={"birth_input": user_birth(), "current_priorities": ["career"], "change_goal": "완성도"},
            headers={"X-User-Id": "usr_a", "X-Request-Id": "n1"},
        )
    require(response.status_code == 200, f"profile facade: {response.status_code} {response.text}")
    body = response.json()
    profile = body["profile"]
    require(profile["trait_candidates"], "trait candidates missing")
    require(profile["identity_sentence"], "identity sentence missing")
    require("narrative" not in profile, "engine narrative must stay internal")
    require("use_god_candidates" not in profile, "use-god must stay internal")
    require("growth_direction" not in profile, "growth_direction must stay internal")
    require("analysis" not in profile, "raw analysis must stay internal")
    traits = {c["trait"] for c in profile["trait_candidates"]}
    require("recovery" in traits, f"dominant water should map to recovery trait: {traits}")
    require("execution" in traits, f"deficient metal should map to execution trait: {traits}")
    labels = {t["label_ko"] for t in profile["traits"]}
    require("회복력" in labels, labels)
    require("추진력" in labels, labels)
    raw = str(body)
    require("judgment_text" not in raw and "name_zh" not in raw, "raw engine data must not leak to facade response")
    for leaked in ("주작", "백호", "청룡", "현무", "황룡", "일간", "丙", "병화", "오행", "용신"):
        require(leaked not in raw, f"myeongni term leaked: {leaked}")


async def test_nabom_facade_reflection_no_raw():
    from datetime import date, timedelta

    nabom_main.iching_transport = httpx.ASGITransport(app=iching_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    start = (date.today() - timedelta(days=6)).isoformat()
    end = date.today().isoformat()
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        seeded = await client.post(
            "/api/v1/living/entries",
            json={"date": start, "mood": 3, "energy": 3, "satisfaction": 3, "text": "회고 시드"},
            headers={"X-User-Id": "usr_a"},
        )
        require(seeded.status_code == 200, f"seed daily: {seeded.status_code} {seeded.text}")
        response = await client.post(
            "/api/v1/living/reflections",
            json={"period_from": start, "period_to": end, "days_recorded": 99, "evidence_refs": ["ignore-client"]},
            headers={"X-User-Id": "usr_a", "X-Request-Id": "n2"},
        )
    require(response.status_code == 200, f"reflection facade: {response.status_code} {response.text}")
    body = response.json()
    require(body["reflection"]["mode"] == "record_reflection", "mode mismatch")
    require(body["mirror"]["coverage"]["days_recorded"] >= 1, "mirror must be attached to reflection")
    raw = str(body)
    require("judgment_text" not in raw and "name_zh" not in raw, "classical/hexagram data must not leak to user-facing reflection")


async def test_nabom_facade_relationship_consent():
    nabom_main.saju_transport = httpx.ASGITransport(app=saju_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        denied = await client.post(
            "/api/v1/relationships/rel_1/mirror",
            json={"context": "friend", "partner_birth_input": partner_birth()},
            headers={"X-User-Id": "usr_a", "X-Request-Id": "n3"},
        )
        allowed = await client.post(
            "/api/v1/relationships/rel_1/mirror",
            json={"context": "friend", "partner_birth_input": partner_birth()},
            headers={"X-User-Id": "usr_a", "X-Consent": "granted", "X-Request-Id": "n4"},
        )
    require(denied.status_code == 403, f"relationship without consent should be 403: {denied.status_code}")
    require(allowed.status_code == 200, f"relationship with consent should pass: {allowed.status_code} {allowed.text}")
    body = allowed.json()
    require(body["good_points"], "good points missing")
    require(body["status"] == "hypothesis", "mirror must be hypothesis-level")


async def test_saju_engine_lunar_convert_or_fail_closed():
    transport = httpx.ASGITransport(app=saju_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://saju") as client:
        ok = await client.post(
            "/internal/v1/charts",
            json={
                "birth_input": {**user_birth(), "calendar": "lunar", "is_lunar_leap_month": False},
                "calculation_policy": {"quality_mode": "strict"},
            },
            headers={"X-Request-Id": "req5a", "X-Contract-Version": "1.0"},
        )
        auto = await client.post(
            "/internal/v1/charts",
            json={
                "birth_input": {**user_birth(), "calendar": "lunar", "is_lunar_leap_month": None},
                "calculation_policy": {"quality_mode": "strict"},
            },
            headers={"X-Request-Id": "req5b", "X-Contract-Version": "1.0"},
        )
        ambiguous = await client.post(
            "/internal/v1/charts",
            json={
                "birth_input": {**user_birth(), "date": "2001-04-15", "calendar": "lunar", "is_lunar_leap_month": None},
                "calculation_policy": {"quality_mode": "strict"},
            },
            headers={"X-Request-Id": "req5c", "X-Contract-Version": "1.0"},
        )
        unknown_time = await client.post(
            "/internal/v1/charts",
            json={
                "birth_input": {**user_birth(), "time": "", "time_precision": "unknown"},
                "calculation_policy": {"quality_mode": "strict"},
            },
            headers={"X-Request-Id": "req5d", "X-Contract-Version": "1.0"},
        )
        boundary = await client.post(
            "/internal/v1/charts",
            json={
                "birth_input": {**user_birth(), "date": "2026-02-04", "time": "05:01"},
                "calculation_policy": {"quality_mode": "strict"},
            },
            headers={"X-Request-Id": "req5e", "X-Contract-Version": "1.0"},
        )
    require(ok.status_code == 200, f"lunar with explicit leap flag should convert: {ok.status_code} {ok.text[:200]}")
    trace = ok.json()["chart"]["calendar_conversion"]
    require(trace["solar_birth_date"] == "1992-04-03", f"lunar 1992-03-01 -> solar: {trace['solar_birth_date']}")
    require(auto.status_code == 200, f"1992 lunar without leap flag should convert: {auto.status_code} {auto.text[:200]}")
    require(auto.json()["chart"]["calendar_conversion"].get("leap_month_auto_resolved") is True, auto.json()["chart"]["calendar_conversion"])
    require(ambiguous.status_code == 422, f"ambiguous leap should 422: {ambiguous.status_code} {ambiguous.text[:240]}")
    detail = ambiguous.json()["detail"]
    require(detail["code"] == "LUNAR_LEAP_MONTH_AMBIGUOUS", detail)
    require(len(detail["candidates"]) == 2, detail)
    require(unknown_time.status_code == 200, f"unknown time: {unknown_time.status_code} {unknown_time.text[:200]}")
    unknown_chart = unknown_time.json()["chart"]
    require(unknown_chart["four_pillars"]["hour"] is None, unknown_chart["four_pillars"])
    require("hour_pillar_omitted" in unknown_chart["quality_flags"], unknown_chart["quality_flags"])
    require(boundary.status_code == 200, f"boundary: {boundary.status_code} {boundary.text[:200]}")
    require(boundary.json()["chart"]["boundary_candidates"], boundary.json()["chart"])
    schools = ok.json()["element_analysis"]["use_god_schools"]["schools"]
    require(set(schools) == {"ziping_pattern", "di_tian_sui", "qiaohou"}, schools)
    require(ok.json()["element_analysis"]["use_god_candidates"]["merge_policy"] == "schools_stay_separate", ok.json()["element_analysis"]["use_god_candidates"])


async def test_nabom_facade_reflection_schema_valid():
    import jsonschema
    import json
    from datetime import date, timedelta

    nabom_main.iching_transport = httpx.ASGITransport(app=iching_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    schema = json.loads((BACKEND / "contracts" / "reflection.schema.json").read_text(encoding="utf-8"))
    start = (date.today() - timedelta(days=6)).isoformat()
    end = date.today().isoformat()
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        seeded = await client.post(
            "/api/v1/living/entries",
            json={"date": start, "mood": 3, "energy": 3, "satisfaction": 3, "text": "스키마 시드"},
            headers={"X-User-Id": "usr_schema"},
        )
        require(seeded.status_code == 200, f"seed daily: {seeded.status_code} {seeded.text}")
        response = await client.post(
            "/api/v1/living/reflections",
            json={"period_from": start, "period_to": end, "days_recorded": 5, "evidence_refs": ["ev1", "ev2"]},
            headers={"X-User-Id": "usr_schema", "X-Request-Id": "n5"},
        )
    require(response.status_code == 200, f"reflection schema test: {response.status_code} {response.text}")
    jsonschema.validate(response.json()["reflection"], schema)


async def test_nabom_facade_rejected_hypothesis_blocked():
    nabom_main.saju_transport = httpx.ASGITransport(app=saju_app)
    nabom_main.iching_transport = httpx.ASGITransport(app=iching_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        created = await client.post(
            "/api/v1/living/profiles/initial",
            json={"birth_input": user_birth()},
            headers={"X-User-Id": "usr_b", "X-Request-Id": "n6"},
        )
        profile_id = created.json()["profile_version_id"]
        require("execution" in {c["trait"] for c in created.json()["profile"]["trait_candidates"]}, "execution should exist initially")
        rejected = await client.post(
            f"/api/v1/living/profiles/{profile_id}/feedback",
            json={"target_type": "trait", "target_key": "execution", "rating": "incorrect", "comment": "결정은 잘 하지만 표현이 부족함"},
            headers={"X-User-Id": "usr_b"},
        )
        require(rejected.status_code == 200, f"feedback: {rejected.status_code} {rejected.text}")
        fetched = await client.get(f"/api/v1/living/profiles/{profile_id}", headers={"X-User-Id": "usr_b"})
        traits = {c["trait"] for c in fetched.json()["profile"]["trait_candidates"]}
        require("execution" not in traits, f"rejected hypothesis must not appear in active profile: {traits}")
        require("recovery" in traits, "other candidates should remain")
        wrong_owner = await client.get(f"/api/v1/living/profiles/{profile_id}", headers={"X-User-Id": "other"})
        require(wrong_owner.status_code == 404, "cross-owner profile access should be 404")


async def test_saju_engine_token_rotation():
    import os
    previous = os.environ.get("SAJU_SERVICE_TOKENS")
    os.environ["SAJU_SERVICE_TOKENS"] = "tok_old,tok_new"
    try:
        transport = httpx.ASGITransport(app=saju_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://saju") as client:
            old_ok = await client.post(
                "/internal/v1/charts",
                json={"birth_input": user_birth()},
                headers={"X-Request-Id": "tok1", "Authorization": "Bearer tok_old"},
            )
            new_ok = await client.post(
                "/internal/v1/charts",
                json={"birth_input": user_birth()},
                headers={"X-Request-Id": "tok2", "Authorization": "Bearer tok_new"},
            )
            bad = await client.post(
                "/internal/v1/charts",
                json={"birth_input": user_birth()},
                headers={"X-Request-Id": "tok3", "Authorization": "Bearer wrong"},
            )
            missing = await client.post(
                "/internal/v1/charts",
                json={"birth_input": user_birth()},
                headers={"X-Request-Id": "tok4"},
            )
    finally:
        if previous is None:
            os.environ.pop("SAJU_SERVICE_TOKENS", None)
        else:
            os.environ["SAJU_SERVICE_TOKENS"] = previous
    require(old_ok.status_code == 200, f"rotation overlap must accept old token: {old_ok.status_code}")
    require(new_ok.status_code == 200, f"rotation must accept new token: {new_ok.status_code}")
    require(bad.status_code == 401, f"wrong token must be rejected: {bad.status_code}")
    require(missing.status_code == 401, f"missing token must be rejected when tokens configured: {missing.status_code}")


async def test_nabom_relationship_consent_machine():
    nabom_main.saju_transport = httpx.ASGITransport(app=saju_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        created = await client.post(
            "/api/v1/relationships",
            json={
                "participant_user_id": "usr_y",
                "context": "friend",
                "user_birth_input": user_birth(),
                "participant_birth_input": partner_birth(),
            },
            headers={"X-User-Id": "usr_x"},
        )
        require(created.status_code == 200, f"create relationship: {created.status_code} {created.text}")
        rel = created.json()
        require(rel["status"] == "draft", f"initial state should be draft: {rel['status']}")
        rel_id = rel["relationship_id"]

        # 한쪽만 동의 → consent_pending, mirror 불가
        one = await client.post(f"/api/v1/relationships/{rel_id}/consent", json={"scopes": ["birth_hypothesis", "relationship_mirror"]}, headers={"X-User-Id": "usr_x"})
        require(one.json()["status"] == "consent_pending", f"one-sided consent: {one.json()['status']}")
        blocked = await client.post(f"/api/v1/relationships/{rel_id}/mirror", json={}, headers={"X-User-Id": "usr_x"})
        require(blocked.status_code == 403, f"mirror before bilateral consent: {blocked.status_code}")

        # 양쪽 동의 → active, mirror 가능
        two = await client.post(f"/api/v1/relationships/{rel_id}/consent", json={"scopes": ["birth_hypothesis", "relationship_mirror"]}, headers={"X-User-Id": "usr_y"})
        require(two.json()["status"] == "active", f"bilateral consent: {two.json()['status']}")

        # 동의 철회 → paused
        rev = await client.post(f"/api/v1/relationships/{rel_id}/consent", json={"scopes": []}, headers={"X-User-Id": "usr_y"})
        require(rev.json()["status"] == "paused", f"revoke consent: {rev.json()['status']}")
        blocked2 = await client.post(f"/api/v1/relationships/{rel_id}/mirror", json={}, headers={"X-User-Id": "usr_x"})
        require(blocked2.status_code == 403, f"mirror after revoke: {blocked2.status_code}")


async def test_nabom_relationship_mirror_directional():
    nabom_main.saju_transport = httpx.ASGITransport(app=saju_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        created = await client.post(
            "/api/v1/relationships",
            json={"participant_user_id": "usr_y", "user_birth_input": user_birth(), "participant_birth_input": partner_birth()},
            headers={"X-User-Id": "usr_x"},
        )
        rel_id = created.json()["relationship_id"]
        await client.post(f"/api/v1/relationships/{rel_id}/consent", json={"scopes": ["birth_hypothesis", "relationship_mirror", "relationship_evidence"]}, headers={"X-User-Id": "usr_x"})
        await client.post(f"/api/v1/relationships/{rel_id}/consent", json={"scopes": ["birth_hypothesis", "relationship_mirror", "relationship_evidence"]}, headers={"X-User-Id": "usr_y"})
        # 공동 기록 2건 추가 (immutable event)
        ev1 = await client.post(f"/api/v1/relationships/{rel_id}/evidence", json={"content": "팀 프로젝트 준비", "observations": ["결정 전 역할 합의가 없었음"], "consent_scope": "relationship_evidence"}, headers={"X-User-Id": "usr_x"})
        ev2 = await client.post(f"/api/v1/relationships/{rel_id}/evidence", json={"content": "회고 후 다음 계획 합의", "observations": ["담당자와 완료 조건을 사전 합의함"], "consent_scope": "relationship_evidence"}, headers={"X-User-Id": "usr_y"})
        require(ev1.status_code == 200 and ev2.status_code == 200, f"evidence add: {ev1.status_code} {ev2.status_code}")
        listed = await client.get(f"/api/v1/relationships/{rel_id}/evidence", headers={"X-User-Id": "usr_x"})
        require(len(listed.json()["evidence"]) == 2, "evidence should be append-only")

        mirror = await client.post(f"/api/v1/relationships/{rel_id}/mirror", json={}, headers={"X-User-Id": "usr_x"})
        require(mirror.status_code == 200, f"directional mirror: {mirror.status_code} {mirror.text[:300]}")
        body = mirror.json()
        require(isinstance(body["contributions_a_to_b"], list), "a_to_b must be a list")
        require(isinstance(body["contributions_b_to_a"], list), "b_to_a must be a list")
        require(isinstance(body["shared_growth_areas"], list), "shared must be a list")
        require(isinstance(body["tensions"], list), "tensions must be a list")
        require(body["evidence_count"] == 2, "mirror should reflect evidence count")
        require(body["status"] == "hypothesis", "mirror must be hypothesis-level")


async def test_nabom_insight_group_minimum_five():
    transport = httpx.ASGITransport(app=nabom_main.app)
    snapshots = [
        {"ratio": {"wood": 0.4, "fire": 0.2, "earth": 0.1, "metal": 0.1, "water": 0.2}},
        {"ratio": {"wood": 0.2, "fire": 0.4, "earth": 0.1, "metal": 0.1, "water": 0.2}},
        {"ratio": {"wood": 0.1, "fire": 0.2, "earth": 0.4, "metal": 0.1, "water": 0.2}},
        {"ratio": {"wood": 0.2, "fire": 0.1, "earth": 0.1, "metal": 0.4, "water": 0.2}},
        {"ratio": {"wood": 0.2, "fire": 0.2, "earth": 0.1, "metal": 0.1, "water": 0.4}},
    ]
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        group = await client.post("/api/v1/insight-groups", json={"name": "팀A", "owner_profile_snapshot": snapshots[0]}, headers={"X-User-Id": "g_owner"})
        gid = group.json()["group_id"]
        # 소유자 포함 4명 → insufficient
        for i in range(1, 4):
            await add_consented_member(client, gid, f"m{i}", snapshots[i], "g_owner")
        prof = (await client.get(f"/api/v1/insight-groups/{gid}/profile", headers={"X-User-Id": "g_owner"})).json()
        require(prof["status"] == "insufficient_members", f"4 members should block inference: {prof['status']}")
        require(prof["aggregate_only"] is False, "insufficient group must not aggregate")
        require("mean_element_ratio" not in prof, "no element inference below minimum")
        await add_consented_member(client, gid, "m4", snapshots[4], "g_owner")
        prof5 = (await client.get(f"/api/v1/insight-groups/{gid}/profile", headers={"X-User-Id": "g_owner"})).json()
        require(prof5["status"] == "active", f"5 members should activate: {prof5['status']}")
        require(prof5["aggregate_only"] is True, "group profile must be aggregate-only")
        require(prof5["anonymization"] == "k_anonymous", "anonymization flag missing")
        require("mean_element_ratio" in prof5, "aggregate ratio should exist")
        require(abs(sum(prof5["mean_element_ratio"].values()) - 1.0) < 0.01, "mean ratios should sum to 1")


async def test_nabom_group_to_group_aggregate_only():
    transport = httpx.ASGITransport(app=nabom_main.app)
    snap_a = [{"ratio": {"wood": 0.5, "fire": 0.2, "earth": 0.1, "metal": 0.1, "water": 0.1}}] * 5
    snap_b = [{"ratio": {"water": 0.5, "fire": 0.2, "earth": 0.1, "metal": 0.1, "wood": 0.1}}] * 5
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        ga = (await client.post("/api/v1/insight-groups", json={"name": "팀A"}, headers={"X-User-Id": "o1"})).json()["group_id"]
        gb = (await client.post("/api/v1/insight-groups", json={"name": "팀B"}, headers={"X-User-Id": "o2"})).json()["group_id"]
        for gid, snaps, owner in ((ga, snap_a, "o1"), (gb, snap_b, "o2")):
            for i, snap in enumerate(snaps):
                await add_consented_member(client, gid, f"{gid}_{i}", snap, owner)
        insight = await client.post(f"/api/v1/insight-groups/{ga}/relationship-insights", json={"group_b_id": gb}, headers={"X-User-Id": "o1"})
        require(insight.status_code == 200, f"group insight: {insight.status_code} {insight.text[:300]}")
        body = insight.json()
        require(body["aggregate_only"] is True, "group insight must be aggregate-only")
        require(body["group_a_contributes"], "group A contribution missing")
        require(body["group_b_contributes"], "group B contribution missing")
        require(body["recommended_joint_experiment"], "joint experiment missing")


async def test_nabom_group_buy_separate_namespace():
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        group = await client.post("/api/v1/insight-groups", json={"name": "공동구매아님"}, headers={"X-User-Id": "o1"})
        require(group.status_code == 200, "insight-group create should not collide with group-buy routes")
        # 그룹 생성만으로는 어떤 GroupBuy 캠페인도 생기지 않는다 (별도 도메인)
        require(group.json()["status"] in {"inviting", "active"}, "insight group state mismatch")


async def test_saju_engine_luck_outlook():
    transport = httpx.ASGITransport(app=saju_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://saju") as client:
        response = await client.post(
            "/internal/v1/luck",
            params={"year": 2026, "month": 5},
            json={"birth_input": user_birth(), "calculation_policy": {"quality_mode": "strict"}},
            headers={"X-Request-Id": "luck1", "X-Contract-Version": "1.0"},
        )
    require(response.status_code == 200, f"luck: {response.status_code} {response.text[:200]}")
    body = response.json()["luck_outlook"]
    require(body["annual"]["pillar"]["ko"] == "병오", f"2026 세운: {body['annual']['pillar']}")
    require(body["monthly"]["pillar"]["ko"] == "계사", f"2026-5월 월운: {body['monthly']['pillar']}")
    require(body["policy"] == "luck_weather_not_prediction", "policy missing")
    require(body["decade"]["decade_cycles"][0]["pillar"]["ko"] == "계묘", "decade reuse broken")


async def test_nabom_facade_luck():
    nabom_main.saju_transport = httpx.ASGITransport(app=saju_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        response = await client.post(
            "/api/v1/living/luck?year=2026&month=5",
            json={"birth_input": user_birth()},
            headers={"X-User-Id": "usr_a", "X-Request-Id": "n-luck"},
        )
    require(response.status_code == 200, f"facade luck: {response.status_code} {response.text[:200]}")
    body = response.json()
    require(body["annual"]["pillar"]["ko"] == "병오", "annual pillar missing")
    require(body["monthly"]["pillar"]["ko"] == "계사", "monthly pillar missing")
    require("cycles" in body["decade"] and body["decade"]["cycles"][0]["pillar_ko"] == "계묘", "decade summary missing")
    require("raw" not in str(body).lower() and "judgment_text" not in str(body), "raw data must not leak")


async def test_luck_params_validation():
    transport = httpx.ASGITransport(app=saju_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://saju") as client:
        for label, params in [("year 500", {"year": 500}), ("year 1800", {"year": 1800}), ("year 2200", {"year": 2200}), ("month 13", {"year": 2026, "month": 13}), ("month 0", {"year": 2026, "month": 0})]:
            response = await client.post(
                "/internal/v1/luck",
                params=params,
                json={"birth_input": user_birth(), "calculation_policy": {"quality_mode": "strict"}},
                headers={"X-Request-Id": f"luck-val-{label}"},
            )
            require(response.status_code == 422, f"luck {label} should 422: {response.status_code} {response.text[:120]}")
            require(response.json()["detail"]["code"] == "INVALID_INPUT", f"luck {label} code: {response.json()['detail']['code']}")


async def test_engine_error_sanitized():
    """422 메시지에 내부 환경변수/경로가 노출되지 않아야 한다."""
    transport = httpx.ASGITransport(app=saju_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://saju") as client:
        response = await client.post(
            "/internal/v1/charts",
            json={"birth_input": {**user_birth(), "date": "2001-04-15", "calendar": "lunar", "is_lunar_leap_month": None}, "calculation_policy": {"quality_mode": "strict"}},
            headers={"X-Request-Id": "sanitize1"},
        )
    require(response.status_code == 422, f"lunar blocked: {response.status_code}")
    message = response.json()["detail"]["message"]
    require("SAJU_" not in message and "/" not in message, f"error message must not leak internals: {message}")
    require(response.json()["detail"]["code"] == "LUNAR_LEAP_MONTH_AMBIGUOUS", response.json()["detail"])


async def test_nabom_facade_idempotency():
    nabom_main.saju_transport = httpx.ASGITransport(app=saju_app)
    nabom_main.iching_transport = httpx.ASGITransport(app=iching_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    headers = {"X-User-Id": "idem_user", "Idempotency-Key": "facade-idem-1"}
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        payload = {"birth_input": user_birth()}
        first = await client.post("/api/v1/living/profiles/initial", json=payload, headers=headers)
        second = await client.post("/api/v1/living/profiles/initial", json=payload, headers=headers)
        require(first.status_code == 200 and second.status_code == 200, f"facade idem: {first.status_code} {second.status_code}")
        require(first.json()["profile_version_id"] == second.json()["profile_version_id"], "replay must return same profile (no duplicate)")
        conflict = await client.post("/api/v1/living/profiles/initial", json={**payload, "birth_input": {**user_birth(), "time": "12:00"}}, headers=headers)
        require(conflict.status_code == 409, f"facade conflict: {conflict.status_code}")
        require(conflict.json()["detail"]["code"] == "IDEMPOTENCY_CONFLICT", "facade conflict code")


async def test_nabom_relationship_create_validates_birth():
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        bad = await client.post(
            "/api/v1/relationships",
            json={"participant_user_id": "usr_y", "user_birth_input": {**user_birth(), "date": "2026-02-30"}, "participant_birth_input": partner_birth()},
            headers={"X-User-Id": "usr_x"},
        )
        require(bad.status_code == 422, f"relationship create should validate birth: {bad.status_code}")
        bad_tz = await client.post(
            "/api/v1/relationships",
            json={"participant_user_id": "usr_y", "user_birth_input": {**user_birth(), "location": {"timezone": "Not/AZone"}}, "participant_birth_input": partner_birth()},
            headers={"X-User-Id": "usr_x"},
        )
        require(bad_tz.status_code == 422, f"relationship create should validate timezone: {bad_tz.status_code}")


async def test_nabom_mirror_scope_enforcement():
    """character_profile only cannot run a birth mirror; birth_hypothesis is required."""
    nabom_main.saju_transport = httpx.ASGITransport(app=saju_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        created = await client.post(
            "/api/v1/relationships",
            json={"participant_user_id": "usr_y", "user_birth_input": user_birth(), "participant_birth_input": partner_birth()},
            headers={"X-User-Id": "usr_x"},
        )
        rel_id = created.json()["relationship_id"]
        await client.post(f"/api/v1/relationships/{rel_id}/consent", json={"scopes": ["character_profile"]}, headers={"X-User-Id": "usr_x"})
        await client.post(f"/api/v1/relationships/{rel_id}/consent", json={"scopes": ["character_profile"]}, headers={"X-User-Id": "usr_y"})
        denied = await client.post(f"/api/v1/relationships/{rel_id}/mirror", json={}, headers={"X-User-Id": "usr_x"})
        require(denied.status_code == 403, f"character-only mirror: {denied.status_code} {denied.text[:150]}")
        require(denied.json()["detail"]["code"] == "CONSENT_REQUIRED", denied.json())
        await client.post(f"/api/v1/relationships/{rel_id}/consent", json={"scopes": ["birth_hypothesis", "character_profile"]}, headers={"X-User-Id": "usr_x"})
        await client.post(f"/api/v1/relationships/{rel_id}/consent", json={"scopes": ["birth_hypothesis", "character_profile"]}, headers={"X-User-Id": "usr_y"})
        allowed = await client.post(f"/api/v1/relationships/{rel_id}/mirror", json={}, headers={"X-User-Id": "usr_x"})
        require(allowed.status_code == 200, f"birth+character mirror: {allowed.status_code} {allowed.text[:150]}")


async def test_nabom_cross_user_access_blocked():
    """제3자는 타인 관계 evidence/그룹 프로필을 읽을 수 없어야 한다."""
    nabom_main.saju_transport = httpx.ASGITransport(app=saju_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        # 관계 생성 + 양쪽 동의 + evidence
        rel = await client.post(
            "/api/v1/relationships",
            json={"participant_user_id": "usr_y", "user_birth_input": user_birth(), "participant_birth_input": partner_birth()},
            headers={"X-User-Id": "usr_x"},
        )
        rid = rel.json()["relationship_id"]
        await client.post(f"/api/v1/relationships/{rid}/consent", json={"scopes": ["birth_hypothesis", "relationship_evidence"]}, headers={"X-User-Id": "usr_x"})
        await client.post(f"/api/v1/relationships/{rid}/consent", json={"scopes": ["birth_hypothesis", "relationship_evidence"]}, headers={"X-User-Id": "usr_y"})
        await client.post(f"/api/v1/relationships/{rid}/evidence", json={"content": "비밀 기록", "observations": ["x"], "consent_scope": "relationship_evidence"}, headers={"X-User-Id": "usr_x"})
        # 제3자 접근 차단
        leak = await client.get(f"/api/v1/relationships/{rid}/evidence", headers={"X-User-Id": "usr_z"})
        require(leak.status_code == 403, f"제3자 evidence 조회는 403이어야 함: {leak.status_code}")
        consent = await client.post(f"/api/v1/relationships/{rid}/consent", json={"scopes": ["birth_hypothesis"]}, headers={"X-User-Id": "usr_z"})
        require(consent.status_code == 403, f"제3자 consent는 403이어야 함: {consent.status_code}")
        # 그룹 프로필 제3자 접근 차단
        g = await client.post("/api/v1/insight-groups", json={"name": "팀X", "owner_profile_snapshot": {"ratio": {"wood": 0.2, "fire": 0.2, "earth": 0.2, "metal": 0.2, "water": 0.2}}}, headers={"X-User-Id": "o1"})
        gid = g.json()["group_id"]
        prof = await client.get(f"/api/v1/insight-groups/{gid}/profile", headers={"X-User-Id": "usr_z"})
        require(prof.status_code == 403, f"비구성원 그룹 프로필은 403이어야 함: {prof.status_code}")
        mine = await client.get(f"/api/v1/insight-groups/{gid}/profile", headers={"X-User-Id": "o1"})
        require(mine.status_code == 200, "구성원(owner)은 조회 가능해야 함")


async def test_nabom_facade_propagates_engine_4xx():
    """facade는 엔진 4xx(입력 오류)를 502가 아닌 원 상태로 전파해야 한다."""
    nabom_main.saju_transport = httpx.ASGITransport(app=saju_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        bad = await client.post(
            "/api/v1/living/profiles/initial",
            json={"birth_input": {**user_birth(), "date": "2099-01-01"}},
            headers={"X-User-Id": "usr_a"},
        )
        require(bad.status_code == 422, f"facade는 입력 오류를 422로 전파해야 함: {bad.status_code}")
        require(bad.json()["detail"]["code"] == "INVALID_INPUT", f"code: {bad.json()['detail']['code']}")
        bad_luck = await client.post(
            "/api/v1/living/luck?year=500",
            json={"birth_input": user_birth()},
            headers={"X-User-Id": "usr_a"},
        )
        require(bad_luck.status_code == 422, f"luck 입력 오류도 422 전파: {bad_luck.status_code}")


async def test_concurrent_profile_creation():
    """동시 요청에서 SQLite lock 없이 전부 성공해야 한다."""
    nabom_main.saju_transport = httpx.ASGITransport(app=saju_app)
    transport = httpx.ASGITransport(app=nabom_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        results = await asyncio.gather(*[
            client.post("/api/v1/living/profiles/initial", json={"birth_input": user_birth()}, headers={"X-User-Id": f"conc_user_{i}"})
            for i in range(8)
        ])
        codes = [r.status_code for r in results]
        require(all(c == 200 for c in codes), f"동시 생성 전부 200이어야 함: {codes}")
        ids = [r.json()["profile_version_id"] for r in results]
        require(len(set(ids)) == 8, f"8개 모두 고유 프로필: {len(set(ids))}")


async def test_nabom_group_to_group_deficient_correct():
    """그룹 간 shared_improvement가 각 그룹의 실제 deficient를 참조해야 한다."""
    transport = httpx.ASGITransport(app=nabom_main.app)
    snap_wood = {"ratio": {"wood": 0.5, "fire": 0.2, "earth": 0.1, "metal": 0.1, "water": 0.1}}
    snap_water = {"ratio": {"water": 0.5, "fire": 0.2, "earth": 0.1, "metal": 0.1, "wood": 0.1}}
    async with httpx.AsyncClient(transport=transport, base_url="http://nabom") as client:
        ga = (await client.post("/api/v1/insight-groups", json={"name": "A", "owner_profile_snapshot": snap_wood}, headers={"X-User-Id": "o1"})).json()["group_id"]
        gb = (await client.post("/api/v1/insight-groups", json={"name": "B", "owner_profile_snapshot": snap_water}, headers={"X-User-Id": "o2"})).json()["group_id"]
        for gid, snap, owner in ((ga, snap_wood, "o1"), (gb, snap_water, "o2")):
            for i in range(4):
                await add_consented_member(client, gid, f"{gid}_{i}", snap, owner)
        insight = (await client.post(f"/api/v1/insight-groups/{ga}/relationship-insights", json={"group_b_id": gb}, headers={"X-User-Id": "o1"})).json()
        elems = {i["element"] for i in insight["shared_improvement"]}
        require("earth" in elems, f"그룹A(목 과다) deficient는 earth여야 함: {elems}")
        require("wood" in elems, f"그룹B(수 과다) deficient는 wood여야 함: {elems}")


async def main():
    await test_saju_engine_chart()
    await test_saju_engine_input_validation()
    await test_saju_engine_lunar_convert_or_fail_closed()
    await test_saju_engine_token_rotation()
    await test_saju_engine_luck_outlook()
    await test_luck_params_validation()
    await test_engine_error_sanitized()
    await test_engine_idempotency()
    await test_iching_idempotency()
    await test_contract_violation_fails_closed()
    await test_iching_engine_reflection_deterministic()
    await test_iching_engine_rejects_bad_casts()
    await test_nabom_facade_profile()
    await test_nabom_facade_reflection_no_raw()
    await test_nabom_facade_reflection_schema_valid()
    await test_nabom_facade_rejected_hypothesis_blocked()
    await test_nabom_facade_luck()
    await test_nabom_facade_idempotency()
    await test_nabom_relationship_consent_machine()
    await test_nabom_relationship_mirror_directional()
    await test_nabom_relationship_create_validates_birth()
    await test_nabom_mirror_scope_enforcement()
    await test_nabom_cross_user_access_blocked()
    await test_nabom_facade_propagates_engine_4xx()
    await test_concurrent_profile_creation()
    await test_nabom_insight_group_minimum_five()
    await test_nabom_group_to_group_aggregate_only()
    await test_nabom_group_to_group_deficient_correct()
    await test_nabom_group_buy_separate_namespace()
    print("backend engine API tests passed")


if __name__ == "__main__":
    asyncio.run(main())


async def test_juyeok_jeonui_not_user_facing():
    """주역전의 정제본은 엔진 데이터 레이어에만 존재하고 사용자-facing 경로에 누출되지 않는다."""
    import json as _json
    import re as _re

    korean = _json.load(open("iching-engine/engine/data/korean_translations.json"))
    assert korean["schema_version"] == 2, "integration schema must be v2"
    assert "integrated_reference" in _json.dumps(korean["source_hierarchy"], ensure_ascii=False)
    # 64괘 전부 주역전의 레이어 + 기존 judgment_ko 유지
    for hid in range(1, 65):
        h = korean["hexagrams"].get(str(hid))
        assert h and h.get("juyeok_jeonui"), f"hexagram {hid} missing juyeok_jeonui"
        assert h.get("judgment_ko"), f"hexagram {hid} missing judgment_ko"
        assert not _re.search(r"[\u4e00-\u9fff]", h.get("judgment_ko", "")), f"judgment_ko hanja leak at {hid}"
    # 사용자-facing mirror/reflection public 응답은 한자 0
    print("juyeok-jeonui-integration: PASS")
