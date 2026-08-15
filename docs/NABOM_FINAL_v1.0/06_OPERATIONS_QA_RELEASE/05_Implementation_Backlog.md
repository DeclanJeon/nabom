---
doc_id: LEGACY-2937AE2AD2
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 06_OPERATIONS_QA_RELEASE/05_Implementation_Backlog.md
---

# 나봄(NABOM) Implementation Backlog v1.0

## Release 0: Technical Spike

목표: 1명의 사용자 데이터가 처음부터 Weekly Mirror까지 흐르는지 검증.

- [ ] 기존 사주 엔진 API 확인
- [ ] Birth Normalization
- [ ] Trait Mapper mock
- [ ] Profile 001 JSON 생성
- [ ] Daily Entry 저장
- [ ] Evidence Extractor
- [ ] Weekly Mirror mock
- [ ] NFC token redirect
- [ ] 기본 인증

완료 조건:
개발자 계정 1개로 전체 loop 수동 테스트 성공.

---

## Release 1: Internal Alpha

### P0 Identity
- [ ] nickname
- [ ] birth date
- [ ] calendar type
- [ ] birth time / unknown
- [ ] location
- [ ] current priorities
- [ ] change goal
- [ ] current goal

### P0 Profile
- [ ] Initial Profile
- [ ] trait/value/confidence
- [ ] profile feedback
- [ ] transparency page

### P0 Daily
- [ ] mood
- [ ] energy
- [ ] satisfaction
- [ ] journal
- [ ] tags

### P0 Weekly
- [ ] data coverage rule
- [ ] deterministic metrics
- [ ] partial/full mirror
- [ ] evidence refs
- [ ] growth experiment

### P0 NFC
- [ ] opaque token
- [ ] authenticated redirect
- [ ] revoke
- [ ] replacement

### P0 Privacy
- [ ] account delete
- [ ] entry delete
- [ ] privacy page
- [ ] admin RBAC

완료 조건:
내부 사용자 5명, 7일 테스트.

### Self Loop 엔진 통합 추가

- [ ] BirthAdapter: 사주 엔진 출력·quality flags·engine version 보존
- [x] CharacterMapper: 일간 오행 수호 상징·일지/연지 동반 동물
- [x] ElementBalance: 지장간 가중 오행 분포 (element_analysis.py)
- [x] DayMasterStrength: 생부/극설 비율 신강신약 후보 (element_analysis.py)
- [x] UseGodCandidates: 계절 용신 규칙 기반 후보 (element_analysis.py)
- [x] GrowthDirection: 부족 오행 성장 루틴 (element_analysis.py)
- [x] TenGods: 일간 기준 십신 산출 (element_analysis.py)
- [x] 십신표 데이터 버그 수정: 인·재·관 正/偏 60행 교정 + 표준 검증 테스트 (fatemirror 대조로 발견)
- [x] SpecialStarClassification: star_family 기반 길흉 분류 (후보 레벨)
- [x] 연운·월운 산출 (luck_analysis.py: 세운·월운, 오호둔 대상 연간, 절기 window) + /internal/v1/luck + /api/v1/living/luck
- [x] 고전 분석 모듈 (classical_analysis.py: 조후/월령/격국/순잡/상신/종합용신 후보)
- [x] 주역 한국어 역주 통합 (ingest_korean_translations.py: 64괘 괘사·효사 ko.wikisource, quality=medium, render 연동)
- [x] 카피 조립 모듈 (report_copy.py: 사용자-facing 문장 + 금지어 guardrail)
- [x] 격국 성패 후보 (pattern_success_failure: 생조/극손상 균형 — 수 0.53 생조 vs 금 0.067 극손상 → 성립 유리)
- [x] 주역 역주 품질 계층 명시 (주역전의=high/reference_only, ko.wikisource=medium/integrated)
- [x] 카피 narrative를 /internal/v1/charts 응답에 노출 (고전·성패 포함)
- [x] 상신 손상 판정 심화 (상신 보호/손상: 수 0.53 보호됨, 손상자 토 0.12 낮음)
- [x] 주역 주제별 해석 연결 (ingest_theme_interpretations.py: 7주제×64괘 매핑, 삼괘 문자 충돌 방지, get_themes + reading 첨부)
- [x] narrative를 facade 프로필 응답에 노출 (사용자-facing 문장)
- [x] 대운-세운 상호작용 해석 (luck_interaction: 천간 합충·지지 육합/충/삼합/형, 현재 대운 자동 탐색)
- [x] 십이운성 외부 대조 (위키피디아: 명칭 12·화토동법·양순음역 4/4 일치, verify_life_stage_external.py)
- [x] 주제 해석 렌더 통합 (render_reading에 주제별 해석 섹션)
- [x] 입력 검증 fail-fast (연도 범위/미래/날짜/시간/timezone → 422, 500 크래시 제거)
- [x] Idempotency-Key 구현 (같은 키+body → 동일 응답, 다른 body → 409)
- [x] 계약 스키마 강제 (chart/reading 응답 jsonschema 검증, 위반 시 500 CONTRACT_VIOLATION)
- [x] backend 엔진 복사본 드리프트 수정 (element_analysis.py 동기화 + 락 갱신)
- [x] luck year/month 쿼리 검증 (1900-2100, 1-12월 → 422)
- [x] facade Idempotency-Key (SQLite 영속, 중복 프로필/회고 방지)
- [x] 관계 생성 시 출생 입력 fail-fast 검증
- [x] 에러 메시지 위생화 (내부 env·경로 비노출)
- [x] mirror scope enforcement 테스트 (character_profile 한정 시 오행 feature 제외)
- [x] dead code 정리 (미사용 import/상수)
- [x] 교차 사용자 접근 차단: 관계 evidence/consent/revoke는 participant 전용, 그룹 프로필/그룹간 분석은 member 전용 (403)
- [x] facade 엔진 4xx 전파 (입력 오류 422 유지, 5xx만 502)
- [x] SQLite WAL + busy_timeout (동시성 lock 방지, 동시 생성 8건 테스트)
- [x] group_to_group deficient 논리 버그 수정 (각 그룹 실제 deficient 참조)
- [x] pyflakes 클린 (미사용 import 전량 제거)
- [x] ReflectionAdapter: 결정적 record_reflection resolver
- [x] CanonicalReflection schema validation (contracts/reflection.schema.json + jsonschema)
- [x] raw 주역 데이터 비노출 narrative adapter (facade 검증)
- [x] rejected hypothesis active profile 차단 (feedback API + 활성 제외)
- [x] lunar/leap-month dependency fail-closed (윤달 미지정 422, 설치 시 검증 변환)

