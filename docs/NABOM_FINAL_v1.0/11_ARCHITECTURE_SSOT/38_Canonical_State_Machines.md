---
doc_id: SYS-STATE-001
title: NABOM Canonical State Machines
version: 1.0
status: SSOT
updated_at: 2026-08-11
---

# Canonical State Machines v1.0

## 1. 핵심 원칙

**한 개의 OrderStatus에 모든 업무상태를 넣지 않는다.**

---

# 2. Order Lifecycle

```text
DRAFT
→ OPEN
→ COMPLETED

DRAFT/OPEN → CANCELLED
```

Order의 상세 진행은 아래 subdomain status로 판단한다.

---

# 3. Payment

```text
PENDING
→ AUTHORIZED
→ CAPTURED
→ PARTIALLY_REFUNDED
→ REFUNDED

PENDING/AUTHORIZED → FAILED
AUTHORIZED → CANCELLED

CAPTURED
→ CHARGEBACK_OPEN
→ CHARGEBACK_WON | CHARGEBACK_LOST
```

---

# 4. Customization

```text
NOT_REQUIRED
or
ASSET_REQUIRED
→ ASSET_SUBMITTED
→ DESIGNING
→ PROOF_READY
→ CUSTOMER_REVIEW
   ├→ REVISION_REQUESTED → DESIGNING
   └→ APPROVED
```

`APPROVED`가 Production Lock의 주요 조건이다.

---

# 5. Fulfillment / Production

```text
NOT_READY
→ PRODUCTION_READY
→ PRINT_ASSET_READY
→ PRODUCTION
→ QC
→ PACKED
→ FULFILLED
```

실패/예외:
- ON_HOLD
- QC_FAILED
- REPRINT_REQUIRED

---

# 6. Shipment

```text
ADDRESS_REVIEW
→ LABEL_CREATED
→ PICKED_UP
→ IN_TRANSIT
→ DELIVERED

IN_TRANSIT
→ DELIVERY_FAILED
→ IN_TRANSIT | RETURN_TO_SENDER

IN_TRANSIT → LOST
RETURN_TO_SENDER → RETURN_RECEIVED
RETURN_RECEIVED → RESHIPPED
```

---

# 7. Digital Fulfillment

```text
NOT_REQUIRED
or
TOKEN_RESERVED
→ PAGE_DRAFT
→ PAGE_READY
→ ACTIVATED
→ CLAIMED(optional)
```

Page moderation status는 별도.

---

# 8. Group Buy Campaign

```text
DRAFT
→ OPEN
→ GOAL_REACHED
→ CLOSED
→ PRODUCTION_LOCKED
→ PRODUCTION
→ COMPLETED

DRAFT/OPEN/CLOSED → CANCELLED
```

### Goal Miss
`OPEN → CLOSED → CANCELLED`
후 eligible participant payments를 환불.

### Production Lock
다음 조건을 모두 만족해야 한다.
- campaign close
- 진행수량 확정
- 결제 확정
- personalization cutoff
- organizer 정책 조건 만족

---

# 9. Group Participant

```text
INVITED(optional)
→ JOINED
→ PAYMENT_PENDING
→ PAID
→ ASSET_PENDING
→ READY
→ LOCKED
→ FULFILLED
```

취소 가능 범위는 Campaign policy를 따른다.

---

# 10. Subscription

```text
TRIALING
→ ACTIVE
→ PAST_DUE
→ GRACE
→ EXPIRED

ACTIVE → CANCEL_AT_PERIOD_END → EXPIRED
ACTIVE → CANCELLED
```

---

# 11. Page Moderation

```text
ACTIVE
→ REPORTED
→ UNDER_REVIEW
→ RESTORED | LIMITED | SUSPENDED | REMOVED
```

# 12. Relationship / InsightGroup

## Relationship

```text
DRAFT
→ CONSENT_PENDING
→ ACTIVE
→ PAUSED
→ REVOKED
→ DELETED
```

`ACTIVE`는 양쪽의 분석 동의와 공개 범위가 유효할 때만 가능하다. 동의 철회 또는 권한 범위 축소 시 `PAUSED`로 전환하고 새 분석 생성을 중단한다.

## InsightGroup

```text
DRAFT
→ INVITING
→ ACTIVE
→ PAUSED
→ ARCHIVED
```

`ACTIVE` 분석은 최소 5명의 활성 동의 구성원을 요구한다. 구성원 상태:

```text
INVITED → JOINED → ACTIVE → LEFT | REMOVED
```

구성원 이탈로 최소 인원 조건을 충족하지 못하면 그룹은 `PAUSED`가 되며 공동 기록·설명 페이지 외의 개인 추정 분석은 제공하지 않는다.

# 13. Insight Consent

```text
REQUESTED → GRANTED | DECLINED
GRANTED → REVOKED
```

모든 전이는 actor, scope, policy version, reason, timestamp, audit reference를 기록한다.

---

# 12. Claim / Return

```text
REQUESTED
→ EVIDENCE_REQUIRED
→ APPROVED | REJECTED

APPROVED
→ REPRINTING | RETURN_IN_TRANSIT | REFUNDING
→ COMPLETED
```

---

# 13. State Transition Rule

모든 중요한 transition은 다음을 기록한다.

- from
- to
- actor
- reason
- timestamp
- idempotency/ref
- audit metadata

운영자가 DB를 직접 수정하는 방식으로 상태를 바꾸지 않는다.
