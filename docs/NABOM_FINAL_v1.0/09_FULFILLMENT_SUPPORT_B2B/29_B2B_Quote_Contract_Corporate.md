---
doc_id: LEGACY-74015D083D
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 09_FULFILLMENT_SUPPORT_B2B/29_B2B_Quote_Contract_Corporate.md
---

# NABOM B2B Quote / Contract / Corporate Account 설계 v1.0

## 1. 대상

- 회사
- 교회
- 학교/동아리
- 행사
- 팬 커뮤니티
- 기관

---

## 2. Lead → Deal

```text
Lead
→ Qualified
→ Sample/Demo
→ Quote
→ Negotiation
→ Accepted
→ Contract/PO
→ Production
→ Delivery
→ Settlement
```

CRM 최소필드:
- organization
- contact
- size
- event_date
- budget
- product
- page requirement
- delivery
- status
- next_action

---

## 3. Quote

- quote_no
- valid_until
- quantity
- unit_price
- customization
- page/service
- shipping
- tax
- payment terms
- lead time

PDF/HTML export 후보.

---

## 4. 계약 / 발주

초기에는 전자계약 시스템을 직접 만들 필요 없음.

다만 Order에:
- contract_ref
- purchase_order_no
- customer_company
- billing_contact
를 연결 가능하게 한다.

---

## 5. Corporate Account

Phase 2:
- organization
- members
- billing admins
- project managers

개인 Living Profile은 조직 관리자에게 자동 공개하지 않는다.

---

## 6. B2B 결제

지원 후보:
- 카드
- 계좌이체
- 선금/잔금
- invoice/세금계산서 프로세스

고액 주문은 PG 카드결제만 강제하지 않는다.

---

## 7. Approval

B2B 프로젝트:
- master design
- participant data
- production proof
- invoice
승인 단계를 둘 수 있다.

---

## 8. 참가자 수집

방법:
- 초대링크
- CSV import
- organizer pays
- participant pays

민감한 개인 입력은 organizer가 전부 볼 수 없게 한다.

---

## 9. White-label

Phase 2:
- organization logo
- event page
- custom color
- co-brand

NABOM 완전 제거는 별도 가격정책.

---

## 10. B2B KPI

- lead response
- meeting
- quote
- win rate
- average order value
- gross margin
- manual minutes
- repeat order
