---
doc_id: LEGACY-562A9DAA6E
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 07_FINANCE_PAYMENTS_TAX/23_Subscription_Entitlement_Billing.md
---

# NABOM Subscription / Entitlement / Recurring Billing 설계 v1.0

## 1. 원칙

결제상품과 권한을 분리한다.

`Plan → Subscription → Billing → Entitlement`

물리 상품이 제공하는 21일 패스도 Subscription과 별개 Entitlement로 표현한다.

---

## 2. Plan

예:
- FREE
- GROWTH_MONTHLY
- GROWTH_ANNUAL

Plan은 기능 목록을 직접 hard-code하지 않고 Entitlement template를 가진다.

---

## 3. Subscription 상태

```text
TRIALING
ACTIVE
PAST_DUE
GRACE
CANCEL_AT_PERIOD_END
CANCELLED
EXPIRED
PAUSED
```

---

## 4. Billing Lifecycle

```text
Renewal Due
→ Charge Attempt
→ Success
   → Entitlement Extend

→ Fail
   → Retry
   → Grace Period
   → Final Fail
   → Expire/Pause
```

재시도 횟수와 grace 기간은 PG 기능/사업정책에 맞춰 설정.

---

## 5. Entitlement

예:
- weekly_mirror
- monthly_mirror
- living_profile_history
- page_storage_gb
- custom_page_blocks
- weekly_mirror_credit

필드:
- source_type
- source_id
- starts_at
- expires_at
- usage_limit
- usage_count

---

## 6. 취소

사용자에게:
- 즉시 취소
- 다음 결제일부터 취소

정책에 따라 하나 또는 둘 다 지원.

취소해도 이미 구매한 물리 상품의 NFC/기본 페이지 자체가 즉시 사라지면 안 된다.

---

## 7. 결제 실패 UX

- 앱 배너
- 이메일
- 결제수단 변경
- 재시도 예정일
- grace 종료일

민감한 일기 데이터는 구독 만료 후에도 즉시 삭제하지 않는다.

읽기전용/기본기능 정책을 별도로 둔다.

---

## 8. 상품 Bundle

예:
Duo Charm 구매:
- basic_page_permanent
- growth_pass_21d
- weekly_mirror_credit: 3

Gift Set:
- gift_page
- recipient_claim

권한은 OrderItem fulfillment와 연결해 발급한다.

---

## 9. Admin

- active subscriptions
- past due
- grace
- failed payment
- cancelled
- entitlement override
- manual grant/revoke

수동 grant는 audit log 필수.
