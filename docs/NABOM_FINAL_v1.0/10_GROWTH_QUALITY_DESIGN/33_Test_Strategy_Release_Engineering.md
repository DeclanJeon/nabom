---
doc_id: LEGACY-7C120C21D4
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 10_GROWTH_QUALITY_DESIGN/33_Test_Strategy_Release_Engineering.md
---

# NABOM Test Strategy / Release Engineering 설계 v1.0

## 1. 목적

QA 체크리스트를 실제 자동/수동 테스트 전략으로 변환한다.

---

## 2. Test Pyramid

### Unit
- price calculation
- group goal
- refund calculation
- entitlement
- token resolver rules

### Integration
- DB
- storage
- queue
- PG sandbox
- marketplace adapter

### Contract
- PG webhook
- external API
- structured AI output

### E2E
- purchase
- customization
- proof
- shipment
- NFC activation
- gift claim
- group buy

---

## 3. Critical E2E

### Flow A
SmartStore/manual import → proof → production → activation.

### Flow B
Direct checkout → payment → refund.

### Flow C
Group buy goal miss → batch refund.

### Flow D
Gift → recipient claim.

### Flow E
NFC lost → revoke → replacement.

### Flow F
Entry delete → Evidence invalidate.

---

## 4. Failure Injection

- PG timeout
- duplicate webhook
- Redis down
- AI timeout
- object storage failure
- marketplace API 429
- mail failure

---

## 5. Load Test

FIRST 100에는 대규모 트래픽보다:
- flash landing
- NFC resolver
- image upload
- group invite
를 우선.

---

## 6. Release

환경:
- local
- staging
- production

필수:
- migration
- rollback plan
- feature flags
- smoke test
- post-release monitor

---

## 7. Database Migration

- backward-compatible 우선
- destructive migration 별도
- backup 확인
- rollback/forward-fix 판단

---

## 8. AI Prompt Version

Profile/Weekly Mirror:
- prompt_version
- schema_version
- model
- generation timestamp

회귀테스트용 golden dataset를 만든다.

---

## 9. Security Test

- auth
- admin role
- IDOR
- upload
- XSS
- token enumeration
- webhook
- rate limit

---

## 10. Release Gate Automation

CI에서:
- lint
- typecheck
- unit
- integration 핵심
- schema validation

Production deploy 전 smoke checklist.
