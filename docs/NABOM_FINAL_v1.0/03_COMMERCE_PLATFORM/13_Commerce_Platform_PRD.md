---
doc_id: LEGACY-87D037BD8B
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 03_COMMERCE_PLATFORM/13_Commerce_Platform_PRD.md
---

# NABOM Commerce Platform PRD v1.0
## 나봄 쇼핑몰 / 커스텀 제작 / 공동구매 / NFC·QR Page Commerce

## 1. 제품 정의

나봄 커머스는 단순 굿즈 쇼핑몰이 아니다.

하나의 주문에서 아래 세 가지를 결합할 수 있는 **개인화 커머스 플랫폼**이다.

1. Physical Product
   - 아크릴 키링
   - NFC Portal Charm
   - 아크릴 스탠드
   - 포토 참
   - 향후 Portal Object

2. Digital Product
   - NFC/QR 연결 페이지
   - Memory Page
   - Profile Page
   - Event Page
   - Community Page
   - Gift Page

3. Living Service
   - Profile 001
   - Daily Record
   - Weekly Mirror
   - Growth Experiment
   - Subscription

즉 한 주문은 다음 조합을 가질 수 있다.

```text
실물만
실물 + NFC/QR 페이지
페이지 제작만
실물 + 나봄 성장서비스
공동구매 + 참가자별 개인화 + 공동 페이지
```

---

## 2. 핵심 사용자 유형

### Individual Buyer
자기 자신 또는 선물을 위한 단품 구매자.

### Gift Buyer
받는 사람에게 개인화 제품과 페이지를 선물.

### Group Organizer
교회, 회사, 동아리, 팬모임, 졸업, 팀 등의 공동구매 주최자.

### Group Participant
주최자가 만든 공동구매 링크를 통해 자기 옵션/사진을 입력하고 결제.

### Digital-only Buyer
NFC/QR에 연결할 페이지 자체만 주문하는 사용자.

### B2B Buyer
대량 주문, 견적, 일괄배송, 로고/브랜드 페이지 필요.

### Admin / Operator
주문, 시안, 제작, NFC, 배송, 공동구매를 운영.

---

## 3. 상품 체계

### Category A. Personalized Goods
- NABOM Duo Charm
- Memory Charm
- Portal Charm
- Acrylic Stand
- Bag Charm
- Photo Tag
- Custom Event Tag

### Category B. Digital Pages
- Simple Link Page
- Memory Page
- Gift Page
- Event Page
- Community Page
- Profile Page
- Custom Page

### Category C. Bundles
- Charm + Memory Page
- Charm + Living Profile
- Group Package
- Gift Package
- Event Package

### Category D. Services
- Custom Chibi Illustration
- Page Design Service
- Bulk Design Service
- Reprint / Replacement
- NFC Portal Replacement

---

# 4. 기본 쇼핑몰 기능

MVP 이후 빠지지 않아야 할 일반 커머스 기능.

## Catalog
- 카테고리
- 상품목록
- 상품상세
- 옵션
- 이미지/영상
- 가격
- 할인
- 재고/판매상태
- 관련상품

## Search / Discovery
- 검색
- 카테고리 필터
- 가격 필터
- 용도 필터
- 인기/신상품
- 선물용/공동체용 필터

## Account
- 회원가입
- 로그인
- 소셜 로그인
- 프로필
- 배송지
- 주문목록
- 주문상세
- 보유 페이지
- 보유 NFC/QR
- 공동구매
- 쿠폰/포인트
- 찜

## Cart
- 일반상품
- 커스텀 상품
- 페이지 상품
- 혼합 장바구니
- 옵션 변경
- 수량 변경
- 쿠폰
- 배송비 계산

## Checkout
- 주문자
- 수령자
- 배송지
- 배송방법
- 쿠폰
- 포인트
- 주문제작 동의
- 개인정보 동의
- 결제
- 주문완료

## Payments
- 카드
- 간편결제
- 계좌이체
- 해외카드 향후
- 환불
- 부분취소
- 결제 실패 복구

## Order
- 주문상태
- 제작상태
- 시안상태
- 배송상태
- 취소/환불
- 교환/재제작
- 문의

