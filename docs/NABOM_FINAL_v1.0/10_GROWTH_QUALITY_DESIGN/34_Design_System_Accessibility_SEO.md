---
doc_id: LEGACY-E551FB064F
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 10_GROWTH_QUALITY_DESIGN/34_Design_System_Accessibility_SEO.md
---

# NABOM Design System / Accessibility / SEO 설계 v1.0

## 1. 목적

페이지별 디자인이 제각각 되지 않도록 쇼핑몰/나봄서비스/Page Builder의 공통 UI 기준을 둔다.

---

## 2. Design Tokens

- color
- typography
- spacing
- radius
- shadow
- motion
- breakpoints

브랜드:
아이보리/웜톤 기반, NABOM의 따뜻한 자기기록 톤 유지.

---

## 3. Core Components

- Button
- Input
- Select
- Upload
- Card
- ProductCard
- Price
- Badge
- Stepper
- Modal
- Toast
- Empty
- Error
- Skeleton
- Tabs
- Drawer

Customization:
- AssetUploader
- ProofViewer
- RevisionForm
- ProductPreview

---

## 4. Responsive

모바일 우선.

특히:
- 상품상세 sticky CTA
- upload
- proof zoom
- checkout
- group participant flow
- NFC activation

을 작은 화면에서 먼저 검증.

---

## 5. Accessibility

목표:
WCAG 계열 권고를 참고해 실용적 접근성 확보.

- semantic HTML
- label
- keyboard
- focus
- contrast
- alt
- error text
- touch target
- reduced motion

---

## 6. SEO

Public commerce:
- title/meta
- canonical
- sitemap
- robots
- OpenGraph
- Product structured data
- Breadcrumb
- locale hreflang

Private/Unlisted:
- noindex
- no sitemap

---

## 7. Page Builder SEO

Memory/Gift Page 기본:
`noindex`

Event/Public marketing page:
소유자가 공개 index를 선택할 수 있는 기능은 Phase 2.

---

## 8. Loading/Error/Empty

모든 주요 화면에:
- loading
- empty
- error
- retry
- offline-ish guidance

정의.

---

## 9. Content Style

- 단정적 성격판정 금지
- 제작상태는 명확
- 환불/승인/마감 문구는 모호하지 않게
