---
doc_id: LEGACY-BE1286ECB2
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 05_GROUPBUY_CHANNELS_GLOBAL/20_Omnichannel_Domestic_Global_Strategy.md
---

# NABOM 국내·해외 옴니채널 판매 전략 v1.0

기준일: 2026-08-11

## 0. 결론

나봄은 처음부터 모든 결제·상품노출·해외판매 기능을 자체몰에 구현하지 않는다.

권장 구조:

```text
[고객 유입/결제 채널]
SmartStore / idus / Etsy / Pinkoi / NABOM Direct
                ↓
        Sales Channel Adapter
                ↓
          NABOM Order Hub
                ↓
Customization / Proof / Production / NFC / Page / Shipping
                ↓
       nabom.ponslink.com
```

핵심은 **판매채널과 나봄 서비스 본체를 분리**하는 것이다.

- 마켓플레이스: 고객획득, 신뢰, 결제, 리뷰
- 나봄 플랫폼: 개인화 제작, 디자인 승인, NFC/QR, Digital Page, Living Profile, 공동구매, 구독

단, 각 마켓플레이스에서 시작된 거래를 정책 위반 방식으로 외부 결제로 이동시키지 않는다.

---

# 1. 왜 이 구조가 필요한가

자체 쇼핑몰은 장기적으로 필요하지만 FIRST 10~100 단계에서 아래를 모두 직접 구현하면 과도하다.

- 국내 결제
- 환불
- 현금영수증
- 주문관리
- 리뷰
- 쿠폰
- 고객문의
- 마케팅
- 검색노출
- 해외카드
- 다통화
- 해외정산

따라서 초기에는 이미 검증된 판매 플랫폼을 **Commerce Shell**로 활용하고, 나봄만의 차별기능을 자체 개발한다.

---

# 2. 운영모드

## MODE A. Lean Korea Launch

권장 시점:
FIRST 1~30.

### 결제/주문
**네이버 스마트스토어**

### 보조 판매
**아이디어스**

### 자체 사이트
`nabom.ponslink.com`

자체 사이트 역할:
- 브랜드 소개
- 제품 데모
- NFC/QR 활성화
- 주문 후 제작자료 관리
- 시안 확인
- 맞춤 Page
- Living Profile
- Weekly Mirror

이 단계에서 자체 PG 결제는 없어도 된다.

### 장점
- PG/결제 UI 개발량 감소
- 네이버의 주문/정산/클레임 도구 이용
- 첫 판매에 필요한 신뢰 확보
- 상품 수요부터 검증 가능

### 단점
- 복잡한 옵션 UX 제한
- 자체 Funnel 데이터 제한
- 공동구매/페이지 상품과의 결합이 어려움

따라서 **물리 굿즈 판매는 SmartStore**, 나봄의 특수 기능은 자체 플랫폼이라는 역할분담을 한다.

---

# 3. SmartStore-first 주문 흐름

```text
SmartStore Product
→ SmartStore Checkout
→ Payment Complete
→ NABOM Order Hub에 주문 등록
→ Customization Intake
→ Proof
→ Approval
→ Production
→ Shipping
→ Product Received
→ NFC/QR Activation
→ NABOM Digital Experience
```

## 주문 연동

### 초기
수동 등록 또는 CSV/운영자 입력.

### 이후
Naver Commerce API Adapter.

네이버 커머스 API는 상품, 주문, 정산 등 주요 스마트스토어 기능을 API로 제공하므로 판매량이 늘면 자동화한다.

---

# 4. 채널별 커스터마이징 Intake

각 플랫폼마다 허용되는 방식이 다를 수 있으므로 공통 external upload를 강제하지 않는다.

```text
CustomizationIntakeAdapter

OWN_STORE
→ NABOM Upload Portal

SMARTSTORE
→ 플랫폼이 허용하는 옵션/톡톡/메시지
→ 정책 확인 후 secure upload portal 적용 가능

IDUS
→ 작품 옵션 + 작가 메시지

ETSY
→ Listing Personalization + Etsy Messages

PINKOI
→ 플랫폼 옵션/메시지
```

원칙:

> **거래는 판매가 시작된 채널 안에서 완료한다.**

외부 나봄 페이지는 커스텀 제작 workflow 또는 구매 후 제품 기능을 제공하기 위한 용도로만 사용하며, 각 플랫폼 정책을 먼저 검토한다.

---

# 5. 스마트스토어에 올릴 상품

스마트스토어는 복잡한 디지털서비스 전체를 판매하는 곳으로 사용하지 않는다.

초기 권장 SKU:

