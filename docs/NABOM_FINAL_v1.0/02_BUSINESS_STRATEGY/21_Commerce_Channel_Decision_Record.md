---
doc_id: LEGACY-EA00C0EDA9
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 02_BUSINESS_STRATEGY/21_Commerce_Channel_Decision_Record.md
---

# NABOM Commerce Channel Decision Record v1.0

## 결정

### FIRST 1~30
국내 결제는 **SmartStore 우선**으로 운영 가능.

자체 NABOM 사이트는:
- 브랜드
- 커스터마이징
- 시안
- NFC
- Page
- Living Service
를 담당.

### FIRST 30~100
Naver Commerce API + Unified Order Hub.
자체 PG Checkout 추가.

### 해외 첫 테스트
Etsy / idus Global / Pinkoi 중 국가에 맞게 사용.

### 해외 직접결제
해외 주문 반복 후 Toss Payments 해외카드/PayPal 추가계약을 검토.

## 이유

사업 초기에는 일반 Commerce 기능보다 나봄의 차별기능 구현과 실제 판매 검증에 개발시간을 집중하는 것이 유리하다.
