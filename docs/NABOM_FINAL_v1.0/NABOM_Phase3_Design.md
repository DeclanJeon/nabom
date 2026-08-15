---
doc_id: NABOM-P3-001
title: NABOM Phase 3 Design (나↔그룹)
version: 1.0
status: SSOT
updated_at: 2026-08-13
depends_on:
  - NABOM_Phase0_Design.md (엔진 기반)
  - NABOM_Phase2_Design.md (관계 분석 기반)
scope: Phase 3 — InsightGroup (집계·익명화된 그룹 분석)
---

# NABOM Phase 3 설계서 — 나와 그룹의 연결 (InsightGroup)

## 0. 문서 목적과 전제

Phase 3은 **공동 목표·기록·관계 분석을 위한 사람 집합(InsightGroup)** 을 다룬다. 개인 식별이 불가능한 **집계 결과만** 생성하며, 최소 인원 미달 시 개인 추정이 가능한 분석을 제공하지 않는다.

- **전제**: Phase 1(자기 데이터) + Phase 2(관계 분석)가 안정화되어 있어야 한다.
- **핵심 원칙**: 개인 역산 불가능한 집계(`aggregate_only`, `k_anonymous`)만 허용한다. 운명·확정 진단을 내리지 않는다.
- **제외**: `GroupBuy`(커머스)와 소유권을 공유하지 않는다. `GroupBuyCampaign` 참가자는 자동으로 InsightGroup에 편입되지 않는다.

```text
사람 집합(최소 5명, 활성 동의)
  → GroupMembership (개별 동의 scope + 익명화 메타데이터)
  → GroupProfile / GroupRelationshipInsight (집계 전용)
  → 개인 역산 불가 검증
```

---

## 1. 제품 원칙

- `InsightGroup`은 공동 목표·기록·관계 분석을 위한 사람 집합이다. 주문·결제·제작은 `GroupBuy`가 소유하며 **권한을 공유하지 않는다** (별도 라우트/도메인).
- 그룹 분석은 **최소 5명 이상의 활성 동의 구성원**에서만 개인 역산이 불가능한 집계 결과를 생성한다.
- `GroupProfile`·`GroupRelationshipInsight`는 **가설·근거·confidence를 보존**하며 운명이나 확정 진단이 아니다.
- **동의 철회**는 새 분석 생성을 중단하고 기존 결과를 suspended 처리한다.
- `aggregate_only`가 true가 아니면 생성할 수 없다. `GroupMembership`의 active consent scope와 anonymization metadata가 없는 GroupProfile은 **published 상태가 될 수 없다**.

---

## 2. 상태 머신

### InsightGroup

```text
DRAFT → INVITING → ACTIVE → PAUSED → ARCHIVED
```

- `ACTIVE`는 **최소 5명의 활성 동의 구성원**을 요구한다.
- 구성원 이탈로 최소 인원 조건을 충족하지 못하면 `PAUSED`가 되며, 공동 기록·설명 페이지 외의 **개인 추정 분석은 제공하지 않는다**.

### GroupMembership

```text
INVITED → JOINED → ACTIVE → LEFT | REMOVED
```

---

## 3. 데이터 모델

```jsonc
// InsightGroup
{ "group_id": "ig_x", "status": "draft | inviting | active | paused | archived",
  "minimum_group_size": 5,
  "active_consented_member_count": 6,
  "anonymization": "k_anonymous",
  "group_profile_id": "gp_x" }

// GroupMembership
{ "group_id": "ig_x", "user_id": "usr_a", "role": "member",
  "status": "invited | joined | active | left | removed",
  "visibility_scope": "character_only",
  "consent_id": "ic_group_a", "joined_at": "..." }

// GroupProfile — 집계 전용
{ "group_profile_id": "gp_x", "group_id": "ig_x",
  "shared_goals": ["행사 준비"],
  "role_patterns": [], "shared_patterns": [],
  "current_growth_areas": [],
  "minimum_group_size": 5, "active_consented_member_count": 6,
  "anonymization": "k_anonymous",
  "evidence_refs": [], "status": "hypothesis" }

// GroupRelationshipInsight — 그룹 간 분석, 집계 전용
{ "group_relationship_insight_id": "gri_x",
  "group_a_id": "ig_a", "group_b_id": "ig_b",
  "group_a_contributes": [], "group_b_contributes": [],
  "shared_improvement": [], "coordination_risks": [],
  "recommended_joint_experiment": {},
  "confidence": "low", "aggregate_only": true,
  "evidence_refs": [], "status": "hypothesis" }
```

