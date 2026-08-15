---
doc_id: LEGACY-C8F1820041
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 04_CUSTOM_GOODS_NFC_PAGE/03_Data_Privacy_Security_NFC.md
---

# 나봄 Data / Privacy / Security / NFC 설계

## 1. 데이터 민감도

Living Self Engine에는 다음과 같은 민감한 개인 기록이 쌓인다.

- 생년월일 및 출생시간/지역
- 일기
- 감정
- 관계 이야기
- 사진
- 목표
- 개인적 고민
- 타인에 대한 내용

따라서 “일기 앱 수준”이 아니라 **개인 기록 저장소** 기준으로 설계한다.

---

## 2. 최소 수집

MVP에서 정말 필요한 데이터만 받는다.

필수:
- 인증 정보
- 닉네임
- 생년월일
- 출생지역
- 체크인

선택:
- 정확한 출생시간
- 목표
- 자유일기
- 사진

“왜 필요한지”를 입력 화면에서 설명한다.

---

## 3. 데이터 사용 구분

반드시 분리한다.

### Service Use
사용자에게 프로필/리포트 제공.

### Product Improvement
서비스 품질 개선.

### Research
사주/행동/성격 상관 등을 연구하기 위한 익명화 데이터 분석.

Research는 별도의 명시적 opt-in 없이는 사용하지 않는 방향을 기본으로 한다.

---

## 4. 삭제권

설정에서:

- 특정 일기 삭제
- 특정 사진 삭제
- 프로필 초기화
- AI 추론 데이터 초기화
- 전체 계정/데이터 삭제

를 제공한다.

Raw record가 삭제되면 해당 record만으로 생성된 Evidence/Pattern의 재계산 또는 무효화 정책을 정의한다.

---

## 5. 데이터 Export

Phase 1.5 권장.

사용자는 자신의 기록을 JSON 또는 Markdown 형태로 내려받을 수 있어야 한다.

장기적으로 이 기능은 신뢰에 중요하다.

---

## 6. NFC 보안 원칙

NFC에는 민감한 데이터 URL을 넣지 않는다.

권장:

```text
https://nabom.ponslink.com/k/{opaque_token}
```

토큰은:

- 사용자 ID를 추측할 수 없어야 함
- 취소/revoke 가능
- 새 키링에 재매핑 가능

---

## 7. NFC Tap Flow

### 로그인된 본인
`오늘의 나 기록하기` 또는 Home.

### 로그아웃 상태
로그인/복구.

### 타인
소유자가 공개 프로필을 허용했다면 공개 카드만 표시.

기본값은 private.

---

## 8. 키링 분실

설정:

`키링을 잃어버렸어요`

처리:

1. 기존 NFC token revoke
2. 기존 키링 접근 중단
3. 계정 데이터 영향 없음
4. 새 키링 token 발급 가능

---

## 9. NFC 불량

운영자가 새 NFC token을 생성해 replacement tag에 연결할 수 있어야 한다.

Admin 기능:

- token 검색
- user mapping 확인
- revoke
- regenerate
- replacement status

---

## 10. 공개 프로필

공유 기능이 생기더라도 private 데이터와 분리한다.

Public Profile 후보:

- 치비
- 닉네임
- 한 줄 소개
- 사용자가 직접 선택한 성장 테마
- 공개 승인한 사진

절대 기본 공개하지 않음:

- 생년월일시
- 일기
- 감정 기록
- AI 패턴 분석
- 관계 기록

관계·그룹 분석도 기본 비공개다. `Relationship`은 양쪽 `InsightConsent`가 승인한 scope만 사용하며, 한쪽 철회 즉시 새 분석을 중단하고 기존 `RelationshipMirror`를 suspended 처리한다. `InsightGroup`은 최소 5명의 활성 동의 구성원이 없으면 개인 추정이 가능한 분석을 생성하지 않는다.

