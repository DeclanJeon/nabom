---
doc_id: LEGACY-47D94EED85
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 01_BRAND_PRODUCT/02_Living_Self_Engine.md
---

# 나봄 Living Self Engine / Evidence / Profile 설계

## 0. 시스템 식별자

- 제품명: **나봄(NABOM)**
- 내부 핵심 엔진: **Living Self Engine (LSE)**
- 하위 모듈:
  - `ProfileEngine`
  - `EvidenceEngine`
  - `MirrorEngine`
  - `GrowthEngine`
  - `BirthHypothesisEngine`

## 1. 가장 중요한 시스템 원칙

> **관찰하지 않은 것을 아는 척하지 않는다.**

AI는 사용자에 대한 사실, 관찰, 추론을 구분한다.

### Fact
사용자가 직접 입력한 내용.

### Observation
실제 기록에서 계산 또는 추출된 신호.

### Hypothesis
Fact와 Observation을 기반으로 한 추론.

사용자에게 Hypothesis를 Fact처럼 말하지 않는다.

---

## 2. 데이터 우선순위

초기에는 Birth Hypothesis가 빈 공간을 채울 수 있다.

시간이 지날수록 다음 순서로 신뢰도를 둔다.

1. 반복된 실제 행동/기록
2. 명시적 사용자 피드백
3. 구조화된 self-report
4. 단기 감정 체크
5. 출생정보 기반 초기 가설

고정 가중치를 제품 문구로 노출하지 않는다.

---

## 3. Trait 구조

```json
{
  "trait": "persistence",
  "value": 0.58,
  "confidence": 0.71,
  "status": "active",
  "sources": {
    "birth_hypothesis": 1,
    "self_report": 2,
    "journal": 11,
    "weekly_feedback": 3
  }
}
```

### value
현재 성향 방향.

### confidence
현재 모델이 그 추론에 얼마나 충분한 Evidence를 가지고 있는지.

`높은 value`와 `높은 confidence`는 다른 개념이다.

---

## 4. Confidence 레벨

예시 내부 기준:

- 0.00~0.29: 탐색 단계
- 0.30~0.49: 약한 가설
- 0.50~0.69: 중간 가설
- 0.70~0.84: 반복 관찰
- 0.85+: 강한 반복 관찰

사용자 문구:

### Low
“이런 가능성이 조금 보여요.”

### Medium
“최근 기록에서는 이런 경향이 몇 차례 보였어요.”

### High
“지난 몇 주 동안 이 패턴이 반복해서 나타났어요.”

---

## 5. Birth Hypothesis 처리

명리 계산 결과를 그대로 LLM에 던져 최종 사용자 문장을 생성하지 않는다.

반드시 중간 구조화 계층을 둔다.

```text
명리 raw result
→ Interpretation Rules
→ Trait Candidate
→ Candidate Strength
→ Caveat
→ Profile Narrative
```

예시:

```json
{
  "source": "birth_hypothesis",
  "candidate_trait": "exploration",
  "direction": "high",
  "strength": 0.64,
  "confidence": 0.25,
  "reason_code": ["..."],
  "user_visible": false
}
```

초기 confidence는 낮게 시작한다.

### 5.1 엔진 통합 계약

`BirthHypothesisEngine`은 출생 입력을 정규화한 뒤 기존 `manse_engine`을 호출하고, 계산 결과와 `quality_flags`, `quality_summary`, 엔진 버전을 함께 보존한다.

```text
BirthInput
→ BirthAdapter
→ Manse Chart + Quality Summary
→ TraitMapper
→ CharacterMapper
→ Profile 001
```

`TraitMapper`는 일간·일지·오행 균형·십신 등의 근거를 조건부 `Trait Candidate`로 변환한다. `CharacterMapper`는 일간 오행을 시각 언어로 변환한다.

```text
목 → 청룡
화 → 주작
토 → 황룡
금 → 백호
수 → 현무
```

상징 동물과 캐릭터는 진단이나 운명 판정이 아니며 사용자가 수정·거부할 수 있다. 동반 동물은 일지 기반 self card와 연지 기반 social UX를 구분해 표시한다.

음력·윤달 변환이 검증되지 않거나 출생시간이 없으면 양력/시간을 추정하지 않고 fail-closed한다. 절기 경계, 자시 후보, DST, 역사적 timezone, 고정 UTC offset은 엔진 quality flag를 유지하고 초기 confidence를 낮춘다.

