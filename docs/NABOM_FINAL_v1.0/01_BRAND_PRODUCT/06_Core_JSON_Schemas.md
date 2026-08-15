---
doc_id: LEGACY-4A80CD38C6
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 01_BRAND_PRODUCT/06_Core_JSON_Schemas.md
---

# NABOM Core JSON Schemas v1.0

아래는 구현 논의를 위한 초안이며 실제 DB 스키마와 API schema는 별도 versioning한다.

---

## 1. UserProfile

```json
{
  "user_id": "usr_x",
  "nickname": "Declan",
  "timezone": "Asia/Seoul",
  "created_at": "2026-08-10T17:00:00+09:00"
}
```

---

## 2. BirthInput

```json
{
  "calendar": "solar",
  "date": "1992-03-01",
  "time": "07:20",
  "time_precision": "exact",
  "location": {
    "label": "Busan, South Korea",
    "lat": 35.1796,
    "lon": 129.0756,
    "timezone": "Asia/Seoul"
  }
}
```

`time_precision`:
- exact
- approximate
- unknown

---

## 3. TraitState

```json
{
  "trait": "exploration",
  "value": 0.76,
  "confidence": 0.61,
  "source_counts": {
    "birth_hypothesis": 1,
    "self_report": 2,
    "journal": 7,
    "profile_feedback": 1
  },
  "updated_at": "2026-08-31T21:00:00+09:00"
}
```

`source`가 `birth_hypothesis`인 Trait는 초기 가설로 저장하며, 실제 기록·사용자 피드백보다 낮은 우선순위로 취급한다.

### 3-1. CharacterProfile

```json
{
  "character_profile_id": "cp_x",
  "profile_version_id": "pv_001",
  "day_stem": "병화",
  "representative_element": "fire",
  "guardian_beast": {
    "code": "jujak",
    "label_ko": "주작",
    "source": "day_stem_element"
  },
  "companion_animal": {
    "source": "day_branch",
    "code": "branch_x",
    "label_ko": "..."
  },
  "user_editable": true,
  "status": "active"
}
```

캐릭터와 상징 동물은 사용자-facing 진단값이 아니라 시각적 프로필 표현이다.

---

## 4. Evidence

```json
{
  "evidence_id": "ev_x",
  "user_id": "usr_x",
  "type": "journal",
  "occurred_at": "2026-08-12T22:01:00+09:00",
  "source_record_id": "entry_x",
  "signals": [
    {
      "trait": "persistence",
      "direction": "positive",
      "strength": 0.33
    }
  ],
  "summary": "불편함이 있었지만 하던 작업을 마무리함",
  "status": "active"
}
```

---

## 5. DailyEntry

```json
{
  "entry_id": "entry_x",
  "date": "2026-08-12",
  "mood": 3,
  "energy": 2,
  "satisfaction": 4,
  "text": "오늘 기억하고 싶은 내용",
  "tags": ["work", "relationship"],
  "created_at": "2026-08-12T22:00:00+09:00"
}
```

---

## 6. PatternHypothesis

```json
{
  "pattern_id": "pat_x",
  "title": "결과를 기다릴 때 생각이 많아지는 경향",
  "confidence": 0.68,
  "status": "hypothesis",
  "evidence_ids": ["ev1", "ev2", "ev3"],
  "counter_evidence_ids": ["ev9"],
  "first_seen_at": "2026-08-12",
  "last_seen_at": "2026-08-27"
}
```

---

## 7. WeeklyMirror

```json
{
  "mirror_id": "wm_x",
  "period": {
    "from": "2026-08-10",
    "to": "2026-08-16"
  },
  "coverage": {
    "days_recorded": 5,
    "mode": "full"
  },
  "summary": "새로운 일을 시작하면서 기대가 컸지만 결과를 기다리는 시간에 에너지를 많이 사용한 주였습니다.",
  "notable_moments": [],
  "emotion_flow": [],
  "energy_gainers": [],
  "energy_drainers": [],
  "patterns": [],
  "changes": [],
  "hypotheses": [],
  "growth_experiment_id": "exp_x",
  "generated_at": "2026-08-17T08:00:00+09:00",
  "prompt_version": "weekly-v1"
}
```

### 7-1. CanonicalReflection

