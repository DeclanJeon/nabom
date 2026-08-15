---
doc_id: NABOM-P2-001
title: NABOM Phase 2 Design (나↔타인)
version: 1.0
status: SSOT
updated_at: 2026-08-13
depends_on:
  - NABOM_Phase0_Design.md (엔진 기반)
  - NABOM_Phase1_Design.md (프로필·기록·회고 데이터)
scope: Phase 2 — Relationship (동의 기반 두 사용자 분석)
---

# NABOM Phase 2 설계서 — 나와 타인의 연결 (Relationship)

## 0. 문서 목적과 전제

Phase 2는 **두 사용자 사이의 분석 관계**를 다룬다. Phase 1에서 쌓인 프로필·기록·회고 데이터를, **양쪽의 명시적 동의(InsightConsent)가 승인한 공개 범위만** 사용해 관계를 조명한다.

- **전제**: Phase 1(나↔나)이 안정화되어 있어야 한다. 관계 분석은 양쪽의 개인 데이터가 있어야 의미가 있다.
- **핵심 원칙**: 동의 없이 읽지 않는다. 추측을 사실로 말하지 않는다. 운명·선악·관계 단절을 결론내리지 않는다.
- **제외**: 커머스(공동구매 등)와 소유권을 공유하지 않는다. `GroupBuy` 참가자가 자동으로 관계/그룹 멤버가 되지 않는다.

```text
User A ── 초대/동의 요청 ──▶ User B
   └─ InsightConsent(양쪽) 승인된 공개 범위만
   └─ RelationshipMirror 생성 (A→B, B→A, 공통 보완)
```

---

## 1. 제품 원칙

- `Relationship`은 두 사용자 사이의 **분석 관계**이며, 주문·결제·제작(`GroupBuy`)과 소유권을 공유하지 않는다.
- 관계 분석은 **양쪽 `InsightConsent`가 승인한 공개 범위만** 읽는다. raw journal, birth input, 비공개 Evidence는 기본 응답에 포함하지 않는다.
- `RelationshipMirror`는 **가설·근거·confidence를 보존**하며 운명이나 확정 진단이 아니다.
- **동의 철회**는 새 분석 생성을 중단하고 기존 결과를 suspended 처리한다.
- 관계 출력은 **A→B, B→A, 공통 보완 영역을 분리**한다. 운명·선악·관계 단절을 결론내리지 않는다.

---

## 2. 상태 머신

### Relationship

```text
DRAFT → CONSENT_PENDING → ACTIVE → PAUSED → REVOKED → DELETED
```

- `ACTIVE`는 **양쪽의 유효한 동의와 공개 scope가 있을 때만** 가능하다.
- 동의 철회 또는 권한 범위 축소 시 `PAUSED`로 전환하고 새 분석 생성을 중단한다.

### InsightConsent

```text
REQUESTED → GRANTED | DECLINED
GRANTED → REVOKED
```

- 모든 전이는 actor, scope, policy version, reason, timestamp, audit reference를 기록한다.

---

## 3. 데이터 모델

```jsonc
// Relationship
{ "relationship_id": "rel_x",
  "initiator_user_id": "usr_a", "participant_user_id": "usr_b",
  "context": "friend",
  "status": "consent_pending | active | paused | revoked | deleted",
  "visibility": "private",
  "consent_ids": ["ic_a", "ic_b"], "version": 1 }

// InsightConsent — subject_type: relationship
{ "consent_id": "ic_x", "subject_type": "relationship", "subject_id": "rel_x",
  "user_id": "usr_a",
  "scope": {
    "birth_hypothesis": true, "character_profile": true,
    "trait_state": false, "daily_entry": false, "evidence": false,
    "relationship_mirror": true
  },
  "status": "granted", "policy_version": "insight-consent-v1",
  "granted_at": "...", "revoked_at": null }

// RelationshipMirror — 가설·근거·confidence 보존
{ "relationship_mirror_id": "rm_x", "relationship_id": "rel_x",
  "source_priority": ["relationship_evidence", "mutual_feedback",
                      "public_trait_state", "birth_hypothesis"],
  "contributions": [],   // A→B, B→A 방향성 분해
  "tensions": [],
  "shared_growth_areas": [],
  "confidence": "medium", "evidence_refs": [], "status": "hypothesis" }

// RelationshipEvidence — append-only 이벤트
{ "evidence_id": "rev_x", "relationship_id": "rel_x",
  "rule_code": "a_to_b | b_to_a | shared",
  "occurred_at": "...", "signals": [], "status": "active" }
```

