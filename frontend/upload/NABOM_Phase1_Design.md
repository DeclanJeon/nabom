---
doc_id: NABOM-P1-001
title: NABOM Phase 1 Design (나↔나 MVP)
version: 1.0
status: SSOT
updated_at: 2026-08-13
depends_on:
  - saju-engine (private :8001)
  - iching-engine (private :8002)
scope: Phase 1 개발 전용
---

# NABOM Phase 1 설계서 — 나와 나의 연결 (MVP)

## 0. 문서 목적과 전제

이 파일 하나로 **Phase 1 개발을 진행**한다.

- **사주엔진(`saju-engine`), 주역엔진(`iching-engine`)은 이미 존재한다는 전제**로 설계한다. 프론트엔드와 NABOM API는 엔진을 직접 호출하지 않고 **Facade 계약**만 사용한다.
- 범위는 **나 ↔ 나** 세 가지뿐이다: **프로필 생성 → 기록으로 자기 업데이트 → 회고로 자신을 입체적으로 이해**.
- **제외**: 커머스(상품·주문·결제·배송·공동구매·글로벌 판매), NFC/키링/QR 페이지(유저에게 노출하지 않음), 타인 연결, 그룹 연결. 이 항목들은 전체 로드맵 `NABOM_Phased_MVP_Design.md`의 Phase 2/3·보류로 둔다.
- 개발 순서: **데이터 파이프 검증(Release 0) → Internal Alpha(Release 1)**. UI를 많이 만들기 전에 `Birth Input → Trait JSON → Profile 001 → Journal → Evidence JSON → Weekly Mirror JSON → Growth Experiment`가 안정적인지 먼저 확인한다.

---

## 1. 제품 정의

### 1.1 식별자

| 항목 | 값 |
|---|---|
| 프로젝트명 | 나봄 (NABOM) |
| 메인 도메인 | `https://nabom.ponslink.com` |
| 내부 핵심 엔진 | Living Self Engine (LSE) |
| 브랜드 문장 | 기록할수록 선명해지는 나. |
| 보조 문장 | 오늘의 나는, 어제의 나와 조금 다르니까. |

### 1.2 제품 정체성

사주 앱·성격검사 앱·일기 앱·AI 상담 앱 중 하나로 정의하지 않는다. **여러 입력과 실제 삶의 기록을 통해 시간에 따라 변화하는 한 사람의 Living Profile을 만드는 서비스**다.

- 사용자에게 "사주 서비스"로 보이지 않는다. 출생정보는 가입 과정의 자연스러운 프로필 정보로 입력받고, 명리 계산 결과는 내부 Trait Candidate 생성에만 사용한다.
- 분석 방법은 허위로 표현하지 않는다. 설정의 분석 방법 고지 화면에서 "출생정보 기반 전통 명리 체계가 초기 가설에 포함됨"을 명시한다.

### 1.3 해결 문제

- **P1** 사람은 자신을 장기적으로 객관화하기 어렵다. 일기를 기록해도 과거를 다시 읽고 패턴을 찾는 비용이 높다.
- **P2** 성격검사는 한 번의 결과로 사람을 고정한다. 시간에 따라 변화하는 실제 삶과 분리된다.
- **P3** AI 대화는 순간에는 유용하지만 장기적인 삶의 변화가 구조화되지 않는다.
- **P4** 자기계발 앱은 너무 많은 입력과 행동을 요구해 이탈이 빠르다.

### 1.4 가치 타임라인

| 시점 | 사용자가 느끼는 것 |
|---|---|
| 첫날 | "이거 나랑 조금 비슷한데?" |
| 1주 | "내가 이런 패턴으로 움직이고 있었구나." |
| 1개월 | "내가 생각했던 나와 실제 기록된 내가 조금 다르네." |
| 3개월 | "내가 바뀌고 있다는 게 보인다." |
| 6개월+ | "이 서비스가 내 과거의 나를 내가 기억하는 것보다 더 입체적으로 보여준다." |

### 1.5 핵심 제품 루프

