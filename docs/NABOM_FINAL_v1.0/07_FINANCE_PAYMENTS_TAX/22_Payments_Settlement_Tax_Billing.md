---
doc_id: LEGACY-27450A413E
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 07_FINANCE_PAYMENTS_TAX/22_Payments_Settlement_Tax_Billing.md
---

# NABOM Payments / Settlement / Tax / Billing 설계 v1.0

## 1. 목적

주문금액, 실제 결제, 환불, PG 정산, 플랫폼 정산, 회계용 매출을 서로 분리하고 대사한다.

핵심 원칙:

> Order Total ≠ Payment Captured ≠ Channel Payout ≠ Accounting Revenue

---

## 2. 결제 Domain

### PaymentIntent
- order_id
- provider
- method
- amount
- currency
- status
- idempotency_key

### PaymentTransaction
- authorization
- capture
- cancel
- partial_refund
- refund
- chargeback

### Payment 상태
```text
PENDING
AUTHORIZED
CAPTURED
FAILED
CANCEL_REQUESTED
CANCELLED
PARTIALLY_REFUNDED
REFUNDED
CHARGEBACK_OPEN
CHARGEBACK_WON
CHARGEBACK_LOST
```

---

## 3. 결제 예외

반드시 처리:
- 고객 화면 timeout, PG는 성공
- PG 성공, 내부 Order 생성 실패
- webhook 중복
- webhook 순서 뒤바뀜
- refund API 실패
- 부분환불
- 복수 상품 중 일부 취소
- 해외 환불 환율차
- PG 장애

모든 결제 API는 idempotent하게 설계한다.

---

## 4. Settlement

### PGSettlement
- provider
- settlement_date
- gross
- fee
- vat_on_fee
- refund
- adjustment
- net

### ChannelSettlement
SmartStore / idus / Etsy / Pinkoi 별도.

### Reconciliation
매일 또는 정산주기별:

```text
Internal Payment
↔ PG/Marketplace Statement
↔ Bank Deposit
```

상태:
- MATCHED
- AMOUNT_MISMATCH
- MISSING_INTERNAL
- MISSING_EXTERNAL
- PENDING

Admin에 미대사 항목 큐를 둔다.

---

## 5. Price Snapshot

OrderItem에는 주문 당시 가격을 immutable snapshot으로 저장한다.

- list_price
- sale_price
- option_delta
- customization_fee
- page_fee
- coupon_discount
- group_discount
- shipping_allocated
- tax
- final_price

상품 가격 변경이 과거 주문에 영향을 주면 안 된다.

---

## 6. 쿠폰/포인트

규칙:
- 기간
- 사용횟수
- 사용자당 한도
- 최소주문
- 상품/카테고리 제외
- 다른 할인과 중복
- 취소/환불 시 복원정책

Self-referral / coupon abuse 방지.

---

## 7. 현금영수증 / 세금계산서 / B2B 증빙

자체몰에서 실제 지원 범위는 PG 및 세무 프로세스와 맞춰 확정한다.

데이터모델에는 최소:
- receipt_type
- receipt_identifier
- business_registration_no
- company_name
- tax_invoice_requested
- invoice_status

를 둘 수 있게 한다.

B2B는 견적/계약/증빙 문서와 연결한다.

---

## 8. 회계 Export

월 단위 export:
- gross sales
- refunds
- discounts
- shipping revenue
- platform fees
- PG fees
- ad fees
- product cost
- settlement amount
- channel
- country
- currency

CSV/XLSX export를 지원.

---

## 9. 환불 계산

Bundle은 구성요소 단위 entitlement와 제작상태를 확인한다.

예:
```text
Physical: 제작 전
Digital Page: publish 완료
Weekly Mirror: 1/3 사용
```

환불 가능액은 정책 엔진이 계산하고, 운영자가 근거를 확인할 수 있어야 한다.

---

## 10. 해외 통화

Order:
- display_currency
- charged_currency
- settlement_currency
- fx_reference(optional)

해외 판매가는 실시간 KRW 환산보다 국가별 고정가격을 권장한다.

---

## 11. Finance Admin

- Today Sales
- Captured
- Refund
- Pending Refund
- Settlement
- Channel Fees
- Unreconciled
- Margin Estimate
- Export