### NABOM Duo Charm
개인화 아크릴 + Portal Charm.

### NABOM Memory Charm
NFC 없는 실물 버전.

### NABOM Gift Set
실물 + Gift/Memory Page entitlement.

### NABOM Group Sample
10명 이상 단체는 “견적문의/상담” 흐름으로 연결.

NFC 활성화와 Digital Page 관리는 나봄 서비스에서 수행한다.

---

# 6. 아이디어스 역할

아이디어스는 나봄에게 **커스텀 선물 수요 발견 채널**로 사용한다.

적합:
- 치비 굿즈
- 커스텀 사진
- 기념일
- 선물
- 소량 주문

아이디어스는 현재 작가용 주문관리와 메시지, 매출관리, 해외 물류·자동번역을 통한 글로벌 판매 지원을 안내하고 있다.

초기에는 SmartStore와 idus에 동일 SKU를 모두 올리기보다:

- SmartStore: 대표 대중 상품
- idus: 감성/선물/커스텀 상품

으로 상품 카피를 차별화한다.

---

# 7. MODE B. Domestic Scale

권장 조건:
- 누적 30~100건
- 주 10건 이상 반복
- 자체 공동구매 수요 발생
- Digital Page 단독 구매 수요 발생

이 시점에 자체 PG를 붙인다.

## 자체몰에서만 가능한 핵심기능

- 공동구매
- B2B bulk order
- Page Builder
- Digital-only Page
- Living Service subscription
- 복잡한 Bundle
- Gift Claim
- 다단계 Customization
- 자동 시안 승인

물리 단품은 SmartStore에도 계속 유지한다.

---

# 8. 국내 최종 채널 포지션

| 채널 | 역할 | 추천 상품 |
|---|---|---|
| NABOM Direct | 본진 / 고마진 / 복합상품 | 공동구매, Page, 구독, Bundle |
| SmartStore | 검색 / 신뢰 / 결제편의 | 대표 키링, Gift Set |
| idus | 커스텀/선물 발견 | 감성 굿즈, 주문제작 |
| Offline/B2B | 대량영업 | 회사, 교회, 학교, 이벤트 |

모든 채널을 동일하게 운영하지 않는다.

---

# 9. MODE C. Overseas Marketplace Test

해외는 자체몰부터 만들지 않는다.

## 1차 테스트
- Etsy
- idus Global 가능 여부
- Pinkoi

### Etsy
역할:
Personalized Gift의 국제 수요 검증.

한국 판매자는 Etsy Payments를 Payoneer Payment Account를 통해 이용할 수 있는 국가에 포함된다.

주의:
Etsy는 거래를 플랫폼 밖에서 완료하도록 유도하는 행위를 금지한다.

따라서:

```text
Etsy 발견
→ Etsy 결제
→ Etsy 주문
→ Etsy 허용 범위 내 personalization
→ 제작/배송
→ 물리 제품 속 NFC/QR
→ NABOM 제품 경험
```

으로 설계한다.

**NFC/QR을 외부 결제를 유도하는 장치로 사용하면 안 된다.**

NFC는 판매 후 제품의 디지털 기능이다.

---

# 10. Pinkoi

대만/아시아 디자인상품 테스트 채널.

현재 Pinkoi 판매자 안내의 플랫폼 서비스료 구조는:

```text
(상품금액 + 배송비) × 15% + NT$15
```

수준이므로 저마진 상품을 그대로 올리기보다 해외 판매가를 별도로 설계한다.

추천:
- Premium gift
- Acrylic/Bag Charm
- Memory Page Bundle

---

# 11. 해외 가격은 국내가격 환산이 아니다

예:

한국:
29,900 KRW

해외:
`29,900원을 환율로 USD 변환`

하지 않는다.

국가별로:

```text
Product Cost
+ Packaging
+ Platform Fee
+ Payment Fee
+ Shipping
+ Customs Risk Buffer
+ CS Risk
+ Margin
```

을 계산해 **Localized Fixed Price**를 만든다.

---

# 12. 해외 배송전략

초기:
- 한국에서 직배송
- 상품과 포장을 최대한 경량화
- 국가별 배송비 별도

CountryLaunchConfig:

```text
country
enabled
currency
shipping_method
shipping_price
customs_policy
return_policy
product_available
digital_available
```

한 번에 Global On/Off 하지 않는다.

---

# 13. MODE D. NABOM Global Direct

조건:
- 해외 marketplace 주문 반복
- 특정 국가 월 20~30건 이상 후보
- 현지 고객이 나봄 Digital Service를 실제 사용
- 플랫폼 수수료 절감 필요

이때:

`nabom.ponslink.com/{locale}`

