---
doc_id: NABOM-P0-001
title: NABOM Phase 0 Design (엔진 기반)
version: 1.0
status: SSOT
updated_at: 2026-08-13
scope: Phase 0 — 사주·주역 엔진 독립 서비스 계약
---

# NABOM Phase 0 설계서 — 사주·주역 엔진 기반

## 0. 문서 목적과 전제

이 문서는 **모든 Phase가 공통으로 의존하는 엔진 기반 계약**이다.

- 사주와 주역 계산 엔진은 NABOM API와 **독립 실행**한다. 엔진은 private service이고, 모든 클라이언트(웹·API)는 **NABOM API Facade만 호출**한다.
- 엔진 서비스는 계정·일기·동의·페이지 권한을 **소유하지 않는다**. 이 책임은 NABOM API에 있다.
- Phase 0은 전제 조건으로 이미 구축·검증된 상태를 기준선(SSOT)으로 삼는다. 이후 Phase(1~3)는 이 계약 위에 쌓는다.

```text
Client → NABOM API Facade → Saju Engine API    (private :8001)
                          → I Ching Engine API  (private :8002)
```

---

## 1. 목표 디렉터리

```text
backend/
├── contracts/          # 공통 JSON Schema 계약
├── saju-engine/        # 사주 엔진 서비스
├── iching-engine/      # 주역 엔진 서비스
└── nabom-api/          # Facade (엔진 client adapter 포함)
```

### 참조 구현 (기준)

- Saju: `saju-life-guide/saju-document/manse_engine.py`, `compatibility_engine.py`
- I Ching: `주역/engine/iching.py`, `advice.py`

**참조 구현을 API에서 직접 import하는 임시 결합은 허용하지 않는다.** 엔진 서비스가 자신의 계산 패키지를 소유하고, NABOM API는 HTTP client adapter를 사용한다.

---

## 2. 내부 엔드포인트 (private)

```text
POST /internal/v1/charts          # 만세력 + Trait/Character 후보
POST /internal/v1/compatibility   # 궁합 근거 (Phase 2에서 사용)
POST /internal/v1/readings/cast   # 실제 점괘 모드 (별도 도입 시)
POST /internal/v1/reflections     # 결정적 record_reflection (주역 회고)
GET  /healthz
GET  /readyz
```

### 공통 헤더

```text
Authorization: Bearer <service-token>
X-Request-Id
X-Contract-Version
Idempotency-Key
```

- 엔진 API는 **public ingress를 만들지 않는다.** 브라우저·외부 클라이언트는 반드시 NABOM Facade 라우트를 사용한다.
- 서비스 토큰은 순환(rotation) 지원: `SAJU_SERVICE_TOKENS` overlap 방식.

---

## 3. 외부 Facade 엔드포인트

```text
POST /api/v1/living/profiles/initial            # Phase 1: Profile 001
POST /api/v1/living/reflections                 # Phase 1: 주간 회고
POST /api/v1/relationships/{relationshipId}/mirror  # Phase 2: 관계 회고
POST /api/v1/insight-groups/{groupId}/profile   # Phase 3: 그룹 프로필
```

NABOM API는 다음을 담당한다: 입력 검증, 인증, 소유권, `InsightConsent`, 결과 저장, 사용자 문장, 개인정보 정책.

---

## 4. 계약 원칙

- 엔진 결과는 `engine_version`, `contract_version`, `quality_flags`, `evidence_refs`, `request_id`를 포함한다.
- raw chart와 raw hexagram reading은 **기본 외부 응답에 포함하지 않는다.** Facade가 canonical user-facing schema로 변환한다.
- 주역 `record_reflection`은 정렬된 Evidence ID·기간·resolver version hash로 **결정적으로 생성**한다. (상세 규칙은 Phase 1 설계서 §3.4)
- 주역은 `TraitState` 또는 `ProfileVersion`을 **직접 변경하지 않는다.**
- 음력 변환 provider가 없으면 `422 LUNAR_CONVERSION_UNAVAILABLE`로 **fail-closed**한다.
- 관계 엔진은 양쪽 동의를 알지 못한다. **API Facade가 동의 확인 후 허용된 데이터만 전달**한다.
- 엔진 장애 시 stale/false 결과를 반환하지 않고 `502 ENGINE_UNAVAILABLE` 또는 `504 ENGINE_TIMEOUT`을 반환한다.

---

## 5. 대상 구현 모듈

```text
saju-engine/app       # HTTP adapter, validation, readiness
saju-engine/engine    # manse, compatibility, character mapping
iching-engine/app     # HTTP adapter, validation, readiness
iching-engine/engine  # cast, dataset, reflection resolver
nabom-api/services     # saju-client, iching-client, profile, mirror, relationship
nabom-api/policy       # consent, ownership, privacy
```

---

## 6. 엔진 기준 포함 항목 (검증 완료 기준)

| 영역 | 내용 |
|---|---|
| 출생 처리 | BirthAdapter(엔진 출력·quality flags·engine version 보존), 음력/윤달 fail-closed, 절기 provider 번들 |
| 사주 계산 | ElementBalance, DayMasterStrength, UseGodCandidates, GrowthDirection, TenGods, SpecialStarClassification, 연운·월운, 고전 분석(조후/월령/격국/순잡/상신/종합용신), 격국 성패, 상신 손상 판정, 대운-세운 상호작용 |
| 캐릭터 | CharacterMapper(일간 오행 → 수호 상징, 일지/연지 동반 동물) |
| 주역 | 64괘 괘사·효사 역주(ko.wikisource quality=medium, 주역전의 quality=high/reference_only), 주제별 해석(7주제×64괘), 결정적 record_reflection resolver |
| 카피 | report_copy(사용자-facing 문장 + 금지어 guardrail), narrative를 Facade 응답에 노출 |
| 계약/안정성 | 입력 검증 fail-fast(422), Idempotency-Key(동일 키+body → 동일 응답, 다른 body → 409), 계약 스키마 강제(jsonschema, 위반 시 500 CONTRACT_VIOLATION), 에러 메시지 위생화, facade Idempotency-Key 영속(SQLite), WAL + busy_timeout, 4xx 전파(5xx만 502) |
| 외부 대조 | 십이운성(위키피디아), 신살 표(표준 12신살표/위키피디아 ko) |
| 운영 | engine health/readyz, dataset/provider provenance, 릴리스 해시 게이트(verify_engine_lock.py + lock manifests), 서비스 토큰 로테이션 |

---

## 7. 검증 (필수)

- 기존 사주 만세력 테스트
- 기존 사주 궁합 테스트
- 기존 주역 17개 테스트
- 각 내부 API contract test
- invalid input / fail-closed / timeout / idempotency
- private field omission (raw chart·raw reading 비노출)
- consent revoke call blocking (Phase 2 이후)
- engine unavailable no-update

---

## 8. Phase 간 의존성

- Phase 1: `POST /internal/v1/charts`, `POST /internal/v1/reflections`, `/healthz`, `/readyz` 사용.
- Phase 2: 추가로 `POST /internal/v1/compatibility` (궁합 근거) 사용.
- Phase 3: Phase 2의 관계 분석을 그룹 단위로 집계. 엔진은 그대로, 집계·익명화는 NABOM API 책임.