```text
기본정보 등록
  → Profile 001 생성
  → Daily Check-in / Journal
  → Evidence 축적
  → Weekly Mirror
  → Hypothesis 제안
  → 사용자 피드백
  → Growth Experiment
  → 다시 실제 삶 기록
  → Monthly Profile Update
```

### 1.6 사용자-facing 용어

**사용**: 나봄, 프로필, 오늘의 나, Weekly Mirror(또는 "이번 주의 나"), 성장 테마, 작은 실험, 여정.

**기본 화면에서 피함**: 사주, 팔자, 일간, 십성, 용신, 대운, 세운, 오행 점수. (분석 방법 설명 화면에서는 투명하게 고지)

---

## 2. 시스템 아키텍처

```text
Client (브라우저)
  └─ nabom-web (Next.js)
       └─ nabom-api (Facade) ─┬─→ saju-engine   (private :8001)
                              └─→ iching-engine (private :8002)
       └─ PostgreSQL / Redis / Object Storage
       └─ nabom-worker (Weekly Mirror · AI · 알림 · 정리)
```

### 2.1 배포 단위

| 단위 | 역할 |
|---|---|
| `nabom-web` | Next.js. Living UI 전담(온보딩·오늘·프로필·회고·여정·설정). Admin은 초기 동일 코드베이스의 보호된 영역 가능. |
| `nabom-api` | Next.js Route Handler 또는 Node API. 인증, Living Profile API, 엔진 client adapter, 동의/개인정보 정책. |
| `nabom-worker` | 비동기 잡: AI 생성, Weekly Mirror, 알림, cleanup. 잡은 idempotency, retry, DLQ, 관측 가능성 필수. |
| `PostgreSQL` | 트랜잭션 SSOT. 스키마 모듈: `identity`, `living`, `audit`. 민감한 Journal/Birth data는 권한·조회경로 강하게 분리. |
| `Redis` | 큐, 분산 락, 단기 캐시, rate limit. |
| `Object Storage` | private 업로드(사진 등), 생성 에셋. |

### 2.2 엔진 서비스 경계

- `nabom-api`는 계산 엔진을 내장하지 않고 **private engine API client**로 호출한다.
- 엔진은 public ingress가 없다. 호출 헤더: `Authorization: Bearer <service-token>`, `X-Request-Id`, `X-Contract-Version`, `Idempotency-Key`.
- 엔진 raw 결과(만세력 chart, raw hexagram)는 Facade가 canonical user-facing schema로 변환하기 전 외부에 노출하지 않는다.
- 엔진 장애 시 stale/false 결과를 반환하지 않고 `502 ENGINE_UNAVAILABLE` / `504 ENGINE_TIMEOUT` 반환. 음력 변환 provider 부재 시 `422 LUNAR_CONVERSION_UNAVAILABLE`로 fail-closed.

### 2.3 환경 / 배포 원칙

- 환경: `local` / `staging` / `production`. Production DB와 staging은 완전 분리.
- 기능 출시는 코드 배포와 분리(Feature Flags). Phase 1 플래그 후보: `weekly_mirror`, `record_reflection`, `reflection_intensity`, `photo_upload`.
- 동기 요청에서 오래 걸리는 작업(LLM 생성 등) 금지 — 모두 worker로.

### 2.4 Trust Boundary

- Public: 랜딩
- Authenticated Customer: 프로필, 기록, 회고, 여정, 설정
- Operator: 관리자 기본 도구
- Privileged: 민감 데이터(Journal/Birth)

권한은 UI가 아니라 **API에서 강제**한다.

---

## 3. 엔진 통합 계약

### 3.1 엔드포인트

**Facade (프론트엔드가 사용하는 유일한 경로):**

```text
POST /api/v1/living/profiles/initial   # 온보딩 완료 → Profile 001
POST /api/v1/living/reflections        # 주간 회고 생성 (Weekly Mirror + 주역)
```

**내부 엔진 (Phase 1 사용분):**

```text
POST /internal/v1/charts        # 사주: 출생 정규화 → 만세력 → Trait/Character 후보
POST /internal/v1/reflections   # 주역: 결정적 record_reflection
GET  /healthz
GET  /readyz
```

