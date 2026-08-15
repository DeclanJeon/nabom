---
doc_id: SYS-ARCH-001
title: NABOM System Architecture
version: 1.0
status: APPROVED_BASELINE
updated_at: 2026-08-11
---

# NABOM System Architecture v1.0

## 1. 목적

나봄의 제품·커머스·NFC·페이지·성장서비스·외부 판매채널을 하나의 시스템으로 연결하는 기준 아키텍처다.

이 문서는 기술 구현의 **상위 SSOT**다.

---

## 2. Logical Architecture

```text
                    ┌──────────────────────────────┐
                    │      Sales Channels          │
                    │ SmartStore / idus / Etsy     │
                    │ Pinkoi / B2B / NABOM Direct  │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────┐
│                    NABOM Web Platform                   │
│                                                        │
│ Storefront / My / Customize / Group Buy / Page Builder │
│ Living Profile / Today / Mirror / Journey              │
│ Relationships / Insight Groups / Gift Pages            │
└───────────────┬──────────────────┬──────────────────────┘
                │                  │
                ▼                  ▼
        ┌───────────────┐   ┌──────────────────┐
        │ Commerce API  │   │ Living Self API  │
        └───────┬───────┘   └─────────┬────────┘
                │                     │
                ├──────────┬──────────┤
                ▼          ▼          ▼
          PostgreSQL     Redis      Object Storage
                │          │          │
                │          ▼          │
                │       Workers       │
                │          │          │
                └──────────┼──────────┘
                           │
          ┌────────────────┼─────────────────┐
          ▼                ▼                 ▼
      PG/Payments      AI Providers     Messaging
          │                                  │
          ▼                                  ▼
     Settlement                        Email/SMS/etc.
```

### Living Engine Service Boundary

`Living Self API`는 계산 엔진을 직접 내장하지 않고 private engine API client를 통해 호출한다.

```text
Living Self API
   ├─→ Saju Engine API      (private :8001)
   └─→ I Ching Engine API   (private :8002)
```

- Saju Engine은 출생 정규화·만세력·궁합 근거·캐릭터 매핑을 소유한다.
- I Ching Engine은 괘/효 계산·dataset provenance·record reflection resolver를 소유한다.
- 계정, Evidence 원문, InsightConsent, ProfileVersion, RelationshipMirror 저장은 NABOM API가 소유한다.
- 엔진은 public ingress를 갖지 않으며 service token, request ID, contract version으로 호출한다.
- 엔진 raw 결과는 API Facade가 canonical user-facing schema로 변환하기 전 외부에 노출하지 않는다.

---

## 3. 권장 배포 단위

초기에는 과도한 Microservice 분리를 하지 않는다.

### nabom-web
- Next.js
- Storefront
- My
- Customize
- Group Buy
- Page Builder
- Living UI
- Admin은 초기 동일 코드베이스의 보호된 영역 가능

### nabom-api
초기에는 Next.js Route Handler 또는 Node API로 시작 가능.

책임:
- Commerce
- Orders
- Payments
- NFC Resolver
- Page
- Group Buy
- Living Profile API
- Relationship / InsightGroup API
- Consent and insight access policy
- Saju Engine API client
- I Ching Engine API client

### nabom-worker
비동기:
- image processing
- AI
- Weekly Mirror
- notifications
- marketplace sync
- settlements
- export
- cleanup

### PostgreSQL
SSOT transactional DB.

### Redis
- queue
- distributed lock
- short-lived cache
- rate limit

### Object Storage
- private uploads
- generated assets
- production assets
- page media

---

## 4. Trust Boundary

### Public
- Storefront
- Public/Unlisted Page
- NFC/QR Resolver

### Authenticated Customer
- Order
- Page Editor
- Profile
- Journal
- Group dashboard

### Operator
- Design/Production
- Support

### Privileged
- Finance
- Sensitive Data
- Security/Admin

권한을 UI가 아니라 API에서 강제한다.

---

## 5. Database Strategy

초기 단일 PostgreSQL을 사용해도 된다.

단 Schema/Module 경계를 유지한다.

```text
identity
commerce
payments
customization
fulfillment
nfc
pages
groupbuy
living
subscriptions
support
finance
audit
```

민감한 Journal/Birth data는 권한과 조회경로를 강하게 분리한다.

---

## 6. Async Architecture

동기 요청에서 오래 걸리는 작업을 수행하지 않는다.

Async 대상:
- AI generation
- image processing
- print asset
- notification
- marketplace sync
- settlement reconciliation
- export
- page media optimization

Job:
- idempotency
- retry
- DLQ
- observable

---

## 7. External Integration

모든 외부 시스템은 Adapter 경계를 가진다.

```text
PaymentProvider
SalesChannel
ShippingCarrier
MessagingProvider
AIProvider
StorageProvider
```

Business Logic이 특정 공급자 SDK에 직접 종속되지 않게 한다.

---

## 8. Data Ownership

각 데이터의 canonical owner는 `37_Canonical_Domain_Registry.md`를 따른다.

다른 문서에 같은 Entity 정의가 있으면 Registry가 우선한다.

---

## 9. State Ownership

상태는 `38_Canonical_State_Machines.md`가 우선한다.

단일 `OrderStatus` 하나에 결제·제작·배송·디지털 상태를 섞지 않는다.

---

## 10. Route Ownership

공개 URL/API 경로는 `39_Canonical_Routes_URLs.md`가 우선한다.

---

## 11. Environments

```text
local
staging
production
```

권장:
- Production DB와 staging 완전 분리
- 실제 PG production key를 staging에 사용 금지
- Test NFC token namespace 분리
- Test emails prefix 또는 sink

---

## 12. Feature Flags

기능 출시는 코드 deploy와 분리한다.

Flag 예:
- direct_checkout
- group_buy
- page_builder
- subscription
- japan_storefront
- etsy_sync

Flag 변경은 Admin audit 또는 배포 config에 기록.

---

## 13. Baseline

v1.0에서 이 아키텍처는 **출시 기준선**이며,
서비스 규모가 커지기 전까지 불필요한 분산시스템화를 하지 않는다.
