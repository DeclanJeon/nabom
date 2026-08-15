---
doc_id: GOV-DOC-001
title: NABOM Documentation Standard
version: 1.0
status: SSOT
updated_at: 2026-08-11
---

# Documentation Standard v1.0

## 1. 파일명

앞으로 파일명에 버전을 넣지 않는다.

예:
`Product_PRD`

버전은 frontmatter에만 기록.

v1.0 패키지는 과거 파일명을 보존했지만,
신규/대규모 개정 문서는 stable filename을 사용한다.

---

## 2. Frontmatter

모든 문서:
- doc_id
- version 또는 package_version
- status
- updated_at

권장:
- owner
- depends_on

---

## 3. SSOT 우선순위

충돌 시:

1. Canonical SSOT 문서
2. 해당 Domain 상세 설계
3. Product/Commerce PRD
4. Playbook
5. QA/과거 분석

QA 문서에 있는 오래된 상태/파일명은 역사 기록으로 본다.

---

## 4. Status

- DRAFT
- REVIEW
- APPROVED_BASELINE
- SSOT
- DEPRECATED
- ARCHIVED
- BASELINE_IMPORTED

---

## 5. 변경 방식

상태/URL/Entity 같은 cross-domain 변경은
반드시 Canonical 문서를 먼저 변경한다.

그 뒤 affected docs를 업데이트한다.
