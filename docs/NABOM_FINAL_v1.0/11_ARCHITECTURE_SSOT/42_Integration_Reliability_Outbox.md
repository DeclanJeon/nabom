---
doc_id: PLATFORM-INTEGRATION-001
title: NABOM Integration Reliability
version: 1.0
status: APPROVED_BASELINE
updated_at: 2026-08-11
---

# Integration Reliability / Outbox 설계 v1.0

## 1. 문제

나봄은 PG, Marketplace, 배송, Email, AI 등 외부 시스템과 연결된다.

DB commit 후 외부 호출이 실패하거나,
외부 webhook이 중복/지연되면 데이터가 어긋날 수 있다.

---

## 2. Inbound

Webhook:
- signature verify
- raw event ID 저장
- duplicate ignore
- fast ACK
- async processing
- retry/replay

`InboxEvent`로 idempotency 관리.

---

## 3. Outbound

중요 외부 동기화는 Transactional Outbox pattern을 권장.

예:
Order state 변경 + Notification 요청.

```text
DB Transaction
- business change
- OutboxEvent insert
COMMIT
→ Worker sends external action
```

---

## 4. Reconciliation

Webhook만 믿지 않는다.

주기적으로:
- PG payment
- Settlement
- Marketplace order
- shipment

을 source-of-truth API/statement와 대사.

---

## 5. Retry

분류:
- retryable
- non-retryable
- auth/config
- rate limit

429는 Retry-After 존중.

---

## 6. DLQ

최대 재시도 실패:
Dead Letter Queue.

Admin:
- error
- payload metadata
- retry
- discard with reason

민감 payload는 그대로 UI에 노출하지 않는다.

---

## 7. Ordering

같은 aggregate의 이벤트 순서가 중요하면:
- version
- occurred_at
- aggregate sequence

를 사용.

---

## 8. Marketplace Sync

초기 manual import라도:
- external_order_id unique
- repeated import safe
- update conflict rule

필수.

---

## 9. Provider Adapter

Business layer는:
`TossSpecificPaymentObject`
같은 provider entity를 직접 소유하지 않는다.

Provider payload는 adapter/integration layer에 제한.
