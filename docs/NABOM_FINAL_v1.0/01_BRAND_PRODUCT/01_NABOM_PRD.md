---
doc_id: LEGACY-51F82B6657
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 01_BRAND_PRODUCT/01_NABOM_PRD.md
---

# 나봄(NABOM) PRD v1.0


## 0. 브랜드 / 제품 식별자

### 프로젝트명
**나봄 (NABOM)**

### 메인 도메인
`https://nabom.ponslink.com`

### 내부 엔진명
**Living Self Engine (LSE)**

### 브랜드 핵심 문장
> **기록할수록 선명해지는 나.**

### 제품 정체성
나봄은 사주 앱, 성격검사 앱, 일기 앱, AI 상담 앱 중 하나로 정의하지 않는다.

나봄은 여러 입력과 실제 삶의 기록을 통해 **시간에 따라 변화하는 한 사람의 Living Profile을 만드는 서비스**다.

### URL 구조 초안
```text
nabom.ponslink.com
nabom.ponslink.com/today
nabom.ponslink.com/profile
nabom.ponslink.com/mirror
nabom.ponslink.com/journey
nabom.ponslink.com/settings
nabom.ponslink.com/k/{token}
```

`/k/{token}`은 NFC/QR 진입용 opaque token endpoint이며, 민감한 사용자 ID를 URL에 노출하지 않는다.

---

## 1. 제품 개요

나봄(NABOM)은 사용자의 출생정보와 현재 자기서술을 바탕으로 `Profile 001`을 생성하고, 이후 일기·감정·행동·목표·사용자 피드백을 Evidence로 축적하여 프로필을 계속 발전시키는 AI 성장 다이어리다.

사용자에게는 “사주 서비스”로 보이지 않는다. 출생정보는 가입 과정에서 자연스러운 프로필 정보로 입력받으며, 명리 계산 결과는 내부 Trait Candidate 생성에 사용한다.

다만 분석 방법을 허위로 표현하지 않는다. 별도의 설명 화면에서 출생정보 기반 전통 명리 체계가 초기 가설에 포함됨을 명시한다.

---

## 2. 해결하려는 문제

### P1. 사람은 자신을 장기적으로 객관화하기 어렵다.
일기를 기록해도 과거를 다시 읽고 패턴을 찾는 비용이 높다.

### P2. 성격검사는 한 번의 결과로 사람을 고정한다.
시간에 따라 변화하는 실제 삶과 분리된다.

### P3. AI 대화는 순간에는 유용하지만 장기적인 삶의 변화가 구조화되지 않는 경우가 많다.

### P4. 자기계발 앱은 너무 많은 입력과 행동을 요구해 이탈이 빠르다.

### P5. 디지털 서비스는 물리적 애착과 리추얼을 만들기 어렵다.

---

## 3. 제품 가치 제안

### 첫날
“이거 나랑 조금 비슷한데?”

### 1주
“내가 이런 패턴으로 움직이고 있었구나.”

### 1개월
“내가 생각했던 나와 실제 기록된 내가 조금 다르네.”

### 3개월
“내가 바뀌고 있다는 게 보인다.”

### 6개월+
“이 서비스가 내 과거의 나를 내가 기억하는 것보다 더 입체적으로 보여준다.”

---

## 4. 핵심 제품 루프

```text
기본정보 등록
  ↓
Profile 001 생성
  ↓
Daily Check-in / Journal
  ↓
Evidence 축적
  ↓
Weekly Mirror
  ↓
Hypothesis 제안
  ↓
사용자 피드백
  ↓
Growth Experiment
  ↓
다시 실제 삶 기록
  ↓
Monthly Profile Update
```

---

## 5. 제품 레이어

### 5.1 Physical Layer
NFC 커스텀 아크릴 키링.

- 앞면: 사용자 치비 캐릭터
- 뒷면: 가족/연인/친구/공동체/반려동물/중요한 장면
- NFC: 사용자 서비스 진입 토큰

키링은 **개인 데이터의 공개 URL**을 저장하지 않는다.

### 5.2 Initial Identity Layer
입력:

- 이름/닉네임
- 생년월일
- 양력/음력
- 출생시간 또는 “모름”
- 출생지역
- 현재 중요 영역
- 바꾸고 싶은 것
- 이루고 싶은 것
- 선택적 한 줄 자기소개

### 5.3 Initial Hypothesis Layer
내부:

```text
Birth Normalization
→ Saju Calculation
→ Traditional Interpretation
→ Trait Candidate Mapper
→ Self Report Merge
→ Confidence
→ Profile 001
```

