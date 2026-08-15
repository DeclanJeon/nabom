---
doc_id: LEGACY-A4F7C61B10
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 06_OPERATIONS_QA_RELEASE/18_Full_QA_Gap_Analysis.md
---

# NABOM Full QA / Gap Analysis v1.0

기준일: 2026-08-11
검토범위:
- Product / Living Self Engine
- Commerce
- Custom Manufacturing
- Group Buy
- NFC / QR
- Digital Page Builder
- Payments
- Shipping
- Privacy / Security
- Domestic / Global Operations
- Marketing / Sales
- Admin / Analytics

## 0. 결론

현재 v0.5는 **제품 방향과 핵심 사용자 플로우는 충분히 설계되어 있으나, 상용 출시 문서로는 아직 P0 운영 레이어가 비어 있다.**

가장 큰 누락은 아래 10개다.

1. 세무·회계·PG 정산
2. 결제 실패/차지백/환불 reconciliation
3. 공동구매 목표미달/주최자취소/참가자취소의 돈 흐름
4. 이미지·초상·저작권·금지 콘텐츠 정책
5. 보안 하드닝 + 백업 + 장애복구
6. 배송 예외/반송/분실/재배송
7. 재고/BOM/발주/공급처 관리
8. 약관·개인정보·마케팅 동의의 버전/증적 관리
9. 디지털 페이지 abuse / 신고 / takedown
10. 해외 세금·관세·통관·제품안전 국가별 launch gate

즉, 기능을 더 많이 넣어야 하는 단계가 아니라 **운영과 리스크 제어를 제품 기능으로 내려야 하는 단계**다.

---

# 1. P0 Launch Blockers

## P0-01. 세무 / 회계 / 매출 정산

현재 문서에는 주문과 결제는 있으나 다음이 없다.

- PG 정산내역 ↔ 주문 ↔ 환불 대사
- 카드/계좌/간편결제 매출 집계
- 배송비 매출/비용 구분
- 쿠폰 할인 부담주체
- 부분환불
- 플랫폼 판매 매출
- 해외매출
- 현금영수증
- 세금계산서/사업자 고객 증빙
- 부가세 처리용 export
- 회계 시스템 또는 월별 정산 리포트

### Required

`Settlement` 도메인을 추가한다.

```text
Order
→ Payment
→ PG Settlement
→ Refund
→ Fee
→ Net Settlement
→ Accounting Export
```

Admin:
- 일 매출
- 결제수단별 매출
- 환불
- PG fee
- 플랫폼 fee
- 배송비
- 월 정산
- 미대사 transaction

B2B:
- 견적서
- 거래명세
- 세금계산서 요청정보
를 별도 workflow로 둔다.

---

## P0-02. 결제 장애 / Fraud / Chargeback

현재 webhook과 idempotency 언급은 있으나 실제 운영상태가 부족하다.

필요 상태:

```text
PAYMENT_PENDING
AUTHORIZED
CAPTURED
FAILED
CANCEL_REQUESTED
CANCELLED
PARTIAL_REFUNDED
REFUNDED
CHARGEBACK_OPEN
CHARGEBACK_WON
CHARGEBACK_LOST
```

필수:
- webhook signature 검증
- duplicate webhook
- timeout 후 고객은 실패 화면인데 결제는 성공한 경우
- 결제 성공 후 주문생성 실패
- refund API 실패
- 부분취소
- PG dashboard와 DB reconciliation
- 고액/반복 실패 주문 review
- 카드 도난/chargeback 대응 증빙

---

## P0-03. 공동구매 Money State Machine

현재 공동구매 UX는 좋지만 **돈의 lifecycle**이 약하다.

반드시 결정:

### 목표 미달
- 자동 환불?
- 주최자 진행 선택?
- 언제 확정?
- 환불 수수료 누가 부담?

### 참가자 취소
- 목표 달성 전?
- 목표 달성 후?
- 디자인 승인 후?

### 주최자 취소
- 참가자 전원 자동환불
- 쿠폰/포인트 복원
- 결제수단 원복

