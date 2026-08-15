---
doc_id: LEGACY-B29D134E6C
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 06_OPERATIONS_QA_RELEASE/04_NABOM_FIRST100_Operations.md
---

# NABOM FIRST 100 Beta 실험 및 운영 설계

## 1. 목적

NABOM FIRST 100은 “키링 100개 판매 프로젝트”가 아니라 **나봄(NABOM)의 첫 100개 장기 사용자 프로필을 만드는 실험**이다.

우선순위:

1. 제품 사용성 검증
2. Weekly Mirror 가치 검증
3. NFC 반복 사용 검증
4. 사용자 신뢰 검증
5. 가격/구독 의향 검증
6. 매출

---

## 2. 판매 패키지

### NABOM FIRST 10
예시 가격: 19,900원

목적:
- 강한 피드백
- 제작/배송 흐름 검증
- 초기 콘텐츠 확보

### NABOM FIRST 100
예시 가격: 29,900원

포함:

- 개인 치비 디자인 1종
- 양면 아크릴 키링
- NFC
- Profile 001
- 21일 기록
- Weekly Mirror 최대 3회
- Growth Experiment
- 21일 종료 리포트

배송비 정책은 판매 전에 명확히 고지.

---

## 3. 주문 Flow

```text
SNS / Landing
→ 주문
→ 계정 생성 또는 주문 token
→ 앞면용 사진 업로드
→ 뒷면용 사진 업로드
→ 치비 생성
→ 사용자 승인
→ 인쇄 데이터 생성
→ NFC token 생성
→ 제작
→ NFC write
→ QA
→ 배송
→ 첫 Tap
→ Onboarding
```

---

## 4. 치비 수정 정책

NABOM FIRST 100에서는 무제한 수정 금지.

권장:

- 1차 시안
- 경미한 수정 1회 포함
- 얼굴/헤어/의상 관련 큰 재제작은 별도 정책

주문 페이지에 사전 고지.

---

## 5. NFC 출고 QA

모든 키링은 출고 전:

- NFC read
- URL/token 확인
- 사용자 매핑 확인
- iOS/Android 최소 각 1회 테스트
- 앞/뒷면 인쇄 확인
- 포장 확인

체크리스트로 기록.

---

## 6. CS 예상 항목

- NFC가 안 읽힘
- 어떤 위치에 폰을 대야 하는지 모름
- 로그인 계정 분실
- 태어난 시간을 모름
- 프로필이 안 맞음
- AI 분석이 이상함
- 사진 수정
- 배송 문제
- 키링 분실
- 데이터 삭제 요청
- 결제/환불

각 항목의 canned response와 처리 권한을 미리 정의한다.

---

## 7. NFC 사용 가이드

제품 패키지에 짧은 카드 또는 QR 제공.

예:

1. 휴대폰 NFC를 켜주세요.
2. 키링 뒷면을 휴대폰 NFC 인식 위치에 천천히 대주세요.
3. 기종에 따라 인식 위치가 다를 수 있습니다.
4. 잘 안 되면 QR로 동일한 페이지에 접근할 수 있습니다.

QR은 NFC 실패 시 fallback 역할을 한다.

---

## 8. 실험 Funnel

반드시 이벤트를 수집한다.

```text
landing_view
purchase_started
purchase_completed
design_submitted
design_approved
shipped
nfc_first_tap
onboarding_started
profile_001_created
profile_feedback_submitted
daily_entry_created
weekly_mirror_generated
weekly_mirror_opened
experiment_accepted
experiment_feedback
day21_report_opened
subscription_intent
```

---

## 9. 핵심 Funnel

### A. 물리 제품 Activation
Purchase → Delivery → NFC First Tap

### B. Digital Activation
NFC First Tap → Profile 001

### C. Habit
Profile 001 → First Entry → Day 3 → Day 7

### D. Value
Weekly Mirror Generated → Opened → “새로운 발견 있음”

### E. Retention
Weekly Mirror → 다음 주 기록

---

## 10. 인터뷰

NABOM FIRST 10:
가능하면 전원 인터뷰.

NABOM FIRST 100:
최소 15~20명 인터뷰 목표.

질문:

- 왜 구매했나?
- 키링과 AI 중 무엇이 더 끌렸나?
- 첫 프로필은 어땠나?
- “사주”라고 느꼈나?
- 출생정보를 입력할 때 이상하지 않았나?
- 어떤 분석은 맞고 어떤 것은 틀렸나?
- Daily 기록이 귀찮았나?
- Weekly Mirror에서 새롭게 알게 된 점이 있었나?
- AI가 너무 판단한다고 느낀 적이 있나?
- 21일 뒤 무엇이 남았으면 좋겠나?
- 월 얼마까지 지불할 의향이 있나?

---

## 11. 가격 검증

29,900원이 적절한지 단순 설문보다 실제 conversion을 본다.

테스트 후보:

- 24,900
- 29,900
- 34,900

단, 첫 100명 내에서 너무 많은 가격변형으로 운영 혼란을 만들지 않는다.

---

## 12. 원가 Tracking

주문별:

- 키링 제작비
- 포장
- 배송
- 결제 수수료
- 이미지 생성 비용
- LLM 비용
- 수정 작업시간
- CS 시간

을 추적한다.

핵심은 물리원가보다 **사람이 직접 개입하는 시간**이다.

---

## 13. AI Cost Budget

NABOM FIRST 100부터 사용자 단위 AI 비용을 측정한다.

예:

- Profile 001
- Daily response
- Weekly Mirror
- Experiment
- Day 21 report

각 기능별 token/cost 로깅.

목표:
구독가설을 세우기 전에 사용자당 21일 AI 원가를 알아야 한다.

---

## 14. 실패 기준

다음 중 여러 개가 나오면 제품 구조 재검토:

- Profile 001은 좋아하지만 Daily 기록으로 거의 이어지지 않음
- 기록은 하지만 Weekly Mirror를 열지 않음
- Weekly Mirror가 “이미 아는 이야기”라는 평가가 많음
- AI가 사람을 규정한다고 느끼는 불만이 많음
- 키링 NFC 사용이 배송 직후 1회에 그침
- CS/수정 시간이 매출보다 크게 증가
- 사주 기반 초기 프로필이 신뢰를 훼손

---

## 15. 성공 후 Phase 2

NABOM FIRST 100에서 핵심 Loop가 확인된 후에만:

- Monthly Mirror
- Mini-IPIP/Big Five
- Motivation Engine
- 음성기록
- Similar Moments
- 장기 채팅
- 커플/가족 상품
- 그룹/공동체 상품

을 추가한다.


---

## 16. 브랜드 운영 기준

### 판매명
**NABOM FIRST 100**

### 기본 노출 문구
> 기록할수록 선명해지는 나.

### 랜딩페이지 URL
`https://nabom.ponslink.com`

### 키링 안내 URL
NFC/QR 모두 `https://nabom.ponslink.com/k/{token}` 계열로 통일한다.

### 패키징 노출 우선순위
1. NABOM / 나봄
2. 기록할수록 선명해지는 나.
3. NFC 또는 QR 사용법
4. PonsLink 표기는 보조 브랜드 수준으로 제한
