---
doc_id: LEGACY-9404AC23E3
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 08_SECURITY_DATA_GOVERNANCE/26_Content_Rights_Moderation_UGC.md
---

# NABOM Content Rights / UGC / Moderation 설계 v1.0

## 1. 대상

사용자가 업로드/제작하는:
- 사진
- 캐릭터
- 글
- 영상 링크
- 외부 URL
- QR/NFC destination
- Page content

를 다룬다.

---

## 2. 업로드 권리 확인

주문/페이지 발행 시 사용자는:
- 해당 자료 사용 권한이 있음
- 타인의 저작권/초상권/상표권을 침해하지 않음
- 제작/호스팅을 위한 필요한 범위의 처리에 동의

하도록 한다.

---

## 3. 금지/제한 Content

운영정책 필요:
- 불법 콘텐츠
- 악성코드/피싱
- 사칭
- 명백한 개인정보 침해
- 비동의 사적 이미지
- 저작권 침해 신고 대상
- 플랫폼/결제사업자가 금지하는 상품/콘텐츠

정책은 실제 판매국가와 PG/마켓 규정을 반영해 갱신.

---

## 4. IP 캐릭터 주문

유명 캐릭터/연예인/브랜드를 이용한 굿즈는 별도 위험이 있다.

MVP 권장:
- 고객 소유 사진 기반
- 고객 오리지널 캐릭터
- 나봄이 생성한 원본 캐릭터

에 집중.

IP 침해 가능성이 높은 주문은 운영검토/거부 가능.

---

## 5. AI 생성 캐릭터 권리

정책에:
- 사용자 업로드 이미지 사용범위
- 생성물의 상품 제작 사용범위
- 나봄이 포트폴리오/SNS에 재사용하려면 별도 동의
- 모델/provider 약관과 상업 이용 가능 여부

를 기록한다.

---

## 6. Page Abuse

외부 URL:
- javascript/custom HTML 금지(MVP)
- unsafe scheme 금지
- URL validation
- malicious domain 검사 후보
- rate limit

---

## 7. 신고

Page 하단:
`신고하기`

신고 유형:
- 사칭
- 개인정보
- 저작권
- 피싱
- 기타

---

## 8. Moderation State

```text
ACTIVE
REPORTED
UNDER_REVIEW
LIMITED
SUSPENDED
REMOVED
RESTORED
```

운영자 action은 audit.

---

## 9. Takedown

긴급:
피싱/악성.

일반:
권리침해 신고.

절차:
- 접수
- 임시제한 필요성 판단
- 소유자 통지
- 검토
- 복구/삭제

구체 법적 절차는 실제 서비스 국가 기준으로 별도 법률 검토.

---

## 10. Marketing Reuse

고객 리뷰/사진/스토리를 광고에 쓸 때:
- 리뷰 게시 동의와
- 광고/SNS 재사용 동의

를 분리한다.
