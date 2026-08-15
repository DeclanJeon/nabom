---
doc_id: GOV-VERIFY-001
title: NABOM External Verification Register
version: 1.0
status: REQUIRED_BEFORE_LAUNCH
updated_at: 2026-08-11
---

# External Verification Register v1.0

## 목적

설계서에 적힌 외부 정책·법·수수료·API는 시간이 지나면 바뀐다.

따라서 아래는 문서에서 “고정 사실”로 취급하지 않고,
**출시/변경 직전에 최신 공식자료로 재검증**한다.

---

## Verification Items

| 영역 | 재검증 대상 | 시점 |
|---|---|---|
| 사업 | 통신판매업 신고/표시 | 국내 결제 오픈 전 |
| PG | 계약조건/수수료/해외결제 | PG 계약 전 |
| 소비자 | 주문제작/디지털 콘텐츠 취소 정책 | 약관 확정 전 |
| 개인정보 | 보존/국외처리/처리방침 | 출시 전 |
| 광고 | 이메일/SMS/Kakao 마케팅 동의 | 채널 활성화 전 |
| SmartStore | API/수수료/외부링크 정책 | 입점/연동 전 |
| idus | 판매/글로벌 정책 | 입점 전 |
| Etsy | 한국 판매/수수료/외부거래 정책 | 해외 판매 전 |
| Pinkoi | 수수료/판매자 정책 | 입점 전 |
| 배송 | K-Packet/EMS 요금/제한 | 가격표 확정 전 |
| 미국 | 관세/저가수입 | 미국 판매 전 |
| EU | GPSR/제품안전/책임자 | EU 판매 전 |
| 제조 | MOQ/단가/납기/파일규격 | 발주 전 |
| AI | 데이터 retention/training | provider 변경 전 |
| 폰트/Asset | 상업 라이선스 | 사용 전 |

---

## Evidence

검증 시:
- source
- checked_at
- owner
- conclusion
- affected docs/config

를 기록한다.

---

## 원칙

외부 조건이 바뀌어도 Product Architecture 전체가 무너지지 않도록
Provider/Channel/Country Adapter 방식으로 설계한다.
