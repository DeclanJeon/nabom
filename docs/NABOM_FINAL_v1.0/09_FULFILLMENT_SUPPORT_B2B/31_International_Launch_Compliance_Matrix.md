---
doc_id: LEGACY-ECCC62B451
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 09_FULFILLMENT_SUPPORT_B2B/31_International_Launch_Compliance_Matrix.md
---

# NABOM International Launch Matrix 설계 v1.0

## 1. 원칙

“해외판매 ON”이라는 단일 플래그를 쓰지 않는다.

국가별로:
- 상품
- 결제
- 배송
- 반품
- 세금/관세
- 제품안전
- 개인정보
- 소비자법
- 마켓플레이스

준비상태가 다르다.

---

## 2. CountryLaunchConfig

```text
country
locale
currency
marketplace_enabled
direct_checkout_enabled
physical_enabled
digital_enabled
shipping_profile
returns_profile
tax_mode
duty_mode
legal_review_status
privacy_review_status
product_safety_status
```

---

## 3. 단계

### DISCOVERY
시장/채널 조사.

### MARKETPLACE_TEST
Etsy/Pinkoi/idus 등.

### LIMITED_DIRECT
일부 제품 Direct.

### FULL_DIRECT
현지화 결제/약관/CS.

---

## 4. 국가별 체크리스트

- 상품 적합성
- 가격
- 결제수단
- 통화
- 배송기간
- tracking
- 관세/수입세 부담주체
- 반품주소
- 제품표시
- 개인정보
- 마케팅 메시지
- 디지털 콘텐츠
- 현지 고객지원 언어
- 플랫폼 정책

실제 규정은 출시 시점 최신 공식 소스로 재검증한다.

---

## 5. 우선순위 가설

1. Korea
2. Japan
3. Taiwan / Singapore
4. Australia / Canada
5. UK
6. USA
7. EU

이는 고정이 아니라 실제 conversion/배송/CS 데이터로 업데이트.

---

## 6. Landed Cost

국가별 가격:
```text
COGS
+ packaging
+ channel fee
+ payment
+ international shipping
+ duty/tax risk
+ return reserve
+ support reserve
+ margin
```

---

## 7. Returns

해외 반품은 국내와 별도 policy.

- return shipping
- damaged
- customs rejection
- unclaimed
- return-to-sender

비용이 상품가보다 큰 경우 replacement/refund 정책을 사전 정의.

---

## 8. Digital-only

물리 제품보다 진출이 쉬울 수 있으나:
- 결제
- 소비자보호
- 개인정보
- 디지털콘텐츠 환불
을 별도로 검토.

---

## 9. Launch Gate

나라별 launch approval을 Admin/Config에서 관리.
