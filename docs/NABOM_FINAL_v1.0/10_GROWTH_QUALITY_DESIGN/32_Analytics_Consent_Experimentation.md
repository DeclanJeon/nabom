---
doc_id: LEGACY-9E0941A2C0
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 10_GROWTH_QUALITY_DESIGN/32_Analytics_Consent_Experimentation.md
---

# NABOM Analytics / Attribution / Experimentation 설계 v1.0

## 1. 원칙

Commerce analytics와 Living Profile 민감 이벤트를 분리한다.

광고 플랫폼에:
- 일기 내용
- 감정
- 사주/성향
- 관계
를 전송하지 않는다.

---

## 2. Commerce Event

- product_view
- add_to_cart
- checkout_start
- purchase
- coupon_apply
- proof_approve
- shipment
- nfc_first_tap
- page_publish

---

## 3. Product Event

- profile_created
- daily_entry_created
- weekly_mirror_opened
- experiment_accepted

광고 attribution 데이터와 분리 저장.

---

## 4. Attribution

- UTM
- referrer
- channel
- campaign
- first_touch
- last_touch

Marketplace 주문은 external channel source로 기록.

---

## 5. Marketing Consent

광고성 cookie/pixel 사용 시:
- 필요한 고지
- consent strategy
- opt-out
를 실제 국가/도구에 맞춰 구현.

---

## 6. Experiment

A/B test 예:
- 가격
- landing hero
- 상품명
- onboarding
- page template

실험:
- hypothesis
- audience
- metric
- guardrail
- start/end
- result

---

## 7. Guardrail

conversion만 최적화하지 않는다.

함께:
- refund
- revision
- CS
- retention
- privacy complaint
를 본다.

---

## 8. Dashboard

### Acquisition
### Commerce Funnel
### Production
### Product Activation
### Retention
### Unit Economics