`/internal/v1/compatibility`(궁합), `/internal/v1/readings/cast`(실제 점괘)는 Phase 2 이후 사용.

### 3.2 Birth Hypothesis 파이프라인

```text
BirthInput
  → BirthAdapter
  → Manse Chart + Quality Summary (quality_flags, engine_version 보존)
  → TraitMapper (일간·일지·오행 균형·십신 → Trait Candidate)
  → CharacterMapper (일간 오행 → 시각 언어)
  → Profile 001
```

- 명리 raw result를 LLM에 그대로 던져 사용자 문장을 생성하지 않는다. 반드시 구조화 계층(Trait Candidate + strength + caveat)을 거친다.
- **fail-closed**: 음력·윤달 변환이 검증되지 않거나 출생시간이 없으면 양력/시간을 추정하지 않는다. 절기 경계, 자시 후보, DST, 역사적 timezone은 quality flag를 남기고 초기 confidence를 낮춘다.
- 출생시간 미상: 시주 관련 계산 제외 → 파생 Trait Candidate 제외 → 전체 confidence 감소 → "시간을 몰라도 사용 가능" 안내. 대략적인 시간대를 정확한 시각처럼 취급하지 않는다.
- CharacterMapper 시각 언어(진단이 아니라 사용자가 수정·거부할 수 있는 표현): 목 → 청룡, 화 → 주작, 토 → 황룡, 금 → 백호, 수 → 현무.
- 초기 Trait 후보 풀: 탐색, 실행, 지속, 연결, 회복, 구조, 표현. 각 trait은 `value`와 `confidence`를 별도 관리.

### 3.3 데이터 우선순위 (시간이 지날수록)

1. 반복된 실제 행동/기록
2. 명시적 사용자 피드백
3. 구조화된 self-report
4. 단기 감정 체크
5. 출생정보 기반 초기 가설

고정 가중치는 제품 문구로 노출하지 않는다.

### 3.4 주역 회고 미들웨어 (ReflectionAdapter)

주역 엔진은 성격·프로필을 결정하지 않고 **기록 기간의 현재 국면을 해석하는 어댑터**로만 사용한다.

```text
DailyEntry snapshot → Evidence extraction → Deterministic metrics
  → ReflectionContext → I Ching Situation Resolver → Canonical Reflection
  → Growth Recommendation → LLM Narrative → Safety/Evidence Check → Weekly Mirror
```

**결정적 resolver 규칙:**
1. canonical hash 입력은 **정렬된 Evidence ID, 분석 기간, `resolver_version`** 만 사용한다.
2. 사용자 ID, 현재 시각, 외부 random API를 seed에 포함하지 않는다.
3. hash를 결정적으로 6개의 값(6,7,8,9)으로 매핑하고 매핑 버전(`cast_mapping_version`)을 저장한다.
4. 매핑된 값은 `resolve_casts`에 bottom-to-top 순서로 전달한다.
5. 동일 snapshot replay는 동일 본괘·동효·지괘를 반환해야 한다.
6. 실제 점괘 모드와 기록 기반 회고는 분리하고, 기록 기반 회고는 `mode: record_reflection`으로 표시한다.

**Canonical Reflection이 제공하는 것 (4가지):**
1. 현재 국면
2. 다음 기록에서 볼 관찰 초점
3. 과잉 해석·속도·회피에 대한 주의 신호
4. 1주 안에 실행 가능한 단일 가역 행동

- 저장 시 감사 필드 보존: `resolver_input_hash`, `cast_mapping_version`, `raw_reading_internal_ref`, `classical_source_refs`, `generated_at`.
- LLM에는 raw 괘 데이터를 전달하지 않는다. 구조화된 Reflection과 Evidence reference만. 기본 화면은 괘명·고전 원문보다 "이번 주의 흐름", "살펴볼 점", "작은 실험"을 우선한다.
- **LLM 전에 가능한 계산은 코드로 처리한다**: 기록 일수, 평균 기분/에너지, 태그 빈도, 목표 행동 횟수, 실험 이행 여부. LLM은 계산값을 만들어내지 않는다.

### 3.5 Confidence 레벨

