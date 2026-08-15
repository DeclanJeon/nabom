---
doc_id: LEGACY-EE850D9DD8
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 08_SECURITY_DATA_GOVERNANCE/24_Security_DR_Observability.md
---

# NABOM Security / Disaster Recovery / Observability 설계 v1.0

## 1. 보안 모델

나봄은:
- 결제
- 배송주소
- 개인사진
- 출생정보
- 일기
- 관계기록

을 다루므로 일반 굿즈몰보다 높은 수준의 권한 분리가 필요하다.

---

## 2. 인증

Customer:
- email verification
- password reset
- social login
- session list/revoke

Admin:
- MFA 필수
- RBAC
- 세션 짧게
- 민감작업 재인증 검토

---

## 3. Web Security

필수:
- HTTPS
- secure/HttpOnly cookies
- SameSite
- CSRF protection
- XSS escaping
- CSP
- rate limiting
- brute-force protection
- webhook signature verification
- secret rotation

---

## 4. 권한

Role 예:
- CUSTOMER
- SUPPORT
- DESIGNER
- FULFILLMENT
- FINANCE
- ADMIN
- SUPER_ADMIN

Designer는 결제/일기를 볼 필요가 없다.
Fulfillment는 Living Profile을 볼 필요가 없다.
Support도 raw journal은 기본 접근 금지.

---

## 5. Observability

### Logs
- app errors
- payment webhook
- job failures
- NFC resolver
- admin actions

PII/raw journal을 로그에 남기지 않는다.

### Metrics
- API latency
- error rate
- queue lag
- payment failure
- weekly job failure
- upload failure
- NFC resolver 5xx

### Alert
- payment webhook failure spike
- DB/Redis unavailable
- queue backlog
- error rate threshold
- storage errors
- backup failure

---

## 6. Incident Severity

예:
- SEV1: 결제/개인정보/전체 장애
- SEV2: 주문/NFC/페이지 주요 장애
- SEV3: 일부 기능 장애

각 SEV별:
- owner
- response
- internal comms
- customer notice
- postmortem

---

## 7. Backup

대상:
- PostgreSQL
- object storage metadata
- configuration
- critical secrets backup process

권장:
- PITR 지원
- 정기 snapshot
- restore test

RPO/RTO는 비용에 맞게 숫자를 확정하되 문서화한다.

---

## 8. Restore Drill

백업이 있다는 것과 복구 가능한 것은 다르다.

정기적으로:
1. isolated environment restore
2. integrity check
3. sample order/NFC/page verification
4. 결과 기록

---

## 9. Job Safety

Weekly Mirror, page processing, mail, settlement sync:

- retry
- exponential backoff
- dead-letter queue
- idempotency
- manual replay

---

## 10. Dependency Failure

- PG
- email/SMS
- AI provider
- storage
- CDN
- maps/geocoding
- marketplace API

provider outage 시 graceful degradation 정의.

---

## 11. Status / Incident Communication

MVP 이후:
- status page 또는 공지
- incident ID
- affected functions
- resolution time 기록

---

## 12. Security Review Gate

FIRST 10 전:
- admin MFA
- upload isolation
- payment webhook security
- backup

FIRST 100 전:
- restore drill
- penetration-style checklist
- dependency failure test
