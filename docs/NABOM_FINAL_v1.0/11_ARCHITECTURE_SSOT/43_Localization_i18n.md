---
doc_id: PLATFORM-I18N-001
title: NABOM Localization and Internationalization
version: 1.0
status: APPROVED_BASELINE
updated_at: 2026-08-11
---

# Localization / i18n 설계 v1.0

## 1. 지원 순서

1. ko-KR
2. ja-JP
3. en
4. zh-TW 후보

---

## 2. 분리할 것

- UI translation
- Product content
- Legal documents
- Email templates
- Currency
- Date/time
- Shipping text
- Customer support macros

---

## 3. Locale

User:
preferred_locale.

Page:
content_locale.

Order:
checkout_locale snapshot.

---

## 4. Currency

Locale과 Currency는 같은 개념이 아니다.

예:
영문 UI + JPY 결제 가능.

---

## 5. Timezone

- 주문/결제: UTC 저장 + display timezone
- Living journal: 사용자 timezone 중요
- Group deadline: Campaign timezone 명시
- Notifications: recipient timezone

---

## 6. Translation Workflow

Product/legal copy:
- source locale
- translation
- review
- published version

법적 문구는 기계번역만으로 확정하지 않는다.

---

## 7. URLs

기본 ko:
prefix 없음.

ja/en:
`/ja`, `/en`.

Canonical/hreflang은 SEO 문서와 연결.

---

## 8. User-generated Page

페이지 작성 언어는 사용자 선택.
자동 번역은 Phase 2이며 원문을 보존한다.

---

## 9. Admin

원문과 번역 상태:
- MISSING
- MACHINE_DRAFT
- REVIEWED
- PUBLISHED