```json
{
  "reflection_id": "rf_x",
  "mode": "record_reflection",
  "resolver_version": "iching-reflection-v1",
  "context_refs": ["wm_x", "ev1"],
  "situation": {
    "code": "transition_with_waiting",
    "confidence": 0.62
  },
  "observation_focus": ["기다리는 동안 에너지가 어떻게 변하는지"],
  "caution_signals": ["기록이 적은데 한 주 전체를 단정하지 않기"],
  "recommended_action": {
    "title": "기다리는 시간을 한 번 기록하기",
    "instruction": "기다리는 동안 한 행동과 에너지 변화를 한 줄로 남깁니다.",
    "success_condition": "7일 안에 2회 기록",
    "reversible": true
  },
  "evidence_refs": ["ev1"]
}
```

`CanonicalReflection`은 Profile을 직접 변경하지 않는다. `mode: record_reflection`은 기록 상태에서 결정적으로 생성된 회고임을 뜻하며, 실제 점괘 입력과 분리한다.

---

## 8. GrowthExperiment

```json
{
  "experiment_id": "exp_x",
  "title": "새 아이디어는 기록만 하기",
  "instruction": "이번 주 새 아이디어가 생기면 바로 시작하지 않고 메모한 뒤 현재 진행 중인 한 가지를 먼저 끝내봅니다.",
  "success_condition": "새 아이디어 즉시 착수 0회",
  "status": "accepted",
  "user_result": null
}
```

---

## 9. ProfileVersion

```json
{
  "profile_version_id": "pv_001",
  "number": 1,
  "created_at": "2026-08-10T17:30:00+09:00",
  "identity_sentence": "새로운 가능성을 발견하고 직접 움직일 때 강해지는 사람",
  "traits": [],
  "strengths": [],
  "watch_patterns": [],
  "growth_theme": "확장보다 완성",
  "evidence_cutoff": "2026-08-10T17:25:00+09:00"
}
```

---

## 10. NFC Token

```json
{
  "nfc_token_id": "nfc_x",
  "token": "opaque-random-token",
  "user_id": "usr_x",
  "status": "active",
  "issued_at": "2026-08-10T12:00:00+09:00",
  "revoked_at": null,
  "replacement_of": null
}
```

---

## 11. Profile Feedback

```json
{
  "feedback_id": "pf_x",
  "profile_version_id": "pv_001",
  "target_type": "trait",
  "target_key": "exploration",
  "rating": "mostly_correct",
  "comment": "새로운 건 좋아하지만 사람 많은 곳은 빨리 지칩니다.",
  "created_at": "2026-08-10T17:35:00+09:00"
}
```


---

## 12. Product Metadata

```json
{
  "product": {
    "name_ko": "나봄",
    "name_en": "NABOM",
    "domain": "nabom.ponslink.com",
    "engine": "Living Self Engine",
    "tagline": "기록할수록 선명해지는 나."
  }
}
```

## 13. Relationship

```json
{
  "relationship_id": "rel_x",
  "initiator_user_id": "usr_a",
  "participant_user_id": "usr_b",
  "context": "friend",
  "status": "consent_pending",
  "visibility": "private",
  "consent_ids": ["ic_a", "ic_b"],
  "version": 1
}
```

상태는 `DRAFT → CONSENT_PENDING → ACTIVE → PAUSED → REVOKED → DELETED` 순서를 따른다. `ACTIVE`는 양쪽의 유효한 동의와 공개 scope가 있을 때만 가능하다.

## 14. InsightConsent

```json
{
  "consent_id": "ic_x",
  "subject_type": "relationship",
  "subject_id": "rel_x",
  "user_id": "usr_a",
  "scope": {
    "birth_hypothesis": true,
    "character_profile": true,
    "trait_state": false,
    "daily_entry": false,
    "evidence": false,
    "relationship_mirror": true
  },
  "status": "granted",
  "policy_version": "insight-consent-v1",
  "granted_at": "2026-08-12T10:01:00Z",
  "revoked_at": null
}
```

## 15. RelationshipMirror

