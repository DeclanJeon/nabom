---
doc_id: PLATFORM-MSG-001
title: NABOM Notification and Messaging
version: 1.0
status: APPROVED_BASELINE
updated_at: 2026-08-11
---

# Notification / Messaging 설계 v1.0

## 1. 분리 원칙

### Transactional
서비스 수행에 필요한 알림.
- 결제
- 시안
- 출고
- 공동구매 마감
- 계정 보안

### Product
- Weekly Mirror
- Growth reminder

### Marketing
- 할인
- 신상품
- 캠페인

Marketing은 별도 동의/철회.

---

## 2. Channel

초기:
- Email
- In-app

후보:
- SMS
- Kakao
- Push

채널 구현은 `MessagingProvider` adapter를 사용.

---

## 3. Notification Entity

```text
Notification
- user/contact
- type
- template_version
- locale
- channel
- scheduled_at
- sent_at
- delivery_status
- provider_message_id
```

---

## 4. 중요 Template

Commerce:
- payment_completed
- asset_required
- proof_ready
- revision_ready
- production_started
- shipped
- delivered
- refund_completed

Group:
- invitation
- goal_reached
- deadline_72h
- deadline_24h
- missing_asset
- cancelled

Account:
- verify_email
- password_reset
- gift_claim

Product:
- weekly_mirror_ready

---

## 5. Retry

- retryable provider error
- permanent failure
- bounce
- invalid contact

거래 알림 실패는 Admin queue에 표시.

---

## 6. Preference

사용자 설정:
- product reminder
- marketing email
- marketing SMS

결제/보안 등 필수 거래 알림은 opt-out 대상과 구분한다.

---

## 7. Quiet Hours

Product/Marketing reminder는 사용자 timezone을 반영.
Transactional은 즉시 전송할 수 있다.

---

## 8. Localization

Template은:
`type + locale + version`

조합으로 관리.

---

## 9. Audit

중요 거래 알림은:
- template
- destination masked
- send result
를 추적한다.
