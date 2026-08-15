---
doc_id: LEGACY-59A5CFB7D1
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 00_INDEX/02_Document_Change_Policy.md
---

# Documentation Change Policy v1.0

## 원칙

### 1. 단일 문서에 모든 변경사항을 누적하지 않는다.
- 통합본에 직접 수정 금지
- 해당 도메인 문서만 수정

### 2. 구조가 바뀌면 Decision Record를 남긴다.
예:
- 판매채널 변경
- SmartStore-first → Direct-first
- 해외진출 순서 변경
- 구독정책 변경

### 3. QA 문서는 결과문서다.
- 설계는 설계문서에
- 누락분석은 QA 문서에
- 출시조건은 Checklist에

### 4. 개발 착수 시
- 기능은 PRD
- 데이터는 API/Schema
- 운영은 IA/Admin
- 리스크는 QA
를 기준으로 한다.