### 독립 엔진 API 분리

- [x] `saju-engine` 독립 package/service (FastAPI, 번들 provider)
- [x] `iching-engine` 독립 package/service (FastAPI, reflection resolver)
- [x] 공통 JSON Schema 계약 (backend/contracts)
- [x] NABOM API `saju-client`/`iching-client` adapter (facade)
- [x] private service token 계약 / public ingress 차단
- [x] engine health/readyz와 dataset/provider provenance
- [x] engine timeout/error 매핑 (502/504)
- [x] engine idempotency/request trace 계약
- [x] raw chart/raw reading 외부 응답 차단
- [x] API contract test + 기존 engine test 통과
- [x] 릴리스 해시 게이트 (release/verify_engine_lock.py + lock manifests)
- [x] 서비스 토큰 로테이션 (SAJU_SERVICE_TOKENS overlap)

### 엔진 품질 후속 (평가 기반)

- [x] element_analysis 모듈 및 테스트
- [x] 절기 provider 번들 로드 및 strict fail-closed
- [x] 근사 절기 플래그 시 정밀 판단 금지 enforcement
- [x] 신살 표 내부 대조(표준 12신살표 4/4 일치)
- [x] 오행·강약·용신 결과 → Trait 후보 매핑 (facade)
- [x] 신살 표 외부 대조 (위키피디아 ko 신살/사주팔자 기준 64건 일치, backend/tests/verify_shinsal_external.py)

### Relationship / InsightGroup Alpha

- [x] Relationship consent state machine (DRAFT→CONSENT_PENDING→ACTIVE→PAUSED→REVOKED, domain.py)
- [x] public trait scope enforcement (SCOPE_FEATURES별 feature 필터)
- [x] RelationshipMirror A→B/B→A/shared output (rule_code 방향성 분해)
- [x] RelationshipEvidence immutable event (append-only)
- [x] InsightGroup minimum-five aggregate gate (활동 멤버+프로필 5명 미만 추론 차단)
- [x] GroupBuy와 InsightGroup 권한 분리 (별도 라우트/도메인)
- [x] GroupProfile anonymization (k_anonymous, mean ratio만 노출)
- [x] group-to-group insight aggregate-only output

