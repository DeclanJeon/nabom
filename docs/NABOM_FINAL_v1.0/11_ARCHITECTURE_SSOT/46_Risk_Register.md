---
doc_id: GOV-RISK-001
title: NABOM Risk Register
version: 1.0
status: ACTIVE
updated_at: 2026-08-11
---

# NABOM Risk Register v1.0

| Risk | Impact | Likelihood | Primary Mitigation |
|---|---|---|---|
| 개인화 작업시간 폭증 | High | High | 수정 1회, 자동 생성, capacity |
| Weekly Mirror 가치 부족 | High | Medium | FIRST100 retention 검증 |
| NFC 인식 불편 | Medium | Medium | Portal 분리, QR fallback |
| 제조 불량 | High | Medium | supplier QA, batch trace |
| 공동구매 환불 분쟁 | High | Medium | fixed price, lock policy |
| PG/정산 불일치 | High | Medium | reconciliation |
| 사용자 사진 권리침해 | High | Medium | rights consent/moderation |
| 개인정보/일기 노출 | Critical | Low-Med | RBAC/MFA/audit |
| 외부 AI 장애/비용 | High | Medium | provider adapter/budget |
| Marketplace 의존 | Medium | High | direct channel 단계화 |
| 해외 반품비 폭증 | High | Medium | country matrix/pricing reserve |
| 공급처 지연 | Medium | Medium | secondary supplier |
| 서비스 종료 시 NFC 링크 무용화 | High | Low-Med | resolver continuity/export |
| 과도한 기능 개발 | High | High | FIRST10/100 gate |
| 문서 SSOT 충돌 | High | Medium | canonical registry/state/routes |

각 Risk에는 향후:
- owner
- trigger
- metric
- contingency
를 배정한다.