---

## 6. 출생시간 미상

출생시간을 모르면:

- 시주 관련 계산 제외
- 해당 요소로 파생되는 Trait Candidate 제외
- 전체 Birth Hypothesis confidence 감소
- 사용자에게 “시간을 몰라도 사용 가능”이라고 안내
- AI가 시간을 추정하지 않음

대략적인 시간대를 넣어도 정확한 시각처럼 취급하지 않는다.

---

## 7. Evidence 객체

Evidence는 수정되지 않는 event 형태를 기본으로 한다.

종류:

- `self_report`
- `daily_checkin`
- `journal`
- `goal_action`
- `experiment_result`
- `profile_feedback`
- `weekly_feedback`
- `birth_hypothesis`

Evidence가 가리키는 원문과 AI 해석을 분리 저장한다.

---

## 8. Evidence에서 Trait 업데이트

AI는 매일 Profile을 직접 수정하지 않는다.

### Daily
Evidence 추출.

### Weekly
Pattern 후보 생성.

### Monthly 또는 충분한 Evidence 발생
Profile Update Proposal 생성.

### User
확인/수정/거절.

### System
새 Profile Version 생성.

---

## 9. Pattern 객체

```json
{
  "pattern_id": "pat_x",
  "label": "결과를 기다릴 때 생각이 증가함",
  "confidence": 0.72,
  "first_seen_at": "2026-08-12",
  "last_seen_at": "2026-08-30",
  "evidence_ids": ["ev1", "ev2", "ev3", "ev4"],
  "status": "hypothesis"
}
```

Pattern 조건:

- 한 번의 사건으로 생성 금지
- 서로 독립적인 Evidence가 있어야 함
- 반대 Evidence도 저장
- 최근 데이터만으로 과거 전체를 일반화하지 않음

---

## 10. Contradiction 처리

예:

Birth Hypothesis:
`social_connection = high`

User Self Report:
“혼자 있을 때 회복된다.”

Journal:
공동체 활동일 만족도 높음.

이걸 억지로 하나로 합치지 않는다.

AI는:

“사람과 연결될 때 만족감은 높지만, 회복 자체는 혼자 있는 시간에서 일어날 가능성이 있습니다.”

처럼 축을 분리해서 새로운 Hypothesis를 만들 수 있다.

---

## 11. Weekly Mirror 생성 파이프라인

```text
7일 Evidence
+ 지난 Weekly Snapshot
+ Current Goals
+ Active Experiments
+ Relevant Long-term Memory
→ Deterministic Aggregation
→ Pattern Candidate
→ LLM Narrative
→ Safety / Hallucination Check
→ Weekly Mirror
```

### 11.1 주역 회고 미들웨어

주역 엔진은 성격·프로필을 결정하지 않고, 기록 기간의 현재 국면을 해석하는 `ReflectionAdapter`로만 사용한다.

```text
DailyEntry snapshot
→ Evidence extraction
→ Deterministic metrics
→ ReflectionContext
→ I Ching Situation Resolver
→ Canonical Reflection
→ Growth Recommendation
→ LLM Narrative
→ Safety / Evidence Check
→ Weekly Mirror
```

동일한 기간, 동일한 Evidence snapshot, 동일한 resolver version은 동일한 seed를 사용해 동일한 결과를 생성해야 한다. 실제 점괘 모드와 기록 기반 회고 모드는 분리하고, 기록 기반 회고는 `mode: record_reflection`으로 표시한다.

정확한 resolver 규칙:

1. canonical hash 입력은 정렬된 Evidence ID, 분석 기간, `resolver_version`만 사용한다.
2. 사용자 ID, 현재 시각, 외부 random API를 seed에 포함하지 않는다.
3. hash를 결정적으로 6개의 값(6, 7, 8, 9)으로 매핑하고, 매핑 버전을 저장한다.
4. 매핑된 값은 `주역/engine/iching.py`의 `resolve_casts`에 bottom-to-top 순서로 전달한다.
5. 동일 snapshot replay는 동일 본괘·동효·지괘를 반환해야 한다.
6. 실제 동전/서죽 점괘와 기록 기반 `record_reflection`은 서로 다른 모드와 audit reference를 갖는다.

Canonical Reflection은 다음만 제공한다.

1. 현재 국면
2. 다음 기록에서 볼 관찰 초점
3. 과잉 해석·속도·회피에 대한 주의 신호
4. 1주 안에 실행 가능한 단일 가역 행동