### 목표 달성 직전
참가자 10명 중 1명이 취소해 9명이 되면?

### 생산 Lock
`PRODUCTION_LOCKED` 이후 수량 변경 금지 기준.

MVP 권장:
- **고정단가**
- **최소 인원**
- 목표 미달 시 자동환불
- 생산 Lock 전까지 참가자 취소 가능
- 생산 Lock 이후 커스텀 상품 정책 적용

단계할인/예약금/분담결제는 Phase 2.

---

## P0-04. 주문/약관/동의 Evidence Ledger

현재 “동의를 받는다”는 있지만 증적 구조가 없다.

필요:

```text
ConsentRecord
- user_id/order_id
- consent_type
- policy_version
- text_hash
- agreed_at
- ip
- user_agent
```

종류:
- 이용약관
- 개인정보
- 커스텀 제작 동의
- 청약철회 제한 고지
- 디지털콘텐츠 제공 개시 동의
- 마케팅 수신
- 연구 데이터 opt-in
- 해외이전 고지/동의가 필요한 경우

약관 문구가 바뀌어도 과거 주문에 당시 무엇을 동의했는지 재현 가능해야 한다.

---

## P0-05. 사용자 업로드 저작권 / 초상권

나봄은 사진을 받기 때문에 반드시 필요.

주문자 확인:
- 업로드 자료를 사용할 권리가 있음을 보증
- 타인의 초상/저작권을 침해하지 않음
- 제작을 위해 필요한 범위에서 처리 허용

별도 정책:
- 유명 캐릭터 무단 굿즈
- 연예인 사진
- 타인의 개인정보
- 도용 이미지
- 불법/유해 콘텐츠
- 음란물
- 증오/폭력적 콘텐츠
- 사칭 페이지

운영자:
- 신고
- 제작거부
- 페이지 비공개
- takedown
- 이의제기
workflow 필요.

---

## P0-06. Page Builder Abuse / Phishing

NFC/QR 페이지는 링크 서비스이므로 공격표면이 크다.

필요:
- 외부 URL allow/deny 검사
- 악성 URL 검사
- javascript/embed 금지
- 사용자 custom HTML 금지(MVP)
- 신고 버튼
- abuse admin queue
- phishing page suspend
- token suspend
- repeat offender block

페이지 status:
`PUBLISHED → REPORTED → UNDER_REVIEW → SUSPENDED / RESTORED`

---

## P0-07. 업로드 보안

현재 사진 upload는 있으나 pipeline이 없다.

Required:
- signed upload
- MIME sniffing
- 확장자만 신뢰 금지
- 최대 용량
- pixel/dimension limit
- 악성 파일 검사
- SVG 정책
- EXIF metadata 제거
- 원본 private bucket
- public derivative 분리
- signed URL expiry
- image processing sandbox
- upload rate limit

특히 사진의 GPS EXIF가 남지 않도록 처리한다.

---

## P0-08. 인증 / 관리자 보안

추가 필요:
- 이메일 인증
- 비밀번호 재설정
- 세션 revoke
- social account collision
- admin 2FA/MFA
- admin RBAC
- production admin allowlist 검토
- 민감정보 접근 audit
- 비정상 로그인 감지

웹 보안:
- CSRF
- XSS
- CSP
- secure cookies
- SameSite
- brute-force rate limit
- secrets rotation

---

## P0-09. Backup / Disaster Recovery / Incident Response

현재 encryption/audit은 있지만 복구 설계가 없다.

정의:
- DB backup
- object storage versioning/backup
- restore test
- RPO
- RTO
- incident severity
- on-call owner
- 고객 공지 기준
- 개인정보 유출 대응
- postmortem

MVP 예시 목표:
- DB point-in-time recovery 지원
- 일 1회 이상 backup
- 분기/월 단위 restore drill
- 파일 원본 삭제/복구 정책 명확화

정확한 RPO/RTO 수치는 인프라 비용에 맞춰 확정.

---

## P0-10. 배송 예외 상태

현재 `SHIPPED/DELIVERED`만으로 부족.