### 5.4 Daily Evidence Layer
매일 30초~3분.

필수 최소 입력:

- 기분 1~5
- 에너지 1~5
- 만족도 1~5
- 오늘 기억하고 싶은 한 줄

선택:

- 집중
- 관계
- 태그
- 자유일기
- 사진
- 음성(Phase 2)

### 5.5 Weekly Mirror
핵심 Retention Feature.

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
10. 다음 주 작은 실험

### 5.6 Living Profile
프로필은 overwrite하지 않고 versioning한다.

- Profile 001
- Profile 002
- Profile 003 ...

각 버전은 당시 근거와 confidence snapshot을 가진다.

---

## 6. 온보딩 UX

### Screen 1
**당신에 대해 조금 알려주세요.**

“처음에는 몇 가지 정보로 프로필을 만들고, 앞으로의 기록을 통해 계속 당신을 알아갑니다.”

CTA: `내 프로필 만들기`

### Screen 2
이름 또는 닉네임.

### Screen 3
생년월일 + 양력/음력.

### Screen 4
출생시간.

옵션:
- 정확한 시간 입력
- 대략적인 시간대
- 모르겠어요

시간을 모르면 서비스 이용 가능. 시주 기반 요소는 제외하고 confidence를 낮춘다.

### Screen 5
출생지역.

### Screen 6
현재 가장 중요한 영역 복수선택.

### Screen 7
지금 바꾸고 싶은 것.

### Screen 8
지금 이루고 싶은 것. 선택 입력.

---

## 7. Profile 001

표현 방향은 “점괘”가 아니라 **개인 캐릭터 시트 + 성장 리포트**.

구성:

- 치비 아바타
- Profile Number / Date
- 지금의 나를 설명하는 한 문장
- 핵심 성향 5~7개
- 내가 가진 힘 3개
- 조심해서 볼 패턴 2~3개
- 현재 성장 테마 1개
- “이 설명이 나와 얼마나 비슷한가요?” 피드백

초기 독자 Trait 후보:

- 탐색
- 실행
- 지속
- 연결
- 회복
- 구조
- 표현

각 trait은 내부적으로 `value`와 `confidence`를 별도 관리한다.

---

## 8. Profile Feedback

사용자는 Profile 001의 각 주요 가설을 수정할 수 있어야 한다.

빠른 피드백:

- 맞아요
- 어느 정도 맞아요
- 상황에 따라 달라요
- 잘 모르겠어요
- 아니에요

추가:
`어떤 부분이 다른가요?`

사용자 피드백은 Birth Hypothesis보다 우선순위가 높은 Evidence로 저장한다.

---

## 9. Daily Check-in

### 핵심 원칙
Daily AI는 장문의 분석을 하지 않는다.

응답 예:

“오늘은 ‘기대’와 ‘불확실함’이 함께 있었던 날로 보이네요. 기록해둘게요.”

사용자가 “매일 AI에게 평가받는다”고 느끼지 않게 한다.

### 적응형 질문
매일 동일한 설문만 반복하지 않는다.

기본 3개 지표 + 선택적 adaptive question 1개.

AI가 confidence가 낮거나 상충하는 성향을 하나 골라 가볍게 질문할 수 있다.

---

## 10. Weekly Mirror 데이터 기준

### 기록 0일
Weekly Mirror 생성 안 함.

### 기록 1~2일
`Light Reflection`

패턴을 단정하지 않는다.

예:
“이번 주 전체를 말하기에는 기록이 아직 적어요. 대신 남겨준 장면에서 이런 감정이 눈에 띄었습니다.”

### 기록 3~4일
`Partial Mirror`

반복 패턴은 근거가 충분한 항목만 표시.

### 기록 5일 이상
`Full Weekly Mirror`

정식 비교와 Growth Experiment 제공 가능.

---

## 11. Pattern Definition

AI가 “반복 패턴”이라고 표현할 수 있는 기본 조건:

- 동일/유사 Evidence가 한 주 내 3회 이상, 또는
- 2주 이상에 걸쳐 반복, 또는
- 서로 다른 Evidence source에서 동일한 방향이 확인됨

조건 미달이면:

- “가능성”
- “이번 주에는 이런 모습이 보임”
- “아직 확인이 필요함”

으로 표현한다.

---

## 12. Growth Experiment

Growth Experiment는 치료, 진단, 투자, 법률, 강한 관계결단을 대신하지 않는다.

기본 규칙:

