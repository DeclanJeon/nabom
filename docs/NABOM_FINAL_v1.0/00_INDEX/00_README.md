---
doc_id: LEGACY-BE0808579D
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 00_INDEX/00_README.md
---

# NABOM Final Modular Documentation Pack v1.0

> ## 개발 기준 문서 변경 (2026-08-13)
>
> 개발은 **페이즈별 단일 설계서**를 기준으로 진행한다.
> - Phase 0: `NABOM_Phase0_Design.md` — 사주·주역 엔진 기반 계약
> - **Phase 1 (현재 개발 대상)**: `NABOM_Phase1_Design.md` — 나↔나 MVP (프로필·기록·회고)
> - Phase 2: `NABOM_Phase2_Design.md` — 나↔타인 (동의 기반 관계 분석)
> - Phase 3: `NABOM_Phase3_Design.md` — 나↔그룹 (익명 집계 분석)
> - **커머스, NFC/키링, 공동구매는 전체 로드맵에서 제외/보류**
> - 전체 단계 로드맵은 `NABOM_Phased_MVP_Design.md` 참고
> - 아래 모듈 문서들은 상세 참고/아카이브로만 유지한다

이 패키지는 하나의 거대한 통합 설계서 대신,
**도메인별로 나눈 모듈형 문서 세트**다.

## 왜 이렇게 나눴는가

하나의 md 파일에 모든 내용을 계속 붙이면 다음 문제가 생긴다.

- 문서가 너무 길어져서 검색/수정이 어려움
- 버전 충돌과 중복 문구가 생김
- 수정 영향범위를 파악하기 어려움
- 실제 개발/운영 시 어떤 문서를 기준으로 봐야 할지 모호해짐
- 빠진 내용이 생겨도 발견이 늦어짐

그래서 이번 패키지는 **역할별로 분리**했다.

---

## 폴더 구조

### 00_INDEX
- 전체 문서 안내
- 문서 맵
- 추천 읽기 순서

### 01_BRAND_PRODUCT
- 브랜드/도메인 결정
- 제품 PRD
- Living Self Engine
- 핵심 JSON Schema

### 02_BUSINESS_STRATEGY
- 사업 전략
- 마케팅/영업
- 90일 실행계획
- 커머스 채널 의사결정 기록

### 03_COMMERCE_PLATFORM
- 쇼핑몰/커머스 PRD
- 데이터모델/API
- IA/Admin 운영

### 04_CUSTOM_GOODS_NFC_PAGE
- 제조/소싱
- NFC/QR 맞춤 페이지
- 보안/NFC/개인정보

### 05_GROUPBUY_CHANNELS_GLOBAL
- 공동구매
- 국내/해외 판매채널 전략
- 커머스 법무/PG/운영

### 06_OPERATIONS_QA_RELEASE
- FIRST100 운영
- 백로그
- 전체 QA 갭 분석
- 출시 체크리스트

---

## 추천 읽기 순서

### 1. 사업 전체 방향 파악
1. `01_BRAND_PRODUCT/07_Brand_Domain_Decision.md`
2. `01_BRAND_PRODUCT/01_NABOM_PRD.md`
3. `02_BUSINESS_STRATEGY/08_Business_Strategy_KR_Global.md`

### 2. 실제 판매 구조 파악
4. `05_GROUPBUY_CHANNELS_GLOBAL/20_Omnichannel_Domestic_Global_Strategy.md`
5. `03_COMMERCE_PLATFORM/13_Commerce_Platform_PRD.md`
6. `05_GROUPBUY_CHANNELS_GLOBAL/14_Group_Buy_System.md`

### 3. 제작과 운영
7. `04_CUSTOM_GOODS_NFC_PAGE/09_Manufacturing_Sourcing_Playbook.md`
8. `05_GROUPBUY_CHANNELS_GLOBAL/10_Commerce_Legal_PG_Operations.md`
9. `06_OPERATIONS_QA_RELEASE/04_NABOM_FIRST100_Operations.md`

### 4. 개발 착수
10. `03_COMMERCE_PLATFORM/16_Commerce_Data_Model_API.md`
11. `03_COMMERCE_PLATFORM/17_Commerce_IA_Admin_Operations.md`
12. `06_OPERATIONS_QA_RELEASE/05_Implementation_Backlog.md`

### 5. 출시 전 최종 점검
13. `06_OPERATIONS_QA_RELEASE/18_Full_QA_Gap_Analysis.md`
14. `06_OPERATIONS_QA_RELEASE/19_Release_Readiness_Checklist.md`

---

## 실무 기준 문서 사용법

### 사업 결정을 바꿀 때
- `02_BUSINESS_STRATEGY`
- `05_GROUPBUY_CHANNELS_GLOBAL`

### 화면/기능 설계할 때
- `03_COMMERCE_PLATFORM`

### 제작처/원가/배송을 잡을 때
- `04_CUSTOM_GOODS_NFC_PAGE`
- `06_OPERATIONS_QA_RELEASE`

### 출시 직전
- `18_Full_QA_Gap_Analysis.md`
- `19_Release_Readiness_Checklist.md`

---

## 권장 운영 원칙

- **통합본은 참고용**
- **실제 수정은 각 모듈 문서에서만**
- 변경 시 관련 문서만 부분 업데이트
- 대규모 방향 변화가 있으면 `Decision Record` 추가
- 버전 업데이트 시 폴더는 유지하고 문서만 교체



---

## v1.0 추가 모듈

### 07_FINANCE_PAYMENTS_TAX
- 결제 상태/실패
- PG·마켓 정산
- 가격 Snapshot
- 세무/회계 Export
- 구독/Entitlement

### 08_SECURITY_DATA_GOVERNANCE
- 관리자/웹 보안
- 모니터링
- 백업/복구
- 데이터 보존/삭제
- Consent Ledger
- UGC/저작권/피싱 대응

### 09_FULFILLMENT_SUPPORT_B2B
- 재고/BOM/발주
- 생산능력
- 배송 예외
- 반품/교환/재제작
- Support Ticket
- B2B 견적/계약
- 비회원 구매/Gift Ownership
- 국가별 해외 Launch Matrix

### 10_GROWTH_QUALITY_DESIGN
- Analytics/Attribution
- A/B Test
- 자동화 테스트/Release
- Design System/접근성/SEO
- SLA/Capacity/Cost Guardrail

## 중요한 v1.0 판단

v0.8 QA 문서에서 “빠졌다”고 기록한 P0 항목 중 상당수를
이번 버전에서 **실제 독립 설계 문서로 승격**했다.

앞으로 QA 문서는 설계가 아니라 Gap 탐지에만 사용한다.


---

## v1.0 최종 SSOT

`11_ARCHITECTURE_SSOT` 폴더가 cross-domain 구현의 최우선 기준이다.

특히:
- `36_System_Architecture.md`
- `37_Canonical_Domain_Registry.md`
- `38_Canonical_State_Machines.md`
- `39_Canonical_Routes_URLs.md`
- `47_Documentation_Standard.md`

를 개발 전에 반드시 읽는다.

최종 QA:
`00_INDEX/06_FINAL_QA.md`