필요:
- ADDRESS_INVALID
- LABEL_CREATED
- PICKED_UP
- IN_TRANSIT
- DELIVERY_FAILED
- LOST
- RETURN_TO_SENDER
- RETURN_RECEIVED
- RESHIPMENT
- PARTIAL_SHIPPED

정책:
- 고객 주소오류
- 택배사 분실
- 제작자 오배송
- 해외 미수령
- 반송 국제배송비
- 재배송비 부담주체

---

## P0-11. 재고 / BOM / 발주

나봄은 주문제작이지만 **재고가 없는 사업이 아니다.**

재고:
- NFC chip/tag
- Portal blank
- 아크릴 hardware
- ring
- package
- card
- envelope
- replacement parts

Entity:
- Material
- BOM
- InventoryLocation
- InventoryTransaction
- PurchaseOrder
- Supplier
- SupplierQuote

필요:
- 안전재고
- reorder point
- 입고
- 불량
- 폐기
- 생산사용
- 재고조정

---

## P0-12. 생산 Batch / Traceability / Recall

품질 문제가 생겼을 때 “어느 주문이 어느 부품/공급처와 연결되었는지” 알아야 한다.

필드:
- supplier
- purchase_order
- batch/lot
- production_date
- QC inspector
- NFC lot

리콜 기능:
- 해당 batch 주문 검색
- 고객 알림
- replacement
- 비용 집계

---

## P0-13. 디지털콘텐츠 / 페이지 환불 정책

Physical + Digital bundle은 환불이 복잡하다.

예:
- 키링 제작 전인데 Page는 이미 publish
- Profile 001 사용 시작
- Weekly Mirror 1회 사용
- 커스텀 페이지 제작 완료
- 물리제품 불량

Entitlement마다:
- delivered_at
- consumed_at
- refundable status
를 둔다.

Bundle refund 계산 규칙이 필요하다.

---

## P0-14. Subscription Lifecycle

현재 정기결제 개념만 있다.

필요:
- trial
- first charge
- renewal
- payment failed
- grace period
- retry/dunning
- cancellation
- cancel at period end
- immediate cancel
- plan change
- entitlement expiration
- refund
- expired card

물리 상품 구매 혜택과 구독 entitlement를 분리한다.

---

## P0-15. 선물 Claim / 개인정보

Gift buyer가 타인의 이름/사진을 넣을 수 있다.

결정:
- 받는 사람 개인정보를 어디까지 구매자가 입력 가능한가
- recipient가 claim 전에 수정/삭제 가능한가
- claim 기간
- claim 실패
- 잘못된 사람 claim
- ownership recovery
- buyer가 recipient 일기를 볼 수 있는가 → **절대 기본 허용 금지**

Buyer와 Owner 권한을 강하게 분리한다.

---

# 2. P1 반드시 보완해야 하는 것

## P1-01. 가격 Snapshot

주문 당시:
- product price
- option
- coupon
- tax
- shipping
- group price
를 snapshot으로 저장.

상품 가격이 바뀌어도 과거 주문 계산이 변하면 안 된다.

---

## P1-02. Coupon / Point Abuse

필요:
- 사용횟수
- 고객당 제한
- 최소주문
- 특정상품 제외
- 중복 가능성
- 취소시 복원
- 부분환불시 처리
- referral self-abuse

---

## P1-03. Marketplace Order Sync

자체몰 + SmartStore + idus + Etsy 등을 실제로 병행하면 별도 운영 문제 발생.

초기에는 수동이어도 되지만 최소한:
- external_order_id
- channel
- payout
- fee
- status
를 공통 Order 모델에 넣어야 한다.

장기:
Channel Adapter.

---

## P1-04. International Tax / Customs

국가별 출시 전에 Country Launch Checklist.

필드:
- HS code
- declared value
- origin
- import duties
- local VAT/GST
- DDP/DDU 정책
- prohibited/restricted item
- packaging/product labeling

“해외 판매 가능”을 global boolean로 만들지 않는다.

Country capability table로 관리.

---

## P1-05. Currency

해외 가격은 실시간 환율 그대로 계산하지 않는 것을 권장.

