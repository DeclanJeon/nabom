---
doc_id: LEGACY-14DC1BC904
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 05_GROUPBUY_CHANNELS_GLOBAL/14_Group_Buy_System.md
---

# NABOM 공동구매 시스템 설계 v1.0

## 1. 공동구매의 목적

공동구매는 가격 할인 기능이 아니라 **그룹 단위 개인화 주문을 운영 가능하게 만드는 핵심 B2B/B2C 기능**이다.

대상:
- 교회
- 선교팀
- 대학 동아리
- 회사
- 워크숍
- 졸업반
- 팬모임
- 친구 여행
- 가족

---

# 2. 공동구매 유형

## Type A. 목표수량형
예:
10명 이상 모이면 제작.

- 최소 인원
- 목표 인원
- 최대 인원
- 종료일

## Type B. 단계할인형
예:
10명 29,900
20명 27,900
50명 24,900

참가 인원에 따라 최종가격 결정.

## Type C. 주최자 확정형
이미 조직된 팀.

주최자가 20명 패키지를 구매하고 참가자에게 입력 링크 배포.

## Type D. 예약금형
참가자는 예약금만 결제.
달성 후 잔금.

MVP에서는 복잡도가 높으므로 후순위.

---

# 3. 권장 MVP

MVP는 두 가지.

### Organizer Package
주최자가 인원/상품을 정하고 전체 또는 일부 결제.

### Participant Pay
각 참가자가 자기 상품을 직접 결제.

---

# 4. 공동구매 생성

주최자 입력:

- 캠페인 제목
- 대표 이미지
- 그룹명
- 상품
- 기본 디자인
- 참가자 개인화 가능 항목
- 최소 인원
- 최대 인원
- 마감
- 배송방식
- 공개/초대전용
- 주최자 메시지

생성하면:

`nabom.ponslink.com/group-buy/{slug}`

짧은 공유 URL `/g/{slug}`는 canonical 페이지로 redirect하는 alias로만 사용한다.

링크/QR 생성.

---

# 5. 참가 UX

```text
Invite Link
→ Campaign Landing
→ 현재 참가자 / 마감 / 가격
→ 참가하기
→ 이름
→ 개인사진
→ 개인 옵션
→ 배송지
→ 결제
→ 제출완료
```

로그인 없이 먼저 참여 후 결제 단계에서 계정 생성도 가능.

---

# 6. 개인화 범위

주최자가 설정.

예:

공통:
- 뒷면 단체사진
- 링 색상
- Portal 디자인
- Community Page

개인:
- 이름
- 앞면 치비
- 닉네임
- 개인 페이지

---

# 7. 공동 페이지

공동구매에는 Group Page를 붙일 수 있다.

예:
`Mission Team 2026`

구성:
- 대표 사진
- 행사 설명
- 참가자 목록
- 단체 갤러리
- 개인 페이지 링크

각 개인의 민감한 Living Profile은 자동 공개하지 않는다.

---

# 8. 결제 방식

### Organizer Pays All
주최자 한 번 결제.

참가자는 개인화 정보만 제출.

### Individual Pay
각자 결제.

### Split Sponsor
주최자가 일정금액 보조.
예:
상품 29,900원 중 조직 10,000원 부담, 참가자 19,900원.

Phase 2 강력 추천.

---

# 9. 목표 달성

Campaign 상태:

- DRAFT
- OPEN
- GOAL_REACHED
- CLOSED
- PRODUCTION_LOCKED
- PRODUCTION
- SHIPPED
- COMPLETED
- CANCELLED

MVP에서는 목표 미달 시:
- 자동 취소/환불
또는
- 주최자에게 진행/취소 결정권

정책을 캠페인 생성 시 명시.

---

# 10. 가격 Lock

공동구매에서 가장 까다로운 부분.

단계할인형은 참가시점 가격과 최종가격이 다를 수 있다.

권장 MVP:
**최종 목표구간 가격으로 선결제하지 않는다.**

간단하게:
- 캠페인 생성 시 확정 단가
- 최소 인원 달성 여부만 사용

단계할인은 Phase 2.

---

# 11. 배송

### Bulk Ship
한 주소로 전체 배송.
가장 저렴.

### Individual Ship
각 참가자 주소로 개별배송.
배송비 개인부담.

### Hybrid
일부만 개별.

MVP:
Bulk + Individual 지원.

---

# 12. 주최자 Dashboard

표시:
- 참가자 수
- 목표
- 결제완료
- 자료제출
- 시안승인
- 배송
- 미완료 참가자
- 초대링크

액션:
- 참가자 리마인드
- 마감 연장
- 캠페인 닫기
- CSV 다운로드
- 메시지 발송

개별 참가자의 민감한 데이터는 주최자에게 보여주지 않는다.

---

# 13. 운영자 Dashboard

- Campaign
- Organizer
- Participant
- Payment
- Personalization completeness
- Production batch
- Shipping mode
- Issues

Batch export:
`participant → print asset → token → shipping`

---

# 14. 공동구매 자동 리마인드

이벤트:
- 3일 남음
- 24시간 남음
- 결제 미완료
- 사진 미제출
- 시안 미승인

Email/Kakao/SMS는 provider 비용과 개인정보 정책에 따라 적용.

---

# 15. B2B 견적 전환

공동구매 인원이 일정 수준 이상이면:

`50명 이상인가요? 맞춤 견적 받기`

Quote Request로 전환.

필드:
- 조직
- 인원
- 행사일
- 제품
- 페이지
- 배송
- 예산
