---
doc_id: LEGACY-7E2C6D38C5
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 03_COMMERCE_PLATFORM/17_Commerce_IA_Admin_Operations.md
---

# NABOM 쇼핑몰 IA / Admin / 운영 화면 설계 v1.0

# 1. 고객 IA

## Global Nav

### Shop
- 전체
- 나를 위한 선물
- 소중한 사람에게
- 공동체/단체
- NFC/QR Pages

### Group Buy
- 진행중 공동구매
- 공동구매 만들기

### Create Page
- 맞춤 페이지 만들기

### About NABOM
- 사용방법
- 브랜드 이야기

### My
- 주문
- 페이지
- NFC
- 공동구매

---

# 2. 홈

섹션 순서:

1. Hero
2. 대표 제품
3. 사진 → 치비 → 실물 데모
4. NFC tap 데모
5. 페이지 데모
6. 공동구매
7. 용도별
8. 후기
9. FIRST 100/프로모션
10. FAQ

---

# 3. 상품 상세

Above Fold:

- 이미지/영상
- 상품명
- 한 줄 가치
- 가격
- 후기
- 제작기간
- 옵션
- CTA

아래:

- 구성품
- 커스텀 과정
- NFC/QR
- 페이지 옵션
- 실제 사례
- 사이즈
- 제작 안내
- 수정 정책
- 배송/환불
- FAQ

Sticky CTA mobile.

---

# 4. 마이페이지

Dashboard card:

- 진행 주문
- 시안 확인 필요
- 내 NFC
- 내 페이지
- 공동구매
- Weekly Mirror (나봄 사용자일 경우)

---

# 5. Admin Navigation

## Dashboard
오늘:
- 결제
- 신규 주문
- 시안대기
- 승인대기
- 생산대기
- 출고
- CS
- 공동구매

## Orders
필터:
- status
- product
- group
- date
- customer

## Production
Kanban:

```text
Assets
Design
Proof
Approved
Print Ready
Production
QC
Packed
```

## Proofs
수정 대기/승인.

## Products
- 상품
- 옵션
- 가격
- 커스터마이징 schema
- 페이지 bundle

## Group Buy
- campaign
- organizer
- participant
- completeness
- goal

## Pages
- drafts
- assisted orders
- publish
- abuse/report

## NFC
- tag
- token
- page
- last tap
- status

## Shipping
- bulk
- individual
- tracking

## Customers
Commerce 기준 정보.
Living Profile 민감정보는 별도 권한.

## Promotions
- coupon
- codes
- first buyer
- group

## Reviews
moderation.

## Support
tickets.

## Analytics
funnel.

## Settings
- PG
- shipping
- terms
- locale
- admin role

---

# 6. 운영 Kanban

가장 자주 볼 화면은 Order List보다 제작 Kanban일 가능성이 높다.

Card 표시:

```text
#N260812-031
김나봄
Duo Charm ×1
[사진 O] [시안 수정1]
D+2
공동구매: Mission26
```

클릭:
- 주문
- 사진
- production asset
- proof history
- NFC
- shipping
- CS

---

# 7. 알림

고객:
- 결제완료
- 자료 필요
- 시안 준비
- 수정완료
- 제작시작
- 출고
- NFC 활성화
- 공동구매 달성

운영자:
- 결제 webhook 실패
- 마감 공동구매
- 시안 SLA 초과
- 배송 오류
- NFC 미프로비저닝

---

# 8. SLA

초기 내부 목표:

- 자료확인: 1영업일
- 1차 시안: 1~2영업일 가설
- 수정: 1영업일
- 승인 후 제작: 공급처 기준
- CS 답변: 영업일 24시간

실제 공급처 리드타임 데이터 후 수정.


---

# 9. Omnichannel Admin v1.0

주문 목록에 Channel 표시:

```text
[NABOM]
[NAVER]
[IDUS]
[ETSY]
[PINKOI]
[B2B]
```

필터:
- channel
- country
- currency
- external/internal
- payout reconciled

Order 상세:
- Internal Order
- External Order ID
- Channel
- Marketplace customer alias
- Channel message shortcut
- Gross
- Fees
- Payout
- Customization status

Settlement Dashboard:
- 미대사 주문
- 예상 정산
- 실제 정산
- fee 차이
- 환불 차이
