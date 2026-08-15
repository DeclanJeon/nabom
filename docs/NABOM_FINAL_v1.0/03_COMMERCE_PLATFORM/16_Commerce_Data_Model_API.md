---
doc_id: LEGACY-D9121E2C3F
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 03_COMMERCE_PLATFORM/16_Commerce_Data_Model_API.md
---

# NABOM Commerce Data Model / API 설계 v1.0

## 1. 도메인 경계

```text
Identity
Catalog
Pricing
Cart
Checkout
Payment
Order
Customization
Proof
Fulfillment
Shipping
PageBuilder
NFC
GroupBuy
Promotion
Review
Support
Subscription
Analytics
Admin
```

---

# 2. 주요 Entity

## Product
```text
id
type
slug
status
base_price
currency
customizable
digital
```

## ProductVariant
```text
product_id
sku
option_values
price_delta
cost
stock_policy
```

## CustomizationSchema
상품별 입력필드 정의.

```text
photo_front
photo_back
nickname
message
theme
```

## Cart
CartItem은 일반 SKU + customization draft를 가진다.

## Order
결제/배송 기준 부모.

## OrderItem
각 상품.

## Customization
OrderItem별 제작자료.

## DesignProof
시안/수정/승인.

## DigitalPage
페이지 메타.

## PageBlock
순서 기반 block.

## LinkToken
NFC/QR resolver.

## NFCTag
실제 물리 tag.

## GroupBuyCampaign
공동구매.

## GroupParticipant
참가자.

## Shipment
복수 shipment 지원.

## Payment
결제 attempt/history.

## Refund
부분환불.

## Promotion
쿠폰/코드.

## Review
구매검증.

---

# 3. 권장 DB 관계

```text
User
 ├─ Order
 │   └─ OrderItem
 │       ├─ Customization
 │       ├─ DesignProof
 │       └─ DigitalEntitlement
 ├─ DigitalPage
 ├─ LinkToken
 └─ GroupBuyCampaign

GroupBuyCampaign
 └─ GroupParticipant
     └─ Order / OrderItem

NFCTag
 └─ LinkToken
     └─ Destination
```

---

# 4. Resolver

NFC와 QR의 핵심.

`GET /api/resolve/{token}`

처리:
1. token 존재
2. active 확인
3. tap event
4. destination 조회
5. authorization mode 확인
6. redirect

token에 page ID/user ID를 직접 노출하지 않는다.

---

# 5. 주요 API

## Catalog
```text
GET /api/products
GET /api/products/:slug
GET /api/categories
```

## Cart
```text
POST /api/cart/items
PATCH /api/cart/items/:id
DELETE /api/cart/items/:id
```

## Upload
```text
POST /api/uploads/presign
```

## Checkout
```text
POST /api/checkout
POST /api/payments/confirm
POST /api/payments/webhook
```

## Orders
```text
GET /api/orders
GET /api/orders/:id
POST /api/orders/:id/cancel
```

## Customization
```text
PUT /api/order-items/:id/customization
POST /api/order-items/:id/submit-assets
```

## Proof
```text
GET /api/proofs/:id
POST /api/proofs/:id/approve
POST /api/proofs/:id/revision
```

## Page Builder
```text
POST /api/pages
GET /api/pages/:id
PATCH /api/pages/:id
POST /api/pages/:id/publish
```

## NFC
```text
POST /api/nfc/tokens
PATCH /api/nfc/tokens/:id/destination
POST /api/nfc/tokens/:id/revoke
```

## Group Buy
```text
POST /api/group-buys
GET /api/group-buys/:slug
POST /api/group-buys/:id/join
PATCH /api/group-buys/:id
POST /api/group-buys/:id/close
```

---

# 6. Event Model

중요 이벤트:

```text
product_viewed
cart_item_added
checkout_started
payment_completed
customization_submitted
proof_ready
proof_approved
production_started
order_shipped
nfc_activated
nfc_tapped
page_published
group_created
group_joined
group_goal_reached
```

Event table 또는 analytics pipeline에 보낸다.

---

# 7. 기술구성 권장

사용자 기술스택을 기준으로:

### Front
- Next.js App Router
- TypeScript
- Tailwind
- React Hook Form + Zod 후보

### API
초기에는 Next.js Route Handler 또는 별도 Node API.
주문/PG webhook이 커지면 별도 API 서비스 분리.

### DB
PostgreSQL.

### Queue
Redis + BullMQ 계열 후보.

필요:
- image jobs
- AI jobs
- mail
- group reminders
- order state sync

### Storage
S3-compatible object storage.

### Image
원본과 production asset 분리.

### Admin
같은 monorepo의 `/admin` 또는 `nabom-admin`.

---

# 8. Idempotency

필수:
- PG webhook
- order creation
- refund
- NFC provisioning
- group finalize

중복 호출로 주문/토큰이 두 개 생기면 안 된다.

---

# 9. Audit

추적이 필요한 것:
- 가격 변경
- 주문 상태
- 관리자 refund
- 디자인 승인
- NFC destination 변경
- token revoke
- 개인정보 관리자 접근


---

# 10. Sales Channel Domain v1.0

## SalesChannel

```json
{
  "code": "NAVER_SMARTSTORE",
  "type": "MARKETPLACE",
  "country": "KR",
  "active": true
}
```

## ChannelListing

```json
{
  "channel": "NAVER_SMARTSTORE",
  "external_listing_id": "123",
  "product_id": "prod_nabom_duo",
  "currency": "KRW",
  "channel_price": 29900,
  "status": "ACTIVE"
}
```

## ExternalOrderLink

```json
{
  "order_id": "ord_internal",
  "channel": "NAVER_SMARTSTORE",
  "external_order_id": "external",
  "import_mode": "API",
  "imported_at": "..."
}
```

## ChannelSettlement

```json
{
  "channel": "ETSY",
  "external_order_id": "...",
  "gross": 0,
  "platform_fee": 0,
  "payment_fee": 0,
  "ad_fee": 0,
  "refund": 0,
  "net_payout": 0,
  "currency": "USD"
}
```

## CountryLaunchConfig

```json
{
  "country": "JP",
  "enabled": false,
  "locale": "ja-JP",
  "currency": "JPY",
  "direct_checkout": false,
  "marketplace_channels": ["ETSY"],
  "shipping_profile_id": "ship_jp_01"
}
```

## Channel API

```text
POST /api/admin/channel-orders/manual-import
POST /api/integrations/naver/orders/sync
POST /api/integrations/naver/settlements/sync
GET  /api/admin/channels/orders
GET  /api/admin/channels/settlements
```

외부 플랫폼 정책상 API/자동화가 제공되지 않거나 초기 규모가 작으면 manual import를 허용한다.


---

# v1.0 Domain Registry Notice

이 문서의 Entity 목록은 초기 Commerce 중심 목록이다.

v1.0 전체 도메인 Entity ownership은
`11_ARCHITECTURE_SSOT/37_Canonical_Domain_Registry.md`가 SSOT다.

구현 ERD 작성 시 Registry의 모든 P0 domain을 포함한다.
