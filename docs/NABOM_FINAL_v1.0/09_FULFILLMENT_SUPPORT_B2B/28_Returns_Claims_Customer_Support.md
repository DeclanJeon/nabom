---
doc_id: LEGACY-A5D556DD73
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 09_FULFILLMENT_SUPPORT_B2B/28_Returns_Claims_Customer_Support.md
---

# NABOM Returns / Claims / Customer Support 설계 v1.0

## 1. Support Ticket

필드:
- customer
- order
- category
- priority
- channel
- status
- assigned_to
- SLA
- attachments
- internal_notes

상태:
```text
OPEN
WAITING_CUSTOMER
WAITING_INTERNAL
RESOLVED
CLOSED
```

---

## 2. Issue Category

- payment
- customization
- proof
- production
- damaged
- wrong_item
- NFC
- page
- shipping
- refund
- privacy
- account
- group_buy

---

## 3. Return / Exchange / Reprint

나봄에서는 일반 반품과 재제작을 구분한다.

### Reprint
- 인쇄불량
- 잘못된 이미지
- 제작오류

### Replacement
- NFC 불량
- hardware 결함

### Return
상품/법적 청약철회 정책에 따른 반품.

---

## 4. Claim 상태

```text
REQUESTED
EVIDENCE_REQUIRED
APPROVED
REJECTED
REPRINTING
RETURN_IN_TRANSIT
RETURN_RECEIVED
REFUNDING
COMPLETED
```

---

## 5. Evidence

고객:
- 사진
- 영상
- 설명

운영:
- 출고 QC
- proof 승인본
- batch
- NFC verification

---

## 6. 비용 책임

ReasonCode에 따라:
- NABOM
- carrier
- customer
- supplier

를 기록.

---

## 7. Order Edit Window

결제 후:
- 배송지
- 이미지
- 옵션
- 페이지 내용

수정 가능 cutoff를 명확히 한다.

`PRODUCTION_LOCK` 이후 물리제작 관련 변경 제한.

---

## 8. 배송 사고

### Lost
carrier 확인 → replacement/refund 정책.

### Return to Sender
원인:
- 주소오류
- 미수령
- 통관
- carrier

재배송비 책임 규칙 필요.

---

## 9. NFC/Page Support

- NFC 위치 가이드
- QR fallback
- token reset
- destination correction
- ownership claim recovery

민감 데이터 접근이 필요한 CS는 escalation.

---

## 10. Support KPI

- first response time
- resolution time
- reprint rate
- defect rate
- refund rate
- repeat contact
- CS minutes/order