---

## 4. 라우트 / API

```text
/groups                                  # 그룹 목록
/groups/[groupId]                        # 그룹 상세
/groups/[groupId]/members                # 멤버 관리
/groups/[groupId]/mirror                 # 그룹 회고
/groups/[groupId]/profile                # 그룹 프로필 (집계)
/groups/[groupId]/relationship-insights  # 그룹 간 인사이트
```

API:

```text
POST /api/v1/insight-groups/[groupId]/profile   # Facade: 그룹 프로필 생성
```

- 관계·그룹 API는 **동의된 공개 범위만 반환**한다. raw journal, birth input, 비공개 Evidence를 기본 응답에 포함하지 않는다.
- 그룹 간 분석(`group-to-group`)은 `aggregate_only` 출력만 허용하며, 개인을 역식별할 수 없어야 한다.

---

## 5. 구성원 UX (화면)

1. 그룹 생성: 목적·공동 목표 설정 → `DRAFT`
2. 초대: 멤버 초대 → `INVITING`
3. 가입/동의: 각 멤버가 visibility scope(`character_only` 등)와 consent를 승인 → `JOINED`/`ACTIVE`
4. 활성: 최소 5명 충족 시 `ACTIVE` → 집계 분석 제공
5. 이탈/제거: 최소 인원 미달 시 `PAUSED` (개인 추정 분석 중단)

- 각 멤버의 공개 범위를 명확히 보여준다. 그룹은 멤버 개인의 raw 기록을 다른 멤버에게 노출하지 않는다.

---

## 6. 집계 파이프라인

```text
활성 멤버들의 동의 scope 내 데이터
  → 익명화(k_anonymous) 적용
  → 최소 인원(5) 검증
  → Deterministic Aggregation (mean ratio 등 집계 수치만)
  → GroupProfile / GroupRelationshipInsight 생성
  → 개인 역산 가능 여부 검증 후 게시
```

- 노출은 집계 수치(예: mean ratio)만 허용한다.
- `aggregate_only`가 true가 아니면 그룹 분석을 생성할 수 없다.

---

## 7. 보안 / QA 필수

- 5명 미만 활성 멤버 → 개인 추론 차단 (minimum-five aggregate gate)
- group-to-group 출력으로 멤버 역식별 불가
- GroupBuy가 InsightGroup 멤버십을 자동 생성하지 않음
- consent revoke 시 신규·기존 insight 모두 suspend
- 멤버 전용 접근 (403): 그룹 프로필/그룹 간 분석
- 교차 사용자 접근 차단

---

## 8. Phase 3 성공 기준 (후보)

- 그룹 활성화율, 최소 인원 도달율, 그룹 회고 조회율, "집단에서 발견한 점" 비율.
- 숫자는 Phase 1·2 데이터와 사용자 수에 따라 수립한다 (미정).

---

## 9. Phase 경계

- Phase 1·2의 데이터(프로필, 기록, 회고, 관계)를 **읽기 전용**으로만 참조한다.
- 그룹 분석은 항상 `aggregate_only`이며, 개인 프로필·회고에는 영향을 주지 않는다.
- 커머스·공동구매 기능은 Phase 3에도 포함하지 않는다.
