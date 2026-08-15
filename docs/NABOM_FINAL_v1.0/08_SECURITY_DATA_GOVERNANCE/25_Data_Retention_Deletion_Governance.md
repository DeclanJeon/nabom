---
doc_id: LEGACY-C777747244
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 08_SECURITY_DATA_GOVERNANCE/25_Data_Retention_Deletion_Governance.md
---

# NABOM Data Retention / Deletion / Governance 설계 v1.0

## 1. 목적

“삭제 기능 있음”에서 끝내지 않고 데이터 종류마다 보존·삭제·익명화·법정 보존 여부를 구분한다.

출시 전 실제 법적 보존기간은 최신 공식 기준과 전문가 검토를 통해 확정한다.

---

## 2. Data Classification

### Account
이메일, 인증정보.

### Commerce
주문, 결제, 배송, 환불.

### Sensitive Product
출생정보, 일기, 감정, 관계.

### Media
사진, 생성 캐릭터, 제작파일.

### Analytics
이벤트.

### Audit
관리자 접근/동의 이력.

---

## 3. Retention Policy Table

각 데이터셋에:
- purpose
- owner
- retention basis
- retention period
- deletion trigger
- anonymization rule

를 정의한다.

---

## 4. 계정 탈퇴

탈퇴 요청:
1. 로그인 확인
2. 처리 예정 데이터 설명
3. active order/subscription 처리
4. 삭제 job
5. 완료 기록

법/회계상 별도 보존이 필요한 거래정보는 Living Profile 데이터와 분리한다.

---

## 5. 일기 삭제

사용자가 Entry 삭제 시:
- raw entry 삭제/비활성
- derived Evidence invalidate
- Pattern 재계산
- Profile 영향 표시

삭제한 일기를 AI가 계속 근거로 쓰면 안 된다.

---

## 6. 사진 삭제

구분:
- uploaded original
- generated derivative
- print production asset
- public page derivative

연결관계를 추적한다.

---

## 7. AI Provider

외부 AI 요청:
- 직접식별자 최소화
- retention/training policy 확인
- provider/version 기록
- 필요 시 국외처리 검토

---

## 8. Consent Ledger

```text
ConsentRecord
- subject
- type
- policy_version
- text_hash
- agreed_at
- revoked_at
- ip
- user_agent
- source
```

마케팅 동의는 거래 필수동의와 분리.

---

## 9. Data Export

사용자 export:
- profile
- journal
- page content
- media references

형식:
JSON + Markdown 후보.

거래/세무자료는 export 범위를 별도 정의.

---

## 10. Page Hosting Continuity

NFC 물리제품은 오래 남는다.

따라서:
- 무료 기본 redirect 유지 범위
- 페이지 archive
- export
- 서비스 종료 시 대응
- 도메인 변경 redirect

를 운영정책에 둔다.

실제 보장할 수 없다면 “영구” 표현 금지.

---

## 11. Data Access Audit

민감 데이터 조회:
- who
- when
- purpose
- object
- action

Support/Designer/Admin 권한별로 기록한다.