`KRW base → localized fixed price`

Order:
- display_currency
- charged_currency
- fx reference
- settled_currency

환불시 환율차이 정책 필요.

---

## P1-06. SEO / Storefront Discovery

빠짐:
- metadata
- OpenGraph
- canonical
- sitemap
- robots
- product structured data
- image alt
- category SEO
- locale hreflang
- share preview

개인 Memory Page는 기본 noindex.

---

## P1-07. Accessibility

쇼핑몰에서:
- keyboard
- focus
- contrast
- form labels
- error messages
- alt text
- reduced motion
- screen reader

커스텀 편집 UI에서도 고려.

---

## P1-08. Notification Preference Center

거래 알림과 마케팅을 분리.

사용자:
- order transactional
- Weekly Mirror
- group reminder
- promotional email
- SMS
- Kakao
설정 가능.

수신동의/철회 이력 저장.

---

## P1-09. Analytics Consent / Attribution

마케팅 픽셀을 붙일 경우:
- consent strategy
- GA4
- Meta Pixel
- TikTok Pixel
- UTM
- first/last touch
- server-side event 여부

개인일기/Living Profile 이벤트를 광고플랫폼에 보내지 않는다.

Commerce analytics와 sensitive product analytics를 분리한다.

---

## P1-10. Customer Support Ticket Model

단순 FAQ보다:
- ticket
- order link
- issue category
- SLA
- attachment
- internal note
- resolution
- refund/reprint action

이 필요.

---

## P1-11. Order Edit Window

결제 후 사용자가:
- 주소
- 사진
- 옵션
을 언제까지 수정 가능한지 정의.

`Production Lock` 이후 제한.

---

## P1-12. Production Capacity

판매가 갑자기 늘면 제작이 무너질 수 있다.

Admin:
- daily capacity
- proof capacity
- estimated ship date
- cutoff
- sold-out/temporarily paused

상품 페이지에 제작예정일 계산.

---

## P1-13. Supplier Failure Plan

- 공급처 납기 지연
- 폐업
- 인쇄 품질 급락
- NFC stockout

상품별 primary/secondary supplier.

---

## P1-14. Page Hosting Continuity

NFC는 물리적으로 오래 남는다.

따라서:
- 서비스 종료 시 URL
- 무료 page 보관기간
- archive
- export
- redirect
를 제품 약속으로 정의.

“영구”라는 표현은 실제 운영능력 없이는 쓰지 않는다.

---

## P1-15. Page Version History

사용자가 페이지를 망쳤을 때 rollback.

- draft revision
- published revision
- restore

Gift/Event 페이지에 특히 유용.

---

## P1-16. Search / Enumeration Privacy

`/p/{slug}`가 추측 가능하면 private/unlisted page 노출 위험.

- random slug option
- enumeration 방지
- no directory listing
- password retry limit

---

## P1-17. NFC Clone / Token Abuse

NFC token 자체는 복제 가능하다고 가정해야 한다.

따라서 NFC를 **강한 본인인증 수단으로 사용하지 않는다.**

NFC:
- navigation / possession hint

민감기능:
- 로그인/추가 인증

tap anomaly:
- 비정상 대량 hit rate limit.

---

## P1-18. QR Print Lifecycle

QR:
- 인쇄전 test
- minimum size
- contrast
- quiet zone
- print proof
- token activation
- revoke
- reissue

---

## P1-19. Minors / Age Policy

서비스가 성인 중심이라도 가입 연령 정책 필요.

- 최소 연령
- 미성년 구매
- 부모/법정대리인 관련 처리
- 어린이제품 판매확장 시 별도 launch gate

---

## P1-20. Brand/IP Protection

나봄 자체:
- trademark search
- logo ownership
- generated character commercial rights
- creator/vendor contract
- font license
- stock asset license

---

# 3. P2 향후 고도화