- 한 번에 1개 권장
- 최대 3개
- 1주 안에 테스트 가능
- 측정 가능한 작은 행동
- 실패해도 비용이 낮음

예:
“새 아이디어가 생기면 바로 시작하지 않고 메모한 뒤, 현재 진행 중인 한 가지를 먼저 끝내보기.”

다음 Weekly Mirror에서 실행 여부와 체감을 확인한다.

---

## 13. Reflection Intensity

사용자가 AI 개입 강도를 고를 수 있게 Phase 1.5 또는 초기 MVP 옵션으로 검토한다.

### Reflect
해석 중심. 행동 제안 최소.

### Grow
기본값. 작은 행동 실험 제안.

### Challenge
반복되는 회피/모순을 비교적 적극적으로 지적.

안전 영역에서는 Challenge도 진단이나 강압적 조언을 하지 않는다.

---

## 14. “내가 말한 나 vs 기록된 나”

장기 차별화 기능.

예:

초기 자기서술:
“나는 혼자 있는 것을 좋아한다.”

실제 12주 데이터:
의미 있는 공동활동일에 평균 만족도 상승.

AI:
“혼자 있는 것을 좋아하는 것과 혼자 있을 때 에너지가 올라가는 것은 다른 문제일 수 있습니다.”

이 기능은 최소 4주 이상 데이터에서만 활성화한다.

---

## 15. 목표 관리

초기 목표는 버려지지 않아야 한다.

Weekly Mirror에:

- 이번 주 목표와 관련된 행동
- 진척 신호
- 방해 요인
- 목표 자체가 여전히 중요한지

를 포함한다.

월 1회:
`이 목표는 아직 당신에게 중요한가요?`

---

## 16. 21일 상품 정책

NABOM FIRST 100 구매자는 최소 21일 동안 다음을 보장받는다.

- Daily Check-in
- Journal
- Weekly Mirror 최대 3회
- Growth Experiment
- Profile 001
- 21일 종료 리포트

21일 종료 후에도 사용자의 기존 데이터와 기본 프로필은 삭제하지 않는다.

유료 전환 시에만 활성화되는 후보:

- 지속적인 Weekly Mirror
- Monthly Mirror
- 장기 프로필 버전
- Similar Moments
- 고급 AI 질문

무료 잔존 기능은 출시 전 반드시 명확히 고지한다.

---

## 17. MVP 포함

### P0
- 회원가입/로그인
- NFC 연결
- 온보딩
- Birth Normalization
- 기존 사주엔진 연동
- Trait Mapper
- Profile 001
- Profile Feedback
- Daily Check-in
- Journal
- Evidence Store
- Sparse-data-aware Weekly Mirror
- Growth Experiment
- 데이터 삭제
- NFC 분실/비활성화
- 관리자 기본 도구
- 분석 방법 고지

---

## 18. MVP 제외

- 정식 MBTI
- Enneagram 검사
- Big Five 풀검사
- 궁합
- 운세
- 대운/세운 노출
- 커뮤니티
- 랭킹
- 친구 비교
- 의료/정신건강 진단
- 복잡한 gamification
- 자동 치비 성장 애니메이션
- 장기 Similar Moments

---

## 19. NABOM FIRST 100 성공조건

구매자 기준:

- NFC First Tap ≥ 85%
- Profile 001 Complete ≥ 80%
- Profile 완료자 중 First Daily Entry ≥ 70%
- Profile 완료자의 Day 7 Record Retention ≥ 40%
- 생성된 Weekly Mirror Open Rate ≥ 70%
- Weekly Mirror 조회자의 다음 주 기록 재개율 ≥ 50%
- Weekly Mirror 조회자 중 “새롭게 발견한 점이 있다” ≥ 50%
- 21일 종료자 중 “계속 사용하고 싶다” ≥ 20%

숫자는 Prototype 가설이며 데이터에 따라 수정한다.

---

## 20. North Star

**4주 동안 Weekly Mirror를 3회 이상 확인한 활성 사용자 비율**

---

## 21. 장기 비전

사용자가 1~3년 사용했을 때 다음 질문에 자신의 실제 기록을 근거로 답할 수 있어야 한다.

- 나는 언제 가장 행복했나?
- 어떤 관계에서 편안했나?
- 무엇을 할 때 에너지가 올라갔나?
- 어떤 문제가 반복됐나?
- 내가 중요하다고 말했던 가치와 실제 삶이 일치했나?
- 1년 전과 지금의 나는 어떻게 달라졌나?
- 나는 어떤 사람이 되어가고 있나?
