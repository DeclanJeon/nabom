---
doc_id: LEGACY-1950A280FA
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 02_BUSINESS_STRATEGY/12_90Day_Execution_Plan.md
---

# NABOM 90일 실행계획 v1.0

대상: 1인 운영, 사업 초보, 개발 가능.

## 90일 목표
- 유료 FIRST 100 검증
- 제조/배송/CS 체계
- 자체몰/PG
- Weekly Mirror 가치 검증
- 국내 채널 확립
- 일본 테스트 준비

# Week 1: 팔 수 있는 실물을 만든다

### Day 1
- Memory Charm 샘플 디자인 3종
- 국내 제작처 3곳 샘플 주문

### Day 2
- Portal Charm 디자인
- NFC token endpoint 구현
- QR fallback

### Day 3
- PG 신청 준비
- 사업자/정산 서류

### Day 4
- 약관/개인정보/주문제작 정책 초안
- 통신판매업 제출사항 확인

### Day 5
- 포장재
- 브랜드 카드

### Day 6
- Landing 개발

### Day 7
- 샘플/사이트 QA

**주간 목표: 실제 돈을 받을 수 있는 상품 구조**

# Week 2: Commerce MVP

필수:
- `/`
- `/product`
- `/order`
- `/order/{id}`
- 사진 업로드
- 결제
- 주문조회
- 디자인 승인
- Admin
- NFC mapping

**완료조건: 실제 결제 1건 end-to-end.**

# Week 3: 내부 사용자 5명

실제 주문 흐름 그대로 테스트.

측정:
- 이미지 제작시간
- 수정시간
- Manual Minutes
- 인쇄
- NFC
- 포장
- Activation
- Profile
- Daily Entry

주말에 문제 10개를 뽑아 고친다.

# Week 4: FIRST 10

유료로 판매.

실행:
- Reels/TikTok/Shorts
- SmartStore/idus 준비
- 고객 인터뷰

FIRST 10 전 광고비 대규모 지출 금지.

# Month 2: FIRST 100

매주:
- 콘텐츠 5~7개
- B2B 리드 접촉
- 주문/제작/배송
- 인터뷰
- 비용/퍼널 분석

측정:
- CAC
- COGS
- Manual Minutes
- Activation
- Day 7
- Weekly Mirror

## Decision Gate

초기 목표:
- Profile completion ≥ 80%
- Day 7 ≥ 40%
- Weekly Mirror Open ≥ 70%
- Mirror 사용자 Next-week Return ≥ 50%

미달이면 새 기능을 추가하기보다 이탈원인을 먼저 수정한다.

# Month 3: 최적화 + 일본 준비

### 제조
- 공급처 1~2곳 선정
- 대량/개인화 견적

### 자동화
- 인쇄파일 합성
- 주문서
- NFC token
- 배송라벨
- AI cost logging

### 국내
- B2B 첫 계약 목표
- Gift 가격 테스트

### 일본
- 일본어 Landing
- 사용자 인터뷰 5~10명
- Charm vs Stand 테스트
- 실제 국제배송 몇 건 테스트

# 매일 운영 리듬 예시

### 오전
주문/CS/제조.

### 낮
개발/자동화.

### 오후
영업 10~20개 + 콘텐츠.

### 저녁
데이터와 고객피드백 정리.

# 매주 CEO Review
1. 몇 개 팔았나?
2. 어디서 왔나?
3. 왜 샀나?
4. 진짜 원가는?
5. 내 시간이 얼마나 들었나?
6. 어디서 이탈했나?
7. Weekly Mirror가 새 가치를 줬나?
8. 다음 주 개선 1개는?

# 하지 않을 것
- FIRST 10 전에 재고 대량생산
- FIRST 100 전에 기능 폭증
- 검증 없이 전세계 동시진출
- 무제한 수정
- 무료배송 남발
- 초기에 대규모 광고
- 가격만으로 제조처 결정


---

# v1.0 판매채널 실행 수정안

## Week 1~2
자체 PG보다 SmartStore 오픈을 우선할 수 있다.

- SmartStore 판매자 설정
- 대표 상품 등록
- 주문제작 안내
- idus 입점 검토
- NABOM 사이트에는 브랜드/Activation UX 구현

## Week 3
SmartStore 실제 결제 주문을 NABOM 내부 주문으로 수동 등록하여 제작 workflow 테스트.

## Week 4
FIRST 10의 결제는 SmartStore 또는 자체 PG 중 준비가 먼저 끝난 채널을 사용한다.

핵심:
결제 기술이 FIRST 10을 지연시키지 않는다.

## Month 2
반복 판매 확인 후:
- Naver Commerce API
- Unified Order Hub
- Direct Checkout
순으로 자동화한다.

## Month 3
Etsy listing을 이용한 해외 유료 주문 테스트.
해외 Direct Checkout은 marketplace 결과를 본 뒤 개발한다.