| 구간 | 레벨 | 사용자 문구 |
|---|---|---|
| 0.00~0.29 | 탐색 단계 | "이런 가능성이 조금 보여요." |
| 0.30~0.49 | 약한 가설 | — |
| 0.50~0.69 | 중간 가설 | "최근 기록에서는 이런 경향이 몇 차례 보였어요." |
| 0.70~0.84 | 반복 관찰 | — |
| 0.85+ | 강한 반복 관찰 | "지난 몇 주 동안 이 패턴이 반복해서 나타났어요." |

높은 `value`와 높은 `confidence`는 다른 개념이다.

### 3.6 Pattern 정의

- 조건: 동일/유사 Evidence가 한 주 내 3회 이상, 또는 2주 이상 반복, 또는 서로 다른 Evidence source에서 동일 방향 확인.
- 조건 미달 시: "가능성", "이번 주에는 이런 모습이 보임", "아직 확인이 필요함"으로 표현.
- 한 번의 사건으로 패턴 생성 금지, 반대 Evidence도 저장, 최근 데이터만으로 과거 전체를 일반화하지 않는다.
- 상충 Evidence는 억지로 합치지 않고 축을 분리해 새 Hypothesis를 만들 수 있다.

---

## 4. 데이터 모델 (Phase 1)

핵심 스키마 초안. 구현 시 계약 문서로 versioning한다.

```jsonc
// BirthInput
{ "calendar": "solar", "date": "1992-03-01", "time": "07:20",
  "time_precision": "exact | approximate | unknown",
  "location": { "label": "...", "lat": 0, "lon": 0, "timezone": "Asia/Seoul" } }

// UserProfile
{ "user_id": "usr_x", "nickname": "...", "timezone": "Asia/Seoul",
  "created_at": "..." }

// ProfileVersion (overwrite하지 않고 versioning: 001 → 002 → ...)
{ "profile_version_id": "pv_001", "number": 1, "created_at": "...",
  "identity_sentence": "...", "traits": [], "strengths": [],
  "watch_patterns": [], "growth_theme": "...", "evidence_cutoff": "..." }

// TraitState
{ "trait": "exploration", "value": 0.76, "confidence": 0.61,
  "source_counts": { "birth_hypothesis": 1, "self_report": 2,
                     "journal": 7, "profile_feedback": 1 } }

// CharacterProfile (시각적 표현, 사용자 수정/거부 가능)
{ "character_profile_id": "cp_x", "profile_version_id": "pv_001",
  "day_stem": "병화", "representative_element": "fire",
  "guardian_beast": { "code": "jujak", "label_ko": "주작",
                      "source": "day_stem_element" },
  "user_editable": true, "status": "active" }

// DailyEntry (필수: mood/energy/satisfaction 1~5 + 한 줄)
{ "entry_id": "entry_x", "date": "2026-08-12", "mood": 3, "energy": 2,
  "satisfaction": 4, "text": "...", "tags": ["work", "relationship"] }

// Evidence (append-only. 원문과 AI 해석 분리 저장)
{ "evidence_id": "ev_x", "user_id": "usr_x",
  "type": "self_report | daily_checkin | journal | goal_action | experiment_result | profile_feedback | weekly_feedback | birth_hypothesis",
  "occurred_at": "...", "source_record_id": "entry_x",
  "signals": [{ "trait": "persistence", "direction": "positive", "strength": 0.33 }],
  "summary": "...", "status": "active" }

// PatternHypothesis
{ "pattern_id": "pat_x", "title": "...", "confidence": 0.68,
  "status": "hypothesis", "evidence_ids": [], "counter_evidence_ids": [],
  "first_seen_at": "...", "last_seen_at": "..." }

// WeeklyMirror
{ "mirror_id": "wm_x", "period": { "from": "...", "to": "..." },
  "coverage": { "days_recorded": 5, "mode": "full | partial | light" },
  "summary": "...", "notable_moments": [], "emotion_flow": [],
  "energy_gainers": [], "energy_drainers": [], "patterns": [],
  "changes_from_last_week": [], "hypotheses": [],
  "growth_experiment_id": "exp_x", "generated_at": "...", "prompt_version": "weekly-v1" }

// CanonicalReflection (Profile을 직접 변경하지 않음)
{ "reflection_id": "rf_x", "mode": "record_reflection",
  "resolver_version": "iching-reflection-v1", "context_refs": ["wm_x"],
  "situation": { "code": "transition_with_waiting", "confidence": 0.62 },
  "observation_focus": [], "caution_signals": [],
  "recommended_action": { "title": "...", "instruction": "...",
                          "success_condition": "...", "reversible": true },
  "evidence_refs": [] }

// GrowthExperiment (단일 행동, 실행 기간, 성공 조건, 관찰 대상, 가역성 필수)
{ "experiment_id": "exp_x", "title": "...", "instruction": "...",
  "success_condition": "...", "status": "accepted", "user_result": null }

// ProfileFeedback
{ "feedback_id": "pf_x", "profile_version_id": "pv_001",
  "target_type": "trait", "target_key": "exploration",
  "rating": "correct | mostly_correct | situational | unsure | incorrect",
  "comment": "...", "created_at": "..." }
```

