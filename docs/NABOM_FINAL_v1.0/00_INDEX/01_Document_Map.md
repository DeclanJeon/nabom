---
doc_id: LEGACY-65C35C470F
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 00_INDEX/01_Document_Map.md
---

# Document Map v1.0

| 영역 | 핵심 문서 | 목적 |
|---|---|---|
| **Phase 0 (엔진 기반)** | **NABOM_Phase0_Design.md** | 사주·주역 엔진 독립 서비스 계약 |
| **Phase 1 (나↔나, 개발 대상)** | **NABOM_Phase1_Design.md** | MVP — 프로필·기록·회고 |
| **Living 캐릭터** | **49_Living_Character_Growth_Visual_System.md** | 일상어 성장 방식·남녀 변형·10단계·PNG/GIF 카탈로그 |
| **Phase 2 (나↔타인)** | **NABOM_Phase2_Design.md** | Relationship 동의 기반 분석 |
| **Phase 3 (나↔그룹)** | **NABOM_Phase3_Design.md** | InsightGroup 익명 집계 분석 |
| 개발 로드맵 | NABOM_Phased_MVP_Design.md | 전체 단계 개요, 커머스 제외 |
| 브랜드/제품 | 01_NABOM_PRD.md | 제품 정의 (아카이브) |
| 엔진 | 02_Living_Self_Engine.md | 분석/프로필 구조 |
| 사업전략 | 08_Business_Strategy_KR_Global.md | 수익/시장 전략 |
| 커머스 | 13_Commerce_Platform_PRD.md | 쇼핑몰 기능 정의 |
| 공동구매 | 14_Group_Buy_System.md | 그룹 주문 구조 |
| 페이지/NFC | 15_NFC_QR_Custom_Page_Builder.md | 디지털 페이지 구조 |
| API/DB | 16_Commerce_Data_Model_API.md | 개발용 도메인 모델 |
| 운영화면 | 17_Commerce_IA_Admin_Operations.md | IA/Admin 설계 |
| 해외판매 | 20_Omnichannel_Domestic_Global_Strategy.md | SmartStore/Etsy/Pinkoi 전략 |
| QA | 18_Full_QA_Gap_Analysis.md | 빠진 요소 점검 |
| 출시 | 19_Release_Readiness_Checklist.md | 오픈 체크리스트 |
| 엔진 백엔드 API | 48_Engine_Backend_API_Separation.md | 사주·주역 독립 서비스와 Facade 계약 |

## 문서 간 연결

```text
PRD
 ├─ Business Strategy
 ├─ Commerce PRD
 │   ├─ Group Buy
 │   ├─ Page Builder
 │   ├─ Data Model/API
 │   └─ Admin/IA
 ├─ Manufacturing
 ├─ Legal/PG/Operations
 ├─ Omnichannel/Global
 └─ QA/Release
 ├─ Private Engine API Boundary
 └─ Living Character Growth Visual System
```


## v1.0 추가 연결

```text
Commerce
 ├─ Payments/Settlement/Tax
 ├─ Subscription/Entitlement
 ├─ Inventory/Fulfillment
 ├─ Returns/Support
 ├─ Account/Gift Ownership
 ├─ B2B
 └─ International Launch

Platform Foundation
 ├─ Security/DR/Observability
 ├─ Data Governance
 ├─ UGC/Rights/Moderation
 ├─ Analytics/Experiment
 ├─ Test/Release
 └─ Design/A11y/SEO
```