- `RelationshipEvidence`는 불변(append-only) 이벤트다. `rule_code`로 방향성(A→B/B→A/shared)을 분해한다.
- scope enforcement: `SCOPE_FEATURES` 기준으로 feature를 필터링한다 (예: `character_profile` 한정 시 오행 feature 제외).

---

## 4. 라우트 / API

```text
/relationships                              # 관계 목록
/relationships/[relationshipId]             # 관계 상세
/relationships/[relationshipId]/consent     # 동의 요청/응답/철회
/relationships/[relationshipId]/mirror      # 관계 회고
```

API:

```text
POST /api/v1/relationships/[relationshipId]/mirror   # Facade: 관계 회고 생성
```

- 관계·그룹 API는 **동의된 공개 범위만 반환**한다. raw journal, birth input, 비공개 Evidence를 기본 응답에 포함하지 않는다.
- 내부 엔진: `POST /internal/v1/compatibility` (궁합 근거). 관계 엔진은 양쪽 동의를 알지 못하며, **Facade가 동의 확인 후 허용된 데이터만 전달**한다.

---

## 5. 동의 UX (화면)

1. 초대: 상대 식별(닉네임/초대 링크) → `DRAFT`
2. 동의 요청: 관계 유형(context), 공개 scope 선택(위 데이터 모델의 scope) → `CONSENT_PENDING`
3. 상대 응답: 수락(Granted) / 거절(Declined). 수락 시 각자 scope 확인 후 양쪽 모두 GRANTED여야 `ACTIVE`
4. 운용: scope 변경/철회 가능. 철회 시 `PAUSED` + 기존 결과 suspended
5. 회고: `RelationshipMirror` 생성·조회

- 한쪽만 동의한 상태로는 관계를 활성화할 수 없다(one-sided consent cannot activate).
- 동의 화면에서 "무엇이 공유되고 무엇이 공유되지 않는지"를 scope 항목별로 명확히 보여준다.

---

## 6. 회고 파이프라인 (RelationshipMirror)

```text
양쪽 동의 scope 내 데이터
  → RelationshipEvidence 추출 (A→B / B→A / shared)
  → 엔진 궁합 근거 (compatibility) — 보조 입력
  → Deterministic Aggregation → Pattern Candidate
  → LLM Narrative → Safety/Evidence Check → RelationshipMirror
```

- 출력은 기여(A→B), 기여(B→A), 긴장 요소, 공통 성장 영역을 분리한다.
- "운명적 궁합", "이 관계는…" 같은 단정 표현을 금지한다. 가설·근거·confidence로 표현한다.
- 거절된 가설은 학습용으로 보존하되 활성 관계 프로필에는 반영하지 않는다.

---

## 7. 보안 / QA 필수

- one-sided consent로 관계 활성화 불가
- consent revoke 시 신규·기존 insight 모두 suspend
- private trait/journal/evidence scope 유출 금지 (scope 필터 테스트)
- A→B와 B→A 기여 방향 정확성
- rejected hypothesis 재등장 금지
- IDOR: 관계는 participant 전용 접근 (403)
- 교차 사용자 접근 차단: 관계 evidence/consent/revoke는 participant 전용

---

## 8. Phase 2 성공 기준 (후보)

- 관계 활성화율, 동의 응답률, 관계 회고 조회율, "새롭게 발견한 점" 비율.
- 숫자는 Phase 1 데이터와 사용자 수에 따라 수립한다 (미정).

---

## 9. MVP(Phase 1)와의 경계

- Phase 1 범위의 데이터(프로필, 기록, 회고)는 그대로 재사용한다. 관계 분석은 **읽기 전용**으로만 참조한다.
- Phase 2에서도 커머스·공동구매·그룹 기능을 포함하지 않는다.