---

## 5. 상태 규칙

- **Evidence는 append-only(불변).** 삭제 시 raw entry 비활성 → derived Evidence invalidate → Pattern 재계산 → Profile 영향 표시.
- **Profile은 versioning.** AI가 매일 Profile을 직접 수정하지 않는다: Daily(Evidence 추출) → Weekly(Pattern 후보) → Monthly/충분한 Evidence(Profile Update Proposal) → User(확인/수정/거절) → System(새 ProfileVersion).
- **Weekly Mirror coverage**: 기록 0일 → 생성 안 함 / 1~2일 → `Light Reflection`(패턴 단정 금지) / 3~4일 → `Partial Mirror` / 5일 이상 → `Full Weekly Mirror`.
- 거절된 가설은 학습용으로 보존하되 active profile에는 반영하지 않는다.
- idempotent: 같은 기간·같은 Evidence snapshot·같은 resolver version이면 같은 회고 결과.

---

## 6. URL / 라우트

```text
/            # 랜딩 (서비스 소개)
/welcome     # 온보딩 (프로필 생성)
/today       # 오늘의 나 (Daily Check-in + Journal)
/profile     # 내 프로필 (Profile version + 피드백)
/mirror      # Weekly Mirror (회고)
/journey     # 여정 (프로필 버전 이력, 장기 변화)
/settings    # 설정 (계정, 알림, 데이터 내보내기/삭제, 분석 방법 고지)
```

- 내부 정수 ID를 URL에 노출하지 않는다. public token은 opaque random.
- `/k/{token}`, `/relationships`, `/groups`, 커머스 경로는 Phase 1에 없음.

---

## 7. 화면/UX 정의 (프론트엔드)

프론트엔드는 Facade API 계약 기준으로 개발한다. 엔진 준비 전에는 계약 기반 mock으로 병행 개발한다.

### 7.1 API 표면 초안 (화면 ↔ Facade)

| 화면 | API | 책임 |
|---|---|---|
| 온보딩 완료 | `POST /api/v1/living/profiles/initial` | Profile 001 생성 (BirthInput 포함) |
| 프로필 조회 | `GET /api/v1/living/profiles/current` | 현재 ProfileVersion + CharacterProfile |
| 프로필 피드백 | `POST /api/v1/living/profiles/feedback` | 피드백 저장, 가설 수정/거절 |
| 오늘 기록 | `GET/POST /api/v1/living/entries` | DailyEntry 저장/조회 |
| 회고 생성 | `POST /api/v1/living/reflections` | Weekly Mirror + Canonical Reflection |
| 회고 조회 | `GET /api/v1/living/reflections/latest` | 최신/과거 회고 |
| 실험 | `POST /api/v1/living/experiments` | Growth Experiment 수락/결과 입력 |
| 여정 | `GET /api/v1/living/journey` | 프로필 버전 이력, 장기 요약 |
| 계정 | `POST /api/v1/auth/*`, `DELETE /api/v1/account` | 인증, 탈퇴 |

(위 표면은 초안. 구현 시 계약 문서로 확정한다.)

### 7.2 온보딩 (`/welcome`, 8단계)