## P2-01. Wish List / Gift Registry
## P2-02. Abandoned Cart
## P2-03. Back-in-stock
## P2-04. Loyalty
## P2-05. Referral
## P2-06. Corporate Account
## P2-07. Approval Chain for B2B
## P2-08. PO / Invoice Payment
## P2-09. Creator/Affiliate Program
## P2-10. Custom Domain for Pages
## P2-11. White-label Event Page
## P2-12. Multi-warehouse
## P2-13. Returns Portal
## P2-14. Recommendation Engine
## P2-15. Gift Scheduling
## P2-16. Page Guestbook Moderation
## P2-17. Group Buy Organizer Commission
## P2-18. Bulk CSV Participant Import
## P2-19. API/Webhook for B2B
## P2-20. Marketplace automation

---

# 4. 현재 문서 자체 QA

구조 외에 문서 품질 문제도 발견.

### Naming/version drift
파일명:
과거 PRD 파일명(구버전)
하지만 내부 제목은 v0.5.

### Backlog old version
`Implementation Backlog v0.7`

### Schema old version
`Core JSON Schemas v0.7`

### Duplicate brand text
`NABOM FIRST 100`
같은 문자열이 남아 있음.

### 원인
이전 버전을 자동 병합하며 단순 문자열 replace가 누적된 흔적.

### Fix
v0.7에서는:
- 파일명/내부버전 통일
- 브랜드명 중복 제거
- 각 문서 `Status`, `Owner`, `Last Reviewed` metadata 추가 권장

---

# 5. 법/정책 QA 메모

실제 출시 전 최신 공식 기준을 다시 확인해야 한다.

문서에 반드시 넣어야 할 구현 포인트:

- 사업자 신원 및 거래조건 표시
- 계약내용 제공
- 커스텀 상품 청약철회 제한의 사전 별도 고지/전자동의
- 디지털콘텐츠 제공 개시 및 청약철회 처리
- 환급 timing
- 개인정보 처리방침
- 국외이전 사용 시 관련 고지
- 광고성 메시지 수신동의/철회
- 매출/PG 정산 및 세무 증빙

이 항목은 법무 체크리스트와 코드의 Consent/Settlement 데이터모델 양쪽에 존재해야 한다.

---

# 6. 최종 Release Gate

## Gate A. 돈을 받기 전

- [ ] 통신판매/PG/사업자 표시
- [ ] 약관/개인정보
- [ ] Order/Payment idempotency
- [ ] Refund test
- [ ] Consent ledger
- [ ] 세무/정산 export
- [ ] 업로드 권리 동의
- [ ] 금지 콘텐츠
- [ ] 관리자 MFA
- [ ] Backup

## Gate B. FIRST 10

- [ ] 실물 QC
- [ ] production lock
- [ ] 주소 오류
- [ ] 배송 분실 simulation
- [ ] NFC revoke/reissue
- [ ] Page takedown
- [ ] 주문 취소
- [ ] 부분환불
- [ ] 고객 데이터 삭제
- [ ] restore test

## Gate C. 공동구매 공개

- [ ] 목표미달 자동처리
- [ ] 참가자취소
- [ ] 주최자취소
- [ ] payment/refund batch
- [ ] production lock
- [ ] organizer privacy
- [ ] bulk/individual shipping
- [ ] campaign dispute policy

## Gate D. 일본/해외

- [ ] 국가별 판매가능 여부
- [ ] currency
- [ ] customs
- [ ] HS/origin
- [ ] duty policy
- [ ] localized terms
- [ ] localized privacy
- [ ] international return
- [ ] delivery tracking
- [ ] 개인정보 국외처리 구조 검토

---

# 7. QA Verdict

### Product Concept
A

### Core Commerce
A-

### Custom Manufacturing
B+

### Group Buy UX
B+

### Payment/Settlement
C

### Accounting/Tax
D+

### Security/DR
C

### Shipping Exceptions
C+

### UGC/Page Abuse
C

### International Readiness
C

### Legal/Consent Implementation
C+

따라서 현재 상태는:

> **개발 시작 가능**
>
> 하지만
>
> **상용 결제 오픈 전 P0 보완 필수**

이다.

기능을 더 늘리는 것보다 위 P0를 먼저 채우는 것이 맞다.
