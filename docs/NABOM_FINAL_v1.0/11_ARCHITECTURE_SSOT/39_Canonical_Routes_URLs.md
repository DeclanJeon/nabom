---
doc_id: SYS-ROUTE-001
title: NABOM Canonical Routes and URLs
version: 1.0
status: SSOT
updated_at: 2026-08-11
---

# Canonical Routes / URLs v1.0

## 1. Domain

Production:
`https://nabom.ponslink.com`

---

## 2. Storefront

```text
/
/shop
/shop/[category]
/products/[slug]
/cart
/checkout
/orders/[orderNo]
```

---

## 3. Customization

```text
/customize/[orderItemId]
/proofs/[proofId]
```

---

## 4. Group Buy

Canonical:
```text
/group-buy
/group-buy/create
/group-buy/[slug]
/group-buy/[slug]/join
```

Short marketing alias:
```text
/g/[slug] → 302/307 redirect → /group-buy/[slug]
```

따라서 기존 문서의 `/g/{slug}`는 **별도 canonical route가 아니라 short alias**다.

---

## 5. Page

```text
/p/[slug]
/pages/new
/pages/[pageId]/edit
```

---

## 6. NFC / QR Resolver

NFC:
```text
/k/[token]
```

QR:
```text
/q/[token]
```

둘 다 같은 Resolver service를 사용하되 source를 구분해 analytics한다.

민감 기능 인증수단으로 사용하지 않는다.

---

## 7. Living Service

```text
/today
/profile
/mirror
/journey
/settings
/relationships
/relationships/[relationshipId]
/groups
/groups/[groupId]
/groups/[groupId]/mirror
```

---

## 8. My

```text
/my
/my/orders
/my/pages
/my/nfc
/my/group-buys
/my/subscription
/my/reviews
```

---

## 9. Admin

```text
/admin
/admin/orders
/admin/production
/admin/proofs
/admin/group-buys
/admin/pages
/admin/nfc
/admin/shipping
/admin/inventory
/admin/finance
/admin/support
/admin/customers
/admin/settings
```

---

## 10. Localization

기본 한국어:
prefix 없음.

향후:
```text
/ja/...
/en/...
```

단 Resolver URL `/k`, `/q`는 locale-neutral.

Resolver는 page/account preference와 request language를 바탕으로 목적지 locale을 결정한다.

---

## 11. API

Public/Customer:
```text
/api/...
```

External webhook:
```text
/api/webhooks/[provider]
```

Admin:
```text
/api/admin/...
```

Integration:
```text
/api/integrations/...
```

Internal engine routes are not public customer routes:

```text
POST /internal/v1/charts
POST /internal/v1/compatibility
POST /internal/v1/readings/cast
POST /internal/v1/reflections
GET  /healthz
GET  /readyz
```

The engine routes are private network endpoints owned by `saju-engine` and `iching-engine`. Browser and external clients MUST use the NABOM Facade routes:

```text
POST /api/v1/living/profiles/initial
POST /api/v1/living/reflections
POST /api/v1/relationships/[relationshipId]/mirror
POST /api/v1/insight-groups/[groupId]/profile
```

Living relationship API:

```text
/api/relationships
/api/relationships/[relationshipId]/consent
/api/relationships/[relationshipId]/mirror
/api/insight-groups
/api/insight-groups/[groupId]/members
/api/insight-groups/[groupId]/profile
/api/insight-groups/[groupId]/relationship-insights
```

관계·그룹 API는 동의된 공개 범위만 반환하며 raw journal, birth input, 비공개 Evidence를 기본 응답에 포함하지 않는다.

---

## 12. URL 보안

- internal integer ID 공개 금지 권장
- public token은 opaque random
- unlisted page slug는 충분한 entropy
- private pages noindex
- enumeration rate limit