```json
{
  "relationship_mirror_id": "rm_x",
  "relationship_id": "rel_x",
  "source_priority": [
    "relationship_evidence",
    "mutual_feedback",
    "public_trait_state",
    "birth_hypothesis"
  ],
  "contributions": [],
  "tensions": [],
  "shared_growth_areas": [],
  "confidence": "medium",
  "evidence_refs": [],
  "status": "hypothesis"
}
```

관계 출력은 A→B, B→A, 공통 보완 영역을 분리하며 운명·선악·관계 단절을 결론내리지 않는다.

## 16. InsightGroup

```json
{
  "group_id": "ig_x",
  "status": "active",
  "minimum_group_size": 5,
  "active_consented_member_count": 6,
  "anonymization": "k_anonymous",
  "group_profile_id": "gp_x"
}
```

`active_consented_member_count`가 5 미만이면 개인 추정이 가능한 GroupProfile과 그룹 간 분석을 생성하지 않는다. `GroupBuyCampaign`의 참가자는 자동으로 InsightGroup에 편입되지 않는다.

### 16-1. GroupMembership

```json
{
  "group_id": "ig_x",
  "user_id": "usr_a",
  "role": "member",
  "status": "active",
  "visibility_scope": "character_only",
  "consent_id": "ic_group_a",
  "joined_at": "2026-08-12T10:00:00Z"
}
```

### 16-2. GroupProfile

```json
{
  "group_profile_id": "gp_x",
  "group_id": "ig_x",
  "shared_goals": ["행사 준비"],
  "role_patterns": [],
  "shared_patterns": [],
  "current_growth_areas": [],
  "minimum_group_size": 5,
  "active_consented_member_count": 6,
  "anonymization": "k_anonymous",
  "evidence_refs": [],
  "status": "hypothesis"
}
```

### 16-3. GroupRelationshipInsight

```json
{
  "group_relationship_insight_id": "gri_x",
  "group_a_id": "ig_a",
  "group_b_id": "ig_b",
  "group_a_contributes": [],
  "group_b_contributes": [],
  "shared_improvement": [],
  "coordination_risks": [],
  "recommended_joint_experiment": {},
  "confidence": "low",
  "aggregate_only": true,
  "evidence_refs": [],
  "status": "hypothesis"
}
```

`aggregate_only`가 true가 아니면 생성할 수 없다. `GroupMembership`의 active consent scope와 anonymization metadata가 없는 GroupProfile은 published 상태가 될 수 없다.

## 17. NFC/QR Gift Page

```json
{
  "page_type": "relationship",
  "ownership": "shared",
  "access_policy": "consented_relationship_members",
  "authorization_subject_id": "rel_x",
  "authorization_state": "active",
  "content_scope": ["memory", "message", "reflection_prompt"],
  "analysis_result_included": false,
  "token_source": "nfc_or_qr_resolver"
}
```

`access_policy`는 `visibility`와 별개다. resolver는 `authorization_subject_id`의 현재 membership·consent·state를 확인한다. revoke/pause 시 `authorization_state`는 `suspended`가 되고 민감 콘텐츠 접근은 차단된다.

허용되는 canonical `access_policy` 값은 `public`, `claimed_recipient`, `consented_relationship_members`, `active_insight_group_members`, `owner_only`다. `consented_members`는 사용하지 않는다.

`status`는 분석의 인식론적 상태(`hypothesis`, `confirmed`, `rejected`)이고, `authorization_state`는 접근 가능성(`active`, `suspended`)이다. 두 상태를 서로 대체하지 않는다.

## 18. Reflection Audit Reference

`CanonicalReflection`은 다음 감사 필드를 저장한다.

```json
{
  "resolver_input_hash": "sha256:...",
  "cast_mapping_version": "cast-map-v1",
  "raw_reading_internal_ref": "reading_x",
  "classical_source_refs": [],
  "generated_at": "2026-08-17T08:00:00Z"
}
```

raw reading은 내부 접근 통제와 감사 목적에만 사용하며 사용자 기본 화면에 노출하지 않는다.

기본 페이지 유형:

- `memory`
- `reflection_gift`
- `relationship`
- `group_memory`
- `growth_capsule`

분석 결과는 기본적으로 NFC/QR 페이지에 포함하지 않으며, 양쪽 동의와 별도 공개 승인이 있을 때만 제한된 요약을 포함한다.