자체 해외 결제를 연다.

토스페이먼츠는 현재 추가 계약을 통해 해외카드와 PayPal 연동을 제공하고, 해외카드는 KRW 기본 결제 및 별도 계약 시 USD/JPY 등 다통화 결제를 지원한다고 안내한다.

따라서 한국 사업자가 자체 Global Store를 운영하는 기술적 경로가 있다.

다만:
- 해외카드 계약
- 카드사 심사
- PayPal 추가 계약
- 다통화 MID
- 영문 약관
이 필요하다.

---

# 14. 해외 자체몰 권장 순서

### Phase 1
영문 Landing만.

구매:
Etsy.

### Phase 2
JPY/일본 Landing.

구매:
Marketplace 중심.

### Phase 3
NABOM Direct Global Checkout.

결제:
해외카드 / PayPal.

이 방식이 개발비와 법·정산 부담을 가장 늦게 발생시킨다.

---

# 15. SalesChannel 데이터 모델

```text
SalesChannel
- NABOM_DIRECT
- NAVER_SMARTSTORE
- IDUS
- ETSY
- PINKOI
- B2B_OFFLINE
```

## ChannelListing

```text
channel
external_listing_id
product_id
variant_mapping
channel_price
currency
status
```

## ExternalOrder

```text
channel
external_order_id
external_customer_ref
gross_amount
channel_fee
payment_fee
payout_amount
currency
status
```

내부 `Order`에 연결한다.

---

# 16. Channel Adapter

```text
ChannelAdapter
 ├─ ProductSync
 ├─ OrderImport
 ├─ SettlementImport
 ├─ FulfillmentExport
 └─ CustomerMessageLink
```

MVP에서는 모든 adapter를 구현하지 않는다.

우선:
1. SmartStore Order Adapter
2. SmartStore Settlement Adapter
3. Etsy manual import
4. 기타 수동

---

# 17. Unified Order Hub

관리자가 한 화면에서:

```text
[NAVER] N202608...
[IDUS] I202608...
[ETSY] E202608...
[DIRECT] D202608...
```

를 같은 제작 Kanban으로 처리해야 한다.

판매 채널이 달라도 이후 workflow는 동일:

```text
Order
→ Asset
→ Proof
→ Production
→ NFC
→ QC
→ Shipment
```

이게 핵심이다.

---

# 18. 채널별 정산

절대 `판매가 = 매출 입금액`으로 계산하지 않는다.

```text
Gross Sale
- Discount
- Platform Fee
- Payment Fee
- Advertising Fee
- Refund
- Shipping Subsidy
= Channel Payout
```

플랫폼별 Payout을 주문과 대사한다.

---

# 19. 플랫폼 정책 보호

Admin에 채널별 rule metadata를 둔다.

예:

```text
allow_external_checkout: false
allow_external_customization_url: review_required
allowed_message_channel: ETSY_MESSAGE
```

운영자가 실수로 Etsy 구매자에게 “여기서 다시 결제하세요” 같은 메시지를 보내지 않도록 한다.

---

# 20. 추천 최종 실행안

## 지금

### 국내
1. SmartStore 개설
2. NABOM 대표 키링 2~3 SKU 등록
3. idus 입점 테스트
4. nabom.ponslink.com은 브랜드 + 주문제작 workflow + NFC/QR 서비스로 개발

### 자체몰
아직 완전한 checkout을 만들지 않아도 된다.

먼저:
- 계정
- Order Claim
- Asset Upload
- Proof
- NFC
- Page
를 만든다.

---

## FIRST 30 이후

- SmartStore Commerce API 연동
- Unified Order Hub
- 자체 PG
- 공동구매
- Page Builder

---

## FIRST 100 이후

### 해외
- Etsy 10~20건 테스트
- idus Global/Pinkoi 테스트
- 국가별 CAC/배송/CS 측정

---

## 해외 반복주문 확인 후

- NABOM Global Direct
- Toss foreign card
- PayPal
- JPY/USD fixed pricing

---

# 21. 이 전략의 핵심

초기에는:

> **쇼핑몰을 만드는 것이 사업이 아니라 판매하는 것이 사업이다.**

그래서 네가 직접 만들어야 하는 부분은:

- 나봄 고유의 customization
- NFC/QR
- Digital Page
- Living Profile
- 공동구매

이고,

이미 잘 만들어져 있는:

- 국내 일반 결제
- 기본 주문관리
- 리뷰
- 검색
- 고객 신뢰

는 SmartStore/marketplace를 빌린다.

판매가 확인되면 그때 하나씩 자체몰로 가져온다.