1. 안내: "처음에는 몇 가지 정보로 프로필을 만들고, 앞으로의 기록을 통해 계속 당신을 알아갑니다." CTA: `내 프로필 만들기`
2. 이름 또는 닉네임
3. 생년월일 + 양력/음력
4. 출생시간: 정확한 시간 / 대략적인 시간대 / 모르겠어요 ("모름"이어도 이용 가능, 시주 기반 요소 제외)
5. 출생지역
6. 현재 가장 중요한 영역 (복수선택)
7. 지금 바꾸고 싶은 것
8. 지금 이루고 싶은 것 (선택 입력)

→ 완료 시 Profile 001 생성

### 7.3 Profile 001 (`/profile`)

"점괘"가 아니라 **개인 캐릭터 시트 + 성장 리포트**로 표현:

- 치비 아바타 (CharacterProfile 기반)
- Profile Number / Date
- 지금의 나를 설명하는 한 문장
- 핵심 성향 5~7개 (TraitState)
- 내가 가진 힘 3개
- 조심해서 볼 패턴 2~3개
- 현재 성장 테마 1개
- "이 설명이 나와 얼마나 비슷한가요?" 피드백 (맞아요 / 어느 정도 맞아요 / 상황에 따라 달라요 / 잘 모르겠어요 / 아니에요 + "어떤 부분이 다른가요?")

### 7.4 오늘의 나 (`/today`)

- 필수 최소 입력(30초~3분): 기분 1~5, 에너지 1~5, 만족도 1~5, 오늘 기억하고 싶은 한 줄
- 선택: 집중, 관계, 태그, 자유일기, 사진 (음성은 Phase 2)
- 적응형 질문: 기본 3개 지표 + confidence가 낮거나 상충하는 성향 하나를 고른 가벼운 질문 1개
- Daily AI는 장문 분석을 하지 않는다. 예: "오늘은 '기대'와 '불확실함'이 함께 있었던 날로 보이네요. 기록해둘게요." — "매일 AI에게 평가받는다"는 느낌을 주지 않는다.

### 7.5 Weekly Mirror (`/mirror`)

구성:
1. 이번 주 한 문장
2. 주요 장면
3. 감정 흐름
4. 에너지 상승/하락 요인
5. 반복된 생각/행동
6. 관계 또는 목표 패턴
7. 지난주와 달라진 점
8. 현재 가설
9. 사용자 확인
10. 다음 주 작은 실험 (Growth Experiment)

- "왜 이렇게 봤나요?": 주요 insight마다 내부 Evidence를 연결. 어떤 날짜 기록에서 봤는지, 어떤 표현/수치가 영향을 줬는지, 아직 확실하지 않은지를 짧게 보여준다. AI chain-of-thought가 아니라 **사용자 데이터 근거**.
- 목표 관리 통합: 이번 주 목표 관련 행동, 진척 신호, 방해 요인, 목표 자체가 여전히 중요한지. 월 1회 "이 목표는 아직 당신에게 중요한가요?"

### 7.6 여정 (`/journey`)

- Profile version 이력(001 → 002 → ...), 장기 변화 요약.
- "내가 말한 나 vs 기록된 나": 최소 4주 데이터에서 활성화.

### 7.7 설정 (`/settings`)

- 계정, 알림 설정, 데이터 내보내기(JSON + Markdown), 데이터 삭제/탈퇴, 분석 방법 고지.

### 7.8 Reflection Intensity (MVP 옵션 후보)

- Reflect: 해석 중심, 행동 제안 최소
- Grow: 기본값, 작은 행동 실험 제안
- Challenge: 반복되는 회피/모순을 비교적 적극적으로 지적 (안전 영역 한정, 진단/강압적 조언 금지)

### 7.9 문구 원칙

피해야 함: "당신은 원래 이런 사람입니다." / "당신은 반드시…" / "당신의 운명은…" / "당신은 이 유형이 확실합니다." / "AI가 판단하기에…"
권장: "현재 기록에서는…" / "지금까지는 이런 경향이 보입니다." / "이 가설이 당신에게도 맞게 느껴지나요?" / "아직 판단하기에는 기록이 적습니다."