## Marketing
- 쿠폰
- 프로모션 코드
- 기간 할인
- 첫구매 할인
- 친구추천
- 공동구매 할인
- 세트 할인
- 장바구니 할인

## Content
- 공지
- FAQ
- 리뷰
- 포토리뷰
- 상품문의
- 브랜드 스토리
- 사용가이드

---

# 5. 커스텀 상품 주문 UX

일반 옵션 선택 뒤 `Customize` 단계가 추가된다.

## Step 1 상품 선택
예:
`NABOM Duo Charm`

## Step 2 규격/하드웨어
- 사이즈
- 고리
- 추가 참
- 포장

## Step 3 앞면 이미지
- 사진 업로드
- 치비 생성 요청
- 내가 만든 이미지 업로드

## Step 4 뒷면 이미지
- 가족
- 친구
- 공동체
- 자유 이미지

## Step 5 디지털 연결
선택:
- 없음
- 기존 URL 연결
- NABOM Memory Page
- NABOM Gift Page
- NABOM Profile
- 맞춤 페이지 주문

## Step 6 NFC/QR
- NFC만
- QR만
- NFC + QR
- 기존 NFC token 연결

## Step 7 Preview
앞/뒤 목업과 페이지 종류 확인.

## Step 8 결제
커스텀 제작 동의.

## Step 9 제작 자료 제출완료
주문 후에도 마이페이지에서 자료 보완 가능.

---

# 6. 시안 승인

커스텀 제품은 별도 Approval Flow를 가진다.

```text
ASSET_REQUIRED
→ DESIGNING
→ PROOF_READY
→ CUSTOMER_REVIEW
→ REVISION_REQUESTED
→ PROOF_READY
→ APPROVED
→ PRODUCTION
```

사용자 화면:
- 시안 이미지
- 확대
- 수정요청
- 승인
- 승인 후 제작 시작 안내

수정횟수 정책을 상품별 설정 가능하게 한다.

---

# 7. 디지털 페이지 상품

페이지 자체도 `Product`다.

### BASIC LINK PAGE
NFC/QR → 버튼/링크 모음.

### MEMORY PAGE
- 대표사진
- 제목
- 설명
- 사진갤러리
- 타임라인
- 메시지
- 영상/외부링크

### GIFT PAGE
- 선물 메시지
- 받는 사람 이름
- 사진
- 숨겨진 메시지
- 공개일 지정 가능

### EVENT PAGE
- 행사 소개
- 일정
- 사진
- 장소
- 참가자 메시지
- 사후 추억 갤러리

### COMMUNITY PAGE
- 공동체 소개
- 단체사진
- 구성원
- 기록
- 공지/링크

### PROFILE PAGE
- Profile 001
- 현재 성장테마
- 사용자 선택 공개 영역

### CUSTOM PAGE
운영자가 고객 요구에 맞춰 제작.

---

# 8. 상품과 페이지 연결

하나의 Physical Product는 0~N개의 Digital Page에 연결 가능하도록 확장성을 둔다.

초기 기본:
`1 NFC token → 1 active destination`

하지만 redirect layer를 두어 destination을 변경할 수 있다.

```text
NFC
→ /k/{token}
→ Resolver
→ Page / External URL / Profile
```

NFC를 다시 굽지 않고 목적지를 변경할 수 있어야 한다.

---

# 9. 선물 주문

구매자와 실제 사용자가 다를 수 있다.

### Buyer
결제/배송 담당.

### Recipient
NFC 활성화 후 자신의 계정에 Claim.

Gift Flow:

```text
Buyer Order
→ Gift Produced
→ Recipient receives
→ NFC Tap
→ Claim Code
→ Recipient Account
→ Page/Profile Ownership Transfer
```

받는 사람이 가입하지 않아도 공개 Gift Page는 볼 수 있게 할 수 있다.

---

# 10. 주문 상태 모델

### Commerce
- PENDING_PAYMENT
- PAID
- PAYMENT_FAILED
- CANCELLED
- REFUND_REQUESTED
- REFUNDED

### Customization
- ASSET_REQUIRED
- ASSET_SUBMITTED
- DESIGNING
- PROOF_READY
- REVISION
- APPROVED

### Fulfillment
- PRODUCTION_READY
- PRODUCTION
- QC
- PACKED
- SHIPPED
- DELIVERED

