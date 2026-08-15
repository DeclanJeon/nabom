---
doc_id: COMMERCE-CATALOG-001
title: NABOM Catalog CMS and Merchandising
version: 1.0
status: APPROVED_BASELINE
updated_at: 2026-08-11
---

# Catalog / CMS / Merchandising 설계 v1.0

## 1. Product Lifecycle

```text
DRAFT
→ REVIEW
→ ACTIVE
→ PAUSED
→ ARCHIVED
```

상품 삭제보다 Archive를 우선.

---

## 2. Product Content

- name
- slug
- short description
- description
- media
- category
- tags
- use case
- customization schema
- production lead time
- refund/custom notice
- SEO

---

## 3. Variant

- SKU
- option combination
- price
- cost
- availability
- BOM
- channel mapping

---

## 4. Publishing

변경 시:
- draft
- preview
- publish

가격/정책 변경은 audit.

---

## 5. Sales Channel Listing

상품은 Channel마다:
- title
- description
- price
- images
- external ID
- status

가 다를 수 있다.

내부 Product와 외부 Listing을 분리한다.

---

## 6. Merchandising

- featured
- new
- gift
- group
- country availability
- campaign collection

---

## 7. Lead Time

상품별:
- proof lead time
- production lead time
- current capacity adjustment

예상 출고일 계산에 사용.

---

## 8. CMS

브랜드/도움말:
- landing section
- FAQ
- guide
- notice
- policy link

초기에는 DB 기반 간단 CMS 또는 repo content 둘 중 하나로 시작 가능.

---

## 9. Search

FIRST 100에는 DB 검색으로 충분.

검색대상:
- product name
- category
- tags
- use case

전문 검색엔진은 필요 시 후속.