---

## Release 2: FIRST 10

- [ ] 주문 폼
- [ ] 사진 업로드
- [ ] 제작상태 admin
- [ ] NFC mapping admin
- [ ] shipment state
- [ ] QR fallback
- [ ] analytics events
- [ ] AI cost logging
- [ ] CS template
- [ ] Day 21 report
- [ ] interview form

완료 조건:
10개 실제 제작/배송/사용 완료.

---

## Release 3: FIRST 100

- [ ] 장애 모니터링
- [ ] rate limit
- [ ] queue/retry
- [ ] LLM fallback
- [ ] weekly generation scheduler
- [ ] user notification
- [ ] experiment feedback
- [ ] conversion dashboard
- [ ] cohort dashboard

완료 조건:
100명 판매 가능한 운영체계.

---

# P0 상세 QA

## Birth
- [ ] 음력 입력
- [ ] 윤달
- [ ] 해외 출생
- [ ] DST
- [ ] timezone
- [ ] 출생시간 미상
- [ ] 위치 검색 실패
- [ ] 엔진 version/quality flag trace
- [ ] 음력 의존성 미설치 fail-closed

## Profile
- [ ] confidence 낮을 때 단정 금지
- [ ] profile feedback 반영
- [ ] 상충 Evidence
- [ ] 잘못된 분석 report

## Daily
- [ ] 빈 일기
- [ ] 매우 긴 일기
- [ ] emoji
- [ ] 다국어
- [ ] duplicate submission
- [ ] timezone rollover

## Weekly
- [ ] 0일 기록
- [ ] 1일 기록
- [ ] 2일 기록
- [ ] 3~4일
- [ ] 5~7일
- [ ] 부정 Evidence
- [ ] 상충된 감정
- [ ] 숫자 hallucination 금지

## NFC
- [ ] token brute force 방지
- [ ] revoke
- [ ] lost keyring
- [ ] logged out
- [ ] wrong account
- [ ] public/private
- [ ] iPhone
- [ ] Samsung/Android
- [ ] QR fallback

## Relationship / InsightGroup

- [ ] one-sided consent cannot activate relationship
- [ ] consent revoke suspends new and existing insight
- [ ] private trait/journal/evidence scope cannot leak
- [ ] A→B and B→A contribution direction
- [ ] rejected hypothesis does not reappear
- [ ] fewer than 5 active members blocks individual inference
- [ ] GroupBuy does not auto-create InsightGroup membership
- [ ] group-to-group output cannot reverse-identify a member

---

# 운영 관리자 화면 최소 기능

## Orders
- 주문상태
- 사진
- 디자인상태
- 수정요청
- 제작상태
- 배송상태

## NFC
- token
- user
- status
- last tap
- revoke
- replacement

## Users
- activation state
- profile status
- entry count
- weekly status

관리자는 raw journal을 기본 목록에서 볼 수 없어야 한다.

---

# 기술적 비기능 요구

- idempotent weekly generation
- retry-safe jobs
- LLM structured JSON validation
- schema versioning
- prompt versioning
- profile versioning
- evidence immutability
- audit log
- rate limits
- error reporting
- feature flags

---

# 추천 도메인 모듈

```text
auth
users
birth-profile
trait-engine
profile
journal
evidence
mirror
experiments
nfc
orders
media
notifications
analytics
admin
```

---

# 가장 먼저 만들 것

UI를 많이 만들기 전에 아래를 먼저 검증한다.

```text
Birth Input
→ Trait JSON
→ Profile 001
→ Journal
→ Evidence JSON
→ Weekly Mirror JSON
→ Growth Experiment
```

이 데이터 파이프가 안정적이면 화면은 그 다음이다.


---

# 프로젝트/저장소 명명 규칙

```text
nabom-web       # 사용자 웹앱
nabom-api       # API
nabom-worker    # Weekly Mirror / AI jobs
nabom-admin     # 주문/NFC/운영 관리
```

내부 package/module:

```text
auth
users
birth-profile
living-self-engine
trait-engine
profile
journal
evidence
mirror
experiments
nfc
orders
media
notifications
analytics
admin
relationship
insight-group
consent
reflection-adapter
character-mapper
```

환경별 권장 URL:

```text
Production: https://nabom.ponslink.com
Staging:    https://nabom-stg.ponslink.com
API:        내부 reverse proxy 또는 /api 우선
Admin:      가능하면 별도 인증 경로 /admin
```
