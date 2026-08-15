---
doc_id: LEGACY-C443A37B0B
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 10_GROWTH_QUALITY_DESIGN/35_Service_Level_Capacity_Cost_Guardrails.md
---

# NABOM Service Level / Capacity / Cost Guardrails v1.0

## 1. 목적

매출이 늘수록 손실이 커지는 구조를 막는다.

---

## 2. 주문당 Guardrail

추적:
- COGS
- AI cost
- image cost
- payment fee
- channel fee
- packaging
- shipping subsidy
- manual design minutes
- CS minutes
- reprint cost

---

## 3. Capacity

매일:
- design slots
- proof slots
- production slots
- shipping slots

예상 출고일 계산에 사용.

---

## 4. SLA

예시 가설:
- asset review: 1 business day
- proof: 1~2 business days
- revision: 1 business day

실데이터로 조정.

---

## 5. Auto Pause

조건:
- backlog too high
- supplier delay
- stockout
- defect spike

특정 SKU 판매 일시중지 가능.

---

## 6. Margin Guard

채널/국가/상품별 최소 contribution margin 설정.

가격/할인 적용 후 기준 이하이면 경고.

---

## 7. AI Cost Guard

- per user/day
- per Weekly Mirror
- per Profile
- per custom image

budget threshold 초과 시 fallback model 또는 작업 제한을 검토.

사용자 품질을 몰래 크게 떨어뜨리지 않도록 정책화.

---

## 8. Dashboard

- orders backlog
- capacity utilization
- manual minutes
- AI cost/user
- margin/order
- defect/reprint
- SLA breach
