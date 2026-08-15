---
doc_id: LEGACY-84C53F2A6A
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 09_FULFILLMENT_SUPPORT_B2B/27_Inventory_Procurement_Fulfillment.md
---

# NABOM Inventory / Procurement / Fulfillment 설계 v1.0

## 1. 목적

나봄은 주문제작이지만 재고·발주·생산능력이 존재한다.

---

## 2. Material

예:
- NFC tag
- Portal blank
- acrylic
- ring
- connector
- pouch
- card
- envelope

필드:
- sku
- supplier
- unit_cost
- lead_time
- safety_stock
- reorder_point

---

## 3. BOM

ProductVariant → 필요한 Material 수량.

예:
```text
Duo Charm
- Memory Charm x1
- Portal Charm x1
- Ring x1
- Pouch x1
- Card x1
```

---

## 4. Inventory Transaction

- RECEIVE
- CONSUME
- ADJUST
- DEFECT
- SCRAP
- RETURN_TO_VENDOR

재고를 숫자 overwrite하지 않고 movement로 기록한다.

---

## 5. Supplier

- primary
- secondary
- MOQ
- lead_time
- unit_price
- defect_rate
- contact
- payment terms

공급처별 샘플/품질 점수와 연결.

---

## 6. Purchase Order

```text
DRAFT
PLACED
PARTIALLY_RECEIVED
RECEIVED
CANCELLED
```

입고 시 실제 원가를 업데이트.

---

## 7. Production Capacity

일별:
- 디자인 capacity
- proof capacity
- assembly capacity
- QC capacity

주문량이 capacity를 넘으면 상품페이지 예상 출고일을 늘리거나 주문을 pause.

---

## 8. Production Batch

Batch:
- supplier lot
- print order
- date
- operator
- products
- QC

문제 발생 시 해당 batch 고객 검색 가능.

---

## 9. Shipment

상태:
```text
ADDRESS_REVIEW
LABEL_CREATED
PICKED_UP
IN_TRANSIT
DELIVERED
DELIVERY_FAILED
LOST
RETURN_TO_SENDER
RETURN_RECEIVED
RESHIPPED
```

---

## 10. Split Shipment

한 주문에서:
- 일부 상품 선출고
- 공동구매 개별 배송
- replacement 별도 출고

Shipment와 Order를 1:N으로 설계한다.

---

## 11. 주소검증

MVP:
우편번호/주소 검색 + 사용자 확인.

해외:
국가/주/우편번호 형식 검증.

출고 이후 주소변경은 carrier 정책에 따름.

---

## 12. Supplier Failure

- 대체 공급처
- 품절 자재
- 납기 지연
- 대체 부품 승인
- 고객 공지

critical material은 single-source 의존도를 기록한다.

---

## 13. Fulfillment Admin

- 오늘 제작
- 자재 부족
- 발주 필요
- 생산 지연
- QC 실패
- 배송 실패
- replacement