### 7.10 공통 UX

모든 주요 화면에 loading / empty / error / retry 상태를 정의한다. 모바일 우선.

---

## 8. 프로필 업데이트 (Monthly / 충분한 Evidence)

- Proposal 예: "지난 4주 동안 '지속'과 관련해 새롭게 관찰된 내용이 있습니다." + `trait`, `old/proposed value·confidence`, `reason`, `evidence_ids`.
- 사용자 선택: 맞아요 / 일부만 맞아요 / 아니에요 / 나중에 보기.

---

## 9. Growth Experiment

- 규칙: 한 번에 1개 권장, 최대 3개, 1주 안에 테스트 가능, 측정 가능한 작은 행동, 실패해도 비용이 낮음.
- 예: "새 아이디어가 생기면 바로 시작하지 않고 메모한 뒤, 현재 진행 중인 한 가지를 먼저 끝내보기."
- 다음 Weekly Mirror에서 실행 여부와 체감을 확인.
- **금지**: 의료, 법률, 재정, 관계 단절 등 고위험 행동 직접 지시. 치료·진단·투자·법률·강한 관계결단을 대신하지 않는다.
- 주역 Reflection은 실험을 제안할 수 있지만 TraitState나 활성 ProfileVersion을 직접 변경할 수 없다.

---

## 10. 알림

- 채널: 초기 Email + In-app. 구현은 `MessagingProvider` adapter 사용.
- Phase 1 템플릿: Account `verify_email`, `password_reset` / Product `weekly_mirror_ready`, Growth reminder.
- Marketing은 별도 동의/철회. 필수 알림과 구분. Product 알림은 사용자 timezone 반영.

---

## 11. i18n / 시간대

- 기본 한국어 (prefix 없음). `/ja`, `/en`은 향후.
- Living 기록(일기)은 **사용자 timezone**을 중요시한다. 저장은 UTC + display timezone.

---

## 12. 디자인 시스템 / 접근성

- Design tokens: color, typography, spacing, radius, shadow, motion, breakpoints. 브랜드: 아이보리/웜톤 기반의 따뜻한 자기기록 톤.
- 접근성: semantic HTML, label, keyboard, focus, contrast, alt, error text, touch target, reduced motion (WCAG 계열 권고 참고, 실용적 수준).
- 단정적 성격 판정 금지 문구 원칙 유지.

---

## 13. 보안 / 데이터 거버넌스

- **데이터 분류**: Account(이메일/인증), Sensitive Product(출생정보·일기·감정), Media(사진·생성 캐릭터), Analytics(이벤트), Audit(관리자 접근/동의 이력).
- **계정 탈퇴**: 로그인 확인 → 처리 예정 데이터 설명 → 삭제 job → 완료 기록.
- **일기 삭제**: raw entry 삭제/비활성 → derived Evidence invalidate → Pattern 재계산 → Profile 영향 표시. 삭제한 일기를 AI가 계속 근거로 쓰지 않는다.
- **AI Provider**: 직접식별자 최소화, retention/training 정책 확인, provider/version 기록.
- **Consent Ledger**: subject, type, policy_version, text_hash, agreed_at, revoked_at, ip, user_agent, source.
- **데이터 내보내기**: profile, journal, media references — JSON + Markdown.
- **감사**: 민감 데이터 조회 시 who/when/purpose/object/action 기록.
- **운영 관리자 화면 최소 기능**: 사용자 활성 상태, 프로필 상태, 기록 수, 주간 상태. **관리자는 raw journal을 기본 목록에서 볼 수 없어야 한다.**
- 권한은 API에서 강제. IDOR, token enumeration rate limit, 내부 정수 ID 비공개.

---

## 14. 테스트 / 릴리즈