`GroupBuy`의 참가·주문 정보는 `InsightGroup` 구성원이나 관계 분석에 자동 편입하지 않는다. 그룹 간 분석은 aggregate-only 결과만 반환하고 구성원 개인을 역산할 수 있는 소수 패턴을 숨긴다.

---

## 11. 제3자 데이터

사용자가 일기에서 친구, 가족, 연인의 이야기를 적을 수 있다.

시스템은 제3자에 대한 성격 진단을 생성하지 않는다.

예:
“친구가 나르시시스트인 것 같아.”

AI가 기록 분석 과정에서 그 사람을 진단하거나 사실로 저장하지 않는다.

사용자 자신의 감정/반응 중심으로 재구성한다.

---

## 12. AI Provider 데이터 정책

외부 LLM 사용 시 개발 전에 확인할 항목:

- API 입력 데이터가 모델 학습에 사용되는지
- retention 기간
- region
- 로그 저장 여부
- 데이터 삭제 가능 여부

가능하면 민감한 raw journal을 최소 컨텍스트로 전달하고, 불필요한 직접 식별자를 제거한다.

---

## 13. 데이터 암호화

MVP 최소 요구:

- HTTPS/TLS
- DB encryption at rest 지원
- 비밀번호 직접 저장 금지
- secret/env 분리
- access token rotation
- admin RBAC
- raw journal 접근 audit

---

## 14. 관리자 접근

관리자가 사용자의 일기를 기본 화면에서 자유롭게 볼 수 없어야 한다.

CS에 필요할 경우:

- 사용자 동의
- 제한적 접근
- access log

구조를 권장.

---

## 15. 정신건강 안전

이 서비스는 심리치료 또는 진단 도구가 아니다.

AI는 다음을 진단하지 않는다.

- 우울증
- ADHD
- 성격장애
- PTSD
- 기타 정신질환

사용자가 위기 신호를 남기면 일반적인 성장 분석보다 안전 대응이 우선한다.

실제 출시 시 국가별 위기 대응/정책을 별도 Safety Spec으로 정의한다.

---

## 16. 성장 실험 안전

AI가 제안하면 안 되는 예:

- 처방약 조정
- 투자를 하거나 대출받기
- 법적 대응 확정
- 배우자/친구와 즉시 절교
- 위험한 신체행동
- 수면 박탈
- 극단적 식이

나봄(NABOM)의 실험은 **작고 되돌릴 수 있는 자기관찰 행동**이어야 한다.

---

## 17. Birth Analysis Transparency

사용자 기본화면에 “사주” 용어를 밀어 넣지 않는다.

하지만 설정 → 분석 방법에서:

“첫 프로필을 만들 때 사용자가 제공한 현재 상태와 출생정보를 참고합니다. 출생정보 분석에는 동아시아 전통 명리 체계가 초기 성향 가설을 만드는 참고 도구로 사용됩니다. 이 결과는 진단이나 과학적 확정값이 아니며 실제 기록과 피드백이 쌓일수록 영향이 줄어듭니다.”

정도의 고지는 필요하다.

---

## 18. 출시 전 Privacy Checklist

- [ ] 개인정보 처리방침
- [ ] 서비스 이용약관
- [ ] AI 분석 고지
- [ ] 출생정보 이용 목적
- [ ] 사진 저장 정책
- [ ] 삭제 정책
- [ ] 데이터 export 정책
- [ ] 연구 데이터 별도 동의
- [ ] 외부 AI provider 검토
- [ ] NFC 분실/취소
- [ ] 관리자 audit


---

## 19. 공식 라우팅 정책

### NFC / QR
`https://nabom.ponslink.com/k/{token}`

### 인증 후 기본 진입
`https://nabom.ponslink.com/today`

### 프로필
`https://nabom.ponslink.com/profile`

### Weekly Mirror
`https://nabom.ponslink.com/mirror`

### 성장 타임라인
`https://nabom.ponslink.com/journey`

NFC token은 사용자 ID와 분리된 opaque token을 사용한다.