Canonical Reflection 저장 시 `resolver_input_hash`, `cast_mapping_version`, `raw_reading_internal_ref`, `classical_source_refs`, `generated_at`을 감사 필드로 보존한다.

LLM에는 raw 괘 데이터 전체를 전달하지 않고, 구조화된 Reflection과 Evidence reference만 전달한다. 기본 사용자 화면은 괘명·고전 원문보다 “이번 주의 흐름”, “살펴볼 점”, “작은 실험”을 우선한다.

LLM 전에 가능한 계산은 코드로 처리한다.

예:

- 기록 일수
- 평균 기분
- 평균 에너지
- 태그 빈도
- 목표 행동 횟수
- 실험 이행 여부

LLM은 계산값을 만들어내지 않는다.

---

## 12. Weekly Mirror 출력 구조

```json
{
  "week_summary": "...",
  "record_coverage": {
    "days_recorded": 5,
    "confidence": "full"
  },
  "notable_moments": [],
  "emotion_flow": [],
  "energy_gainers": [],
  "energy_drainers": [],
  "patterns": [],
  "changes_from_last_week": [],
  "hypotheses": [],
  "growth_experiment": {},
  "evidence_refs": []
}
```

---

## 13. “왜 이렇게 봤나요?”

주요 insight마다 내부 Evidence를 연결한다.

사용자가 누르면:

- 어떤 날짜 기록에서 봤는지
- 어떤 표현/수치가 영향을 줬는지
- 아직 확실하지 않은지

를 짧게 보여준다.

AI chain-of-thought를 보여주는 것이 아니라 **사용자 데이터 근거**를 보여준다.

---

## 14. Profile Update Proposal

예:

“지난 4주 동안 ‘지속’과 관련해 새롭게 관찰된 내용이 있습니다.”

```json
{
  "trait": "persistence",
  "old_value": 0.43,
  "proposed_value": 0.55,
  "old_confidence": 0.31,
  "proposed_confidence": 0.66,
  "reason": "...",
  "evidence_ids": []
}
```

사용자 선택:

- 맞아요
- 일부만 맞아요
- 아니에요
- 나중에 보기

거절된 가설도 학습용으로 보존하되 active profile에는 반영하지 않는다.

---

## 15. Growth Experiment Generator

입력:

- 현재 목표
- Weekly Pattern
- 사용자 Reflection Intensity
- 지난 실험 이력
- 사용자가 거절했던 제안
- 현실적 제약

출력 조건:

- 1주 내 실행 가능
- 단일 행동
- 성공/실패 판단 가능
- 너무 큰 의사결정 금지
- 의료, 법률, 재정, 관계단절 등 고위험 행동을 직접 지시하지 않음

Growth Experiment는 반드시 단일 행동, 실행 기간, 성공 조건, 관찰 대상, 가역성을 가져야 한다. 주역 Reflection은 Growth Experiment를 제안할 수 있지만 `TraitState`나 활성 `ProfileVersion`을 직접 변경할 수 없다.

---

## 16. 장기 Memory Architecture

모든 일기를 매번 프롬프트에 넣지 않는다.

### L0 Raw
원본 일기/체크인.

### L1 Daily Extract
사건·감정·행동·태그.

### L2 Weekly Snapshot
한 주의 패턴/요약.

### L3 Monthly Snapshot
장기 변화.

### L4 Living Profile
현재의 안정적 가설과 핵심 기억.

AI 질의 시 필요한 계층만 retrieval한다.

---

## 17. 미래 확장

### Big Five
독립 Evidence Source로 추가.

### Enneagram
행동 자체보다 동기 Hypothesis Source로 추가.

### MBTI/Jungian Style
인지/판단 스타일을 보조 설명으로 추가 가능.

어떤 엔진도 “최종 정답” 권한을 갖지 않는다.

---

## 18. 금지 문구 원칙

피해야 함:

- “당신은 원래 이런 사람입니다.”
- “당신은 반드시…”
- “당신의 운명은…”
- “당신은 이 유형이 확실합니다.”
- “AI가 판단하기에…”

권장:

- “현재 기록에서는…”
- “지금까지는 이런 경향이 보입니다.”
- “이 가설이 당신에게도 맞게 느껴지나요?”
- “아직 판단하기에는 기록이 적습니다.”