- **엔진 검증(전제)**: 기존 사주 만세력 테스트, 주역 17개 테스트, 엔진 API contract test, invalid input/fail-closed/timeout/idempotency, private field omission, engine unavailable no-update.
- **AI 검증**: `prompt_version`, `schema_version`, `model`, generation timestamp 기록. 회귀테스트용 golden dataset.
- **릴리즈 게이트 (CI)**: lint → typecheck → unit → integration 핵심 → schema validation.
- **보안 테스트**: auth, admin role, IDOR, XSS, token enumeration, rate limit.
- **QA 엣지 케이스**: 기록 0/1/2/3~4/5~7일, 빈 일기·매우 긴 일기·emoji·다국어, duplicate submission, timezone rollover, 부정 Evidence, 상충 감정, 숫자 hallucination 금지, confidence 낮을 때 단정 금지.

---

## 15. 백로그

### Release 0 — Technical Spike

목표: 1명의 사용자 데이터가 처음부터 Weekly Mirror까지 흐르는지 검증.

- [ ] 기존 사주 엔진 API 확인
- [ ] Birth Normalization
- [ ] Trait Mapper mock
- [ ] Profile 001 JSON 생성
- [ ] Daily Entry 저장
- [ ] Evidence Extractor
- [ ] Weekly Mirror mock
- [ ] 기본 인증

완료 조건: 개발자 계정 1개로 전체 loop 수동 테스트 성공.

### Release 1 — Internal Alpha

- **P0 Identity**: nickname, birth date, calendar type, birth time/unknown, location, current priorities, change goal, current goal
- **P0 Profile**: Initial Profile, trait/value/confidence, profile feedback, transparency page(분석 방법 고지)
- **P0 Daily**: mood, energy, satisfaction, journal, tags
- **P0 Weekly**: data coverage rule, deterministic metrics, partial/full mirror, evidence refs, growth experiment
- **P0 Privacy**: account delete, entry delete, privacy page, admin RBAC

완료 조건: 내부 사용자 5명, 7일 테스트.

### Phase 1.5 후보 (Release 1 이후)

21일 기록 리포트, Reflection Intensity, "내가 말한 나 vs 기록된 나"(4주+), 사진 업로드, 음성 기록.

---

## 16. MVP 포함 / 제외

### 포함 (Phase 1)

- 회원가입/로그인
- 온보딩 (프로필 생성)
- Birth Normalization + 기존 사주엔진 연동
- Trait Mapper
- Profile 001 + Profile Feedback
- Daily Check-in + Journal
- Evidence Store
- Sparse-data-aware Weekly Mirror (+ 주역 record_reflection)
- Growth Experiment
- 데이터 삭제/내보내기
- 관리자 기본 도구
- 분석 방법 고지

### 제외 (Phase 1)

- 정식 MBTI, Enneagram, Big Five 풀검사
- 궁합, 운세, 대운/세운 노출 (엔진 내부 계산은 가능, 사용자 노출 금지)
- 커뮤니티, 랭킹, 친구 비교
- 의료/정신건강 진단
- 복잡한 gamification, 자동 치비 성장 애니메이션
- 장기 Similar Moments
- 커머스 전반, NFC/키링, QR 페이지, 타인/그룹 연결

---

## 17. 성공 지표 (Phase 1)

- Profile 001 Complete ≥ 80%
- Profile 완료자 중 First Daily Entry ≥ 70%
- Profile 완료자의 Day 7 Record Retention ≥ 40%
- 생성된 Weekly Mirror Open Rate ≥ 70%
- Weekly Mirror 조회자의 다음 주 기록 재개율 ≥ 50%
- Weekly Mirror 조회자 중 "새롭게 발견한 점이 있다" ≥ 50%
- 21일 종료자 중 "계속 사용하고 싶다" ≥ 20%

**North Star**: 4주 동안 Weekly Mirror를 3회 이상 확인한 활성 사용자 비율.

숫자는 Prototype 가설이며 데이터에 따라 수정한다.

**장기 비전**: 사용자가 1~3년 사용했을 때 실제 기록을 근거로 답할 수 있어야 한다.
"나는 언제 가장 행복했나? / 어떤 관계에서 편안했나? / 무엇을 할 때 에너지가 올라갔나? / 어떤 문제가 반복됐나? / 내가 중요하다고 말했던 가치와 실제 삶이 일치했나? / 1년 전과 지금의 나는 어떻게 달라졌나? / 나는 어떤 사람이 되어가고 있나?"
