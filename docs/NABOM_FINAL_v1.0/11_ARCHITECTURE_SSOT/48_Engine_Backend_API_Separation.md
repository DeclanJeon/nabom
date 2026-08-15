---
doc_id: SYS-ENG-API-001
title: NABOM Engine Backend API Separation
version: 1.0
status: SSOT
updated_at: 2026-08-12
---

# NABOM 사주·주역 엔진 백엔드 API 분리

## 1. 목적

사주와 주역 계산 엔진은 NABOM API와 독립 실행한다. 엔진은 private service이고, 클라이언트는 NABOM API Facade만 호출한다.

```text
Client → NABOM API Facade → Saju Engine API
                         → I Ching Engine API
```

엔진 서비스는 계정·일기·동의·페이지 권한을 소유하지 않는다. 이 책임은 NABOM API에 있다.

## 2. 목표 디렉터리

```text
backend/
├── contracts/
├── saju-engine/
├── iching-engine/
└── nabom-api/
```

현재 참조 구현:

- Saju: `saju-life-guide/saju-document/manse_engine.py`, `compatibility_engine.py`
- I Ching: `주역/engine/iching.py`, `advice.py`

참조 구현을 API에서 직접 import하는 임시 결합은 허용하지 않는다. 엔진 서비스가 자신의 계산 패키지를 소유하고 NABOM API는 HTTP client adapter를 사용한다.

## 3. 내부 엔드포인트

```text
POST /internal/v1/charts
POST /internal/v1/compatibility
POST /internal/v1/readings/cast
POST /internal/v1/reflections
GET  /healthz
GET  /readyz
```

공통 헤더:

- `Authorization: Bearer <service-token>`
- `X-Request-Id`
- `X-Contract-Version`
- `Idempotency-Key`

엔진 API는 public ingress를 만들지 않는다.

## 4. 외부 Facade 엔드포인트

```text
POST /api/v1/living/profiles/initial
POST /api/v1/living/reflections
POST /api/v1/relationships/{relationshipId}/mirror
POST /api/v1/insight-groups/{groupId}/profile
```

NABOM API는 입력 검증, 인증, 소유권, `InsightConsent`, 결과 저장, 사용자 문장, 개인정보 정책을 담당한다.

## 5. 계약 원칙

- 엔진 결과는 `engine_version`, `contract_version`, `quality_flags`, `evidence_refs`, `request_id`를 포함한다.
- raw chart와 raw hexagram reading은 기본 외부 응답에 포함하지 않는다.
- 주역 `record_reflection`은 정렬된 Evidence ID·기간·resolver version hash로 결정적으로 생성한다.
- 주역은 `TraitState` 또는 `ProfileVersion`을 직접 변경하지 않는다.
- 음력 변환 provider가 없으면 `422 LUNAR_CONVERSION_UNAVAILABLE`로 fail-closed한다.
- 관계 엔진은 양쪽 동의를 알지 못하며, API Facade가 동의 확인 후 허용된 데이터만 전달한다.
- 엔진 장애 시 stale/false 결과를 반환하지 않고 `502 ENGINE_UNAVAILABLE` 또는 `504 ENGINE_TIMEOUT`을 반환한다.

## 6. 대상 구현 모듈

```text
saju-engine/app       # HTTP adapter, validation, readiness
saju-engine/engine    # manse, compatibility, character mapping
iching-engine/app     # HTTP adapter, validation, readiness
iching-engine/engine  # cast, dataset, reflection resolver
nabom-api/services     # saju-client, iching-client, profile, mirror, relationship
nabom-api/policy       # consent, ownership, privacy
```

## 7. 검증

필수:

- 기존 사주 만세력 테스트
- 기존 사주 궁합 테스트
- 기존 주역 17개 테스트
- 각 내부 API contract test
- invalid input/fail-closed/timeout/idempotency
- private field omission
- consent revoke call blocking
- engine unavailable no-update

상세 계약은 Obsidian 문서 `NABOM_엔진백엔드_API_분리설계_v1.0.md`를 따른다.