### Digital
- TOKEN_RESERVED
- PAGE_DRAFT
- PAGE_READY
- ACTIVATED
- CLAIMED

상태를 하나의 거대한 enum으로 만들지 말고 sub-status로 분리한다.

---

# 11. 리뷰

일반 별점뿐 아니라 나봄 특화 리뷰.

- 실물 만족도
- 캐릭터 만족도
- 선물 반응
- NFC 편의성
- 페이지 만족도

포토/영상 리뷰 가능.

운영자 승인 후 SNS 사용 동의를 별도 받을 수 있다.

---

# 12. 구독

Commerce 계정과 Living Service entitlement를 연결한다.

상품 구매 시:
- `21_day_growth_pass`
- `weekly_mirror_3`
등 entitlement를 지급.

정기결제:
- Free
- Growth Monthly
- Growth Annual

---

# 13. 국제화

초기:
- ko-KR
- ja-JP

향후:
- en-US
- zh-TW

아키텍처부터:
- locale
- currency
- localized product content
- localized SEO
- localized legal notice
를 분리한다.

---

# 14. 주요 라우트

```text
/
 /shop
 /shop/[category]
 /products/[slug]
 /customize/[productId]
 /cart
 /checkout
 /order/[orderNo]

 /group-buy
 /group-buy/[slug]
 /group-buy/[slug]/join
 /group-buy/create

 /pages
 /pages/new
 /pages/[pageId]/edit

 /my
 /my/orders
 /my/pages
 /my/nfc
 /my/group-buys
 /my/reviews
 /my/coupons

 /k/[token]
 /q/[token]

 /support
 /faq

 /admin
```

---

# 15. 핵심 KPI

Commerce:
- Product View → Add to Cart
- Add to Cart → Checkout
- Checkout → Paid
- Custom Asset Completion
- Proof Approval Time
- Revision Rate
- Order Lead Time
- Refund/Defect Rate

Digital:
- NFC First Tap
- Page Activation
- Recipient Claim
- Repeat Tap

Group Buy:
- Campaign Created
- Invite → Join
- Goal Achievement
- Participant Completion
- Final Production Conversion


---

# 16. Sales Channel Architecture v1.0

나봄 커머스는 자체 Checkout만을 전제로 하지 않는다.

지원 채널:

```text
NABOM_DIRECT
NAVER_SMARTSTORE
IDUS
ETSY
PINKOI
B2B_OFFLINE
```

외부 플랫폼에서 결제된 주문도 NABOM Order Hub로 들어와 이후 동일한 제작 workflow를 탄다.

```text
External Checkout
→ Channel Order Import
→ NABOM Internal Order
→ Customization
→ Proof
→ Production
→ NFC/QR
→ Shipping
→ Activation
```

## Lean Launch Mode

FIRST 30까지는:

- SmartStore = 국내 결제/주문
- idus = 커스텀 선물 노출
- NABOM = 제작/디지털 경험

구조를 공식 지원한다.

따라서 Commerce Platform MVP는 `자체 Checkout 완성`보다:

1. External Order Claim
2. Sales Channel field
3. Customization intake
4. Proof
5. Fulfillment
6. NFC Activation

을 먼저 구현해도 된다.

## Own Checkout Activation

아래 조건 중 하나가 발생하면 자체 Checkout을 P0로 승격한다.

- 공동구매 출시
- Page 단독판매
- 구독
- 복잡 Bundle
- B2B 자동견적
- marketplace 수수료가 의미있는 규모

## Overseas

해외 marketplace 주문도 같은 Order Hub를 사용한다.

해외결제 직접지원은 `CountryLaunchConfig.enabled = true`인 국가에서만 노출한다.


---

# Canonical Reference Notice v1.0

이 문서의 초기 route/state 예시는 기능 설명용이다.

구현 시 우선순위:
1. `11_ARCHITECTURE_SSOT/37_Canonical_Domain_Registry.md`
2. `11_ARCHITECTURE_SSOT/38_Canonical_State_Machines.md`
3. `11_ARCHITECTURE_SSOT/39_Canonical_Routes_URLs.md`

이 세 문서와 충돌하는 초기 예시는 deprecated로 간주한다.
