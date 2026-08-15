---
doc_id: OPS-PREPRESS-001
title: NABOM Production Asset and Prepress
version: 1.0
status: APPROVED_BASELINE
updated_at: 2026-08-11
---

# Production Asset / Prepress 설계 v1.0

## 1. 목적

“시안 승인”과 “실제 공장에 보내는 파일”을 분리한다.

---

## 2. Asset 종류

### Source Asset
고객 원본.

### Generated Asset
치비/편집 결과.

### Proof Asset
고객 승인용 화면.

### Production Asset
제작업체 제출용 최종 파일.

---

## 3. Production Asset 필드

- order_item
- product_variant
- supplier_profile
- template_version
- front_file
- back_file
- dimensions
- bleed
- cutline
- color_mode
- dpi
- generated_at
- checksum
- approved_proof_id

---

## 4. Supplier Profile

업체마다 요구 파일 규격이 다르므로:

```text
SupplierProductionProfile
- canvas size
- bleed
- cut line convention
- front/back convention
- file format
- color profile
- minimum resolution
```

으로 관리한다.

---

## 5. Print Validation

자동검증 후보:
- pixel dimensions
- DPI
- transparent margin
- missing asset
- wrong orientation
- front/back count
- file size

자동검증 통과 후에도 FIRST 100은 human QC 권장.

---

## 6. Proof vs Production

고객은 Proof를 승인한다.

운영자는 그 승인본을 기반으로 Production Asset을 생성한다.

Production Asset 생성 후 고객 원본이 바뀌면:
- 기존 asset invalid
- 재생성
- 필요 시 재승인

---

## 7. Version

Production Asset은 immutable.

수정 시 v2 생성.

출고된 제품이 어떤 asset version으로 제작됐는지 추적한다.

---

## 8. NFC/QR Production

QR:
- canonical `/q/{token}`
- minimum physical test
- contrast/quiet zone
- 실제 인쇄물 스캔 QC

NFC:
- `/k/{token}`
- write
- read-back verify
- physical item mapping
- verified_at

---

## 9. Batch Export

공급처 제출:
- file bundle
- order map
- quantity
- hardware option

PII는 공급처에 필요한 최소한만 제공한다.
