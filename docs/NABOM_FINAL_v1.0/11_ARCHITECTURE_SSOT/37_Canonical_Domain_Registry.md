---
doc_id: SYS-DOMAIN-001
title: NABOM Canonical Domain Registry
version: 1.0
status: SSOT
updated_at: 2026-08-11
---

# Canonical Domain Registry v1.0

## 목적

여러 설계문서에 Entity가 흩어져 생기는 충돌을 막는다.

**Entity 이름, 소유 도메인, 주요 책임은 이 문서가 우선한다.**

| Domain | Canonical Entities | 책임 |
|---|---|---|
| Identity | User, Identity, Session, Address | 계정/인증 |
| Catalog | Product, ProductVariant, Category, CustomizationSchema, ChannelListing | 상품 |
| Cart | Cart, CartItem | 장바구니 |
| Order | Order, OrderItem, OrderPriceSnapshot | 주문 원장 |
| Payment | PaymentIntent, PaymentTransaction, Refund, Chargeback | 결제 |
| Finance | PGSettlement, ChannelSettlement, Reconciliation | 정산 |
| Customization | Customization, DesignProof, ProductionAsset | 개인화/시안 |
| Procurement | Material, BOM, Supplier, PurchaseOrder, InventoryTransaction | 자재/발주 |
| Fulfillment | ProductionBatch, Shipment, ShipmentItem | 생산/배송 |
| NFC | NFCTag, LinkToken, LinkDestination, TapEvent | NFC/QR |
| Pages | DigitalPage, PageRevision, PageBlock, PageOwnership | 맞춤 페이지 |
| GroupBuy | GroupBuyCampaign, GroupParticipant, GroupOrderPolicy | 공동구매 |
| Gift | GiftClaim, OwnershipTransfer | 선물 Claim |
| Subscription | Plan, Subscription, Entitlement, EntitlementUsage | 구독/권한 |
| Living | ProfileVersion, TraitState, CharacterProfile, Evidence, DailyEntry, PatternHypothesis, CanonicalReflection, WeeklyMirror, GrowthExperiment, Relationship, RelationshipEvidence, RelationshipMirror, ContributionInsight, SharedGrowthArea, InsightGroup, GroupMembership, GroupProfile, GroupRelationshipInsight, InsightConsent | 자기·관계·그룹 성장 서비스 |
| Promotion | Promotion, Coupon, CouponRedemption | 프로모션 |
| Reviews | Review, ReviewMedia, MarketingReuseConsent | 리뷰 |
| Support | SupportTicket, Claim, ReprintCase | CS/클레임 |
| B2B | Organization, Lead, Quote, ContractReference | 기업영업 |
| Compliance | ConsentRecord, PolicyVersion, DataRetentionRule | 동의/정책 |
| Moderation | Report, ModerationCase | UGC |
| Analytics | AnalyticsEvent, Experiment, Attribution | 분석 |
| Audit | AuditEvent | 운영 감사 |
| Engine Integration | EngineRequest, EngineResultReference, EngineHealthSnapshot | private 사주·주역 엔진 호출 추적과 버전/provenance |

---

## Order 원칙

`Order`는 모든 상태를 저장하는 거대한 객체가 아니다.

Order는:
- buyer
- currency
- totals
- channel
- line items
- high-level lifecycle

을 가진다.

결제/제작/배송 상태는 각각 소유 도메인의 상태를 참조한다.

---

## Product 원칙

Product:
마케팅/판매 개념.

ProductVariant:
실제 SKU/옵션 조합.

CustomizationSchema:
해당 상품이 어떤 개인화 입력을 요구하는지 정의.

BOM:
물리 제작 자재를 정의.

이 네 가지를 혼합하지 않는다.

---

## NFC 원칙

`NFCTag` = 물리 태그.
`LinkToken` = 공개 opaque resolver token.
`LinkDestination` = 현재 목적지.

NFC를 다시 쓰지 않고 Destination을 변경할 수 있다.

---

## Page 원칙

Page 내용은 versioning한다.

`DigitalPage` = identity/settings
`PageRevision` = publish 가능한 revision
`PageBlock` = revision 내 block

---

## Money 원칙

- OrderPriceSnapshot: 고객 계약 가격
- PaymentTransaction: 실제 결제
- Settlement: 실제 정산
- Accounting Export: 회계 입력

서로 같은 값이라고 가정하지 않는다.

---

## Living 원칙

Commerce purchase와 Living Profile은 직접 동일 Entity가 아니다.

상품 구매는 `Entitlement`를 발급하고,
Living 모듈이 entitlement를 확인한다.

### Relationship / InsightGroup 원칙

- `Relationship`는 두 사용자 사이의 분석 관계이며 `GroupBuy`와 소유권을 공유하지 않는다.
- `InsightGroup`은 공동 목표·기록·관계 분석을 위한 사람 집합이다. 주문·결제·제작은 `GroupBuy`가 소유한다.
- 관계 분석은 양쪽 `InsightConsent`가 승인한 공개 범위만 읽는다.
- 그룹 분석은 최소 5명 이상에서만 개인 역산이 불가능한 집계 결과를 생성한다.
- `RelationshipMirror`와 `GroupRelationshipInsight`는 가설·근거·confidence를 보존하며 운명이나 확정 진단이 아니다.
- 동의 철회는 새 분석 생성을 중단하고 기존 결과를 suspended 처리한다.
