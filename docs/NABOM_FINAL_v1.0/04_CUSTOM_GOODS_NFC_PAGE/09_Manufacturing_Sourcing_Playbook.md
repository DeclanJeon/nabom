---
doc_id: LEGACY-27188CA7A9
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 04_CUSTOM_GOODS_NFC_PAGE/09_Manufacturing_Sourcing_Playbook.md
---

# NABOM 제조·소싱·원가 Playbook v1.0

## 1. 초기 제조 원칙

1~100개 단계에서는 최저단가보다 다음을 우선한다.
- 1개 단위 개인화
- 앞/뒤 서로 다른 이미지
- 품질
- 수정 대응
- 납기
- 불량 재제작

중국/해외 OEM은 수요가 반복된 이후 비교한다.

## 2. 국내 샘플 후보

초기 비교 후보:
- 레드프린팅
- 오프린트미
- 마플

해외 대량 후보:
- Vograce
- Alibaba/1688 OEM은 별도 샘플과 업체 검증 이후

### 견적의 함정
일반적인 “100개 단가”는 동일 디자인 100개일 수 있다.
나봄은 초기에 사실상:

> **100 different artworks × 1 piece**

다. 견적 요청 시 반드시 이 조건을 적는다.

## 3. 샘플 규격

### Memory Charm
- 50~60mm 후보
- 앞/뒤 서로 다른 이미지
- 자유형 아크릴
- 치비 + 사진 컬러 재현
- 긁힘 내구성

### Portal Charm
- 20~25mm 후보
- NABOM 브랜드
- NFC 태그/칩
- 금속링 간섭 테스트

## 4. 공급처 샘플링

동일한 소스 디자인 3종을 업체별로 주문한다.

테스트 디자인:
1. 밝은 피부 + 검은 머리
2. 어두운 사진 배경
3. 흰색/투명 경계가 많은 캐릭터

## 5. QA 점수표

### 인쇄
- 선명도
- 피부톤
- 검정 표현
- 사진 컬러
- 뒷면 가독성
- 재단 정밀도
- 스크래치
- 가장자리 마감

### 하드웨어
- 고리 내구성
- 체결
- 무게
- 모서리
- 가방 사용성

### NFC
- iPhone
- Samsung/Android
- 케이스 장착 상태
- 5회 반복 인식
- 인식 위치
- 금속 간섭
- QR fallback

각 항목 1~5점.

## 6. 공급처 선정 가중치 예시
- 인쇄품질 30
- 개인화 유연성 20
- 납기 15
- 가격 15
- 불량대응 10
- 주문 자동화 가능성 10

## 7. NFC 프로비저닝

NFC URL:
`https://nabom.ponslink.com/k/{opaque_token}`

사용자 ID를 직접 기록하지 않는다.

흐름:
```text
Order
→ Token 생성
→ NFC write
→ Read verification
→ User mapping
→ QC
→ Packaging
```

## 8. 출고 QA
- [ ] 주문자
- [ ] 앞면
- [ ] 뒷면
- [ ] 방향
- [ ] 고리
- [ ] NFC token
- [ ] 실제 Tap
- [ ] QR
- [ ] 계정 mapping
- [ ] 포장
- [ ] 배송라벨

## 9. 포장

FIRST 100에는 고급 박스를 만들지 않는다.
- 보호봉투
- NABOM 카드
- 완충 포장
- 외포장

해외 확장을 위해 **완전 포장 100g 이하**를 목표로 한다.

## 10. 분실/불량

### NFC 불량
Portal Charm만 교체.

### Memory 불량
개인화 파트만 재제작.

### 분실
기존 token revoke → 새 Portal token 발급.

## 11. 주문/제작 상태

이 문서에서는 단일 상태 enum을 정의하지 않는다.

결제, 커스터마이징, 생산, 배송, 디지털 활성화 상태는 서로 분리하며
**`11_ARCHITECTURE_SSOT/38_Canonical_State_Machines.md`를 SSOT로 사용한다.**

제조 운영 화면에서는 여러 sub-status를 조합해 하나의 제작 Kanban 단계로 보여줄 수 있다.

## 12. 수정 정책
- 첫 시안 포함
- 경미한 수정 1회 포함
- 완전 재제작은 별도 조건

무제한 수정 금지.

## 13. 원가 Tracking

주문별로 다음을 기록한다.
```text
판매가
Memory Charm
Portal/NFC
포장
배송
PG
Image AI
LLM
수정횟수
수작업 분
CS 분
불량여부
재제작비
기여이익
```
