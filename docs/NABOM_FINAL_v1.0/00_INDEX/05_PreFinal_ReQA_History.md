---
doc_id: LEGACY-9F776AC3DF
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 00_INDEX/05_PreFinal_ReQA_History.md
---

# NABOM v1.0 Re-QA Verdict

## 검토 결과

v0.8에서 발견된 가장 큰 문제는:
**QA 문서에 누락사항을 적어두었지만 실제 설계문서가 없었다는 것**이다.

v0.9에서는 다음을 독립 설계로 보완했다.

- 결제/정산/세무
- 구독/Entitlement
- 보안/DR/Observability
- 데이터 보존/삭제/Consent
- UGC/저작권/Moderation
- 재고/BOM/발주/Fulfillment
- Returns/Claims/Support
- B2B Quote/Contract
- Guest Checkout/Gift Ownership
- 국가별 International Launch Matrix
- Analytics/Experimentation
- Test/Release Engineering
- Design System/Accessibility/SEO
- Capacity/Cost Guardrail

## 아직 “문서로 확정할 수 없는” 외부 의존 항목

아래는 제품 설계 누락이 아니라 출시 시점 재검증 항목이다.

1. 실제 PG 계약조건/수수료
2. 통신판매·전자상거래 최신 법적 문구
3. 개인정보 국외이전 요건
4. 국가별 통관/제품안전
5. SmartStore/idus/Etsy/Pinkoi 최신 정책/API
6. 실제 제조사 MOQ/납기/원가
7. 세금계산서/현금영수증의 실제 구현 방식

이들은 별도의 `Launch Verification` 절차로 최신 공식자료를 확인해야 한다.

## 현재 남은 큰 설계 공백

“서비스 범주” 수준의 명백한 P0 공백은 거의 없다.

다만 실제 개발 전 다음은 더 내려가야 한다.

- ERD 전체본
- API OpenAPI 수준 Contract
- Payment State Machine diagram
- Group Buy Money State Machine
- Order/Production State Machine
- Wireframe
- Admin Wireframe
- DB migration plan
- 실제 Terms/Privacy 문안
- 실제 price/unit economics sheet

이들은 누락이라기보다 **구현 상세 설계 단계**다.

## Verdict

- Concept coverage: A
- Commerce coverage: A
- Operations coverage: A-
- Finance/Settlement coverage: A-
- Security/Data coverage: A-
- Fulfillment coverage: A-
- Global coverage: B+ (국가별 외부규정 검증 필요)
- Implementation-detail readiness: B

따라서 다음 단계는 새로운 기능을 찾는 것이 아니라
**상위 설계를 ERD/API/State Machine/Wireframe로 변환하는 것**이다.
