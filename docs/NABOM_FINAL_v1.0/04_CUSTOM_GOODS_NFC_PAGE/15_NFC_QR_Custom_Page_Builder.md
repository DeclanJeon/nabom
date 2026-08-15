---
doc_id: LEGACY-E2DB53ED36
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 04_CUSTOM_GOODS_NFC_PAGE/15_NFC_QR_Custom_Page_Builder.md
---

# NABOM NFC / QR 맞춤 페이지 주문제작 및 Builder 설계 v1.0

## 1. 목표

고객이 NFC 또는 QR을 통해 열리는 페이지를 별도 주문할 수 있게 한다.

두 가지 모드:

### Self Builder
고객이 템플릿을 선택해 직접 제작.

### Designer-assisted
내용을 제출하면 나봄이 제작.

---

# 2. 페이지 상품

## Link Page
가장 저렴.

- 프로필 이미지
- 제목
- 설명
- 버튼 1~10개
- SNS/URL

## Memory Page
- Cover
- Gallery
- Story
- Timeline
- Video
- Message

## Gift Page
- 받는 사람
- 공개일
- 편지
- 사진
- 음악 링크
- Surprise section

## Event Page
- 행사정보
- 날짜/장소
- Gallery
- Schedule
- Participants
- 후기

### Community Page
- 공동체 설명
- 단체사진
- 멤버
- 기록
- 링크

### Relationship Page
- 양쪽 동의된 공동 기억
- 메시지
- 회고 질문
- 함께할 작은 실험

분석 결과와 개인 Living Profile은 기본 포함하지 않는다.

### Group Memory Page
- 그룹의 공동 기록
- 공동 목표
- 기간별 타임라인
- 구성원 공개 메시지

개인별 민감 Trait와 일기는 aggregate-only 정책을 따른다.

### Reflection Gift Page / Growth Capsule
- 특정 기간의 회고
- 받는 사람에게 남기는 질문
- 다음 행동 또는 약속
- 사진·영상·메시지

## Custom
운영자 제작.

---

# 3. Builder UX

```text
Template
→ Basic Info
→ Blocks
→ Theme
→ Preview
→ URL/NFC
→ Publish
```

---

# 4. Block System

MVP block:

- Hero
- Text
- Image
- Gallery
- Button
- Link List
- Video Embed
- Timeline
- Quote
- Divider
- Profile Card
- Map Link
- Contact
- Footer

Phase 2:
- Guestbook
- Countdown
- RSVP
- Audio
- Poll
- Download File

---

# 5. 디자인

테마:
- Warm
- Minimal
- Forest
- Ivory
- Night
- Celebration

사용자 설정:
- Cover
- Accent
- Font pair
- Card radius
- Section visibility

초기에는 완전 자유 CSS 금지.

템플릿 기반으로 품질을 통제한다.

---

# 6. Page 상태

- DRAFT
- REVIEW
- PUBLISHED
- ARCHIVED
- SUSPENDED

Designer-assisted:
- CONTENT_REQUIRED
- DESIGNING
- PROOF_READY
- REVISION
- APPROVED
- PUBLISHED

---

# 7. URL

내부 페이지:

`nabom.ponslink.com/p/{slug}`

NFC/QR은 직접 page URL 대신 Resolver를 쓴다.

```text
/k/{token}
/q/{token}
```

Resolver 목적지:
- NABOM Page
- Living Profile
- External URL

사용자가 destination 변경 가능.

---

# 8. NFC/QR 상품

### Digital Only
QR code + Page.

### NFC Link Kit
NFC tag + Page.

### Page + Physical Product
키링/참 + Page.

### Existing NFC Setup
고객이 이미 가진 NFC에 사용할 URL/Page만 제공.

---

# 9. 주문제작 페이지 Intake Form

Designer-assisted 고객:

- 목적
- 누구를 위한 페이지
- 제목
- 설명
- 사진
- 영상
- 링크
- 원하는 분위기
- 공개일
- 참고 사이트
- 추가 요청

가격은 block/complexity에 따라 옵션화 가능.

---

# 10. Ownership

Page Owner와 Purchaser를 분리한다.

Gift:
Buyer가 구매.
Recipient가 Claim 후 owner.

Group:
Organizer owner.
Participant는 자신의 child page owner.

Relationship Page:
공동 소유자 목록은 양쪽의 승인된 `Relationship` participant로 제한한다.

Group Memory Page:
소유자는 `InsightGroup` subject이며, 활성 동의 구성원만 subject authorization을 통과할 수 있다. Organizer는 운영자일 수 있지만 구성원의 분석 데이터 소유자가 아니다.

소유권과 접근 권한은 별도 개념이다. `PageOwnership`은 소유·편집 주체를, `PageAuthorization`은 현재 공개 범위와 관계/그룹 동의 상태를 표현한다.

---

# 11. 개인정보/공개 범위

페이지별 visibility:

- PUBLIC
- UNLISTED
- PASSWORD
- OWNER_ONLY

페이지별 authorization:

- `public`
- `claimed_recipient`
- `consented_relationship_members`
- `active_insight_group_members`
- `owner_only`

이 값들은 `06_Core_JSON_Schemas.md`의 canonical enum과 동일하게 사용한다.

기본:
Gift/Memory = UNLISTED.

`UNLISTED`는 검색 노출을 막는 discoverability 설정일 뿐, 관계·그룹 구성원 인증을 대체하지 않는다. Relationship Page와 Group Memory Page는 resolver에서 로그인 주체, subject membership, 현재 `InsightConsent`를 확인한다.

동의 철회·관계 revoke·그룹 pause 시:

1. 새 페이지 접근과 분석 결과 생성을 즉시 중단한다.
2. 기존 published revision은 `SUSPENDED` access overlay를 적용한다.
3. NFC/QR token은 폐기하지 않아도 되지만 resolver는 허용 페이지가 없음을 반환한다.
4. audit event에 subject, actor, scope, reason, timestamp를 남긴다.

관계·그룹 페이지를 비로그인 방문자가 열면 민감 콘텐츠를 제공하지 않고 로그인/claim 안내만 표시한다.

검색엔진 index:
기본 OFF.

---

# 12. Analytics

페이지 소유자에게:

- Views
- Unique visitors
- NFC taps
- QR scans
- Button clicks
- Last viewed

정확한 위치 추적 등 과도한 추적은 기본 금지.

---

# 13. 만료

Digital Page는 가능한 한 영구 URL 유지가 이상적.

가격모델:
- Basic Page 구매 시 최소 장기 호스팅 포함
- 고급 기능/저장용량은 구독

페이지를 갑자기 삭제하면 물리 NFC 제품 가치가 사라지므로 URL 지속성을 핵심 약속으로 다룬다.

---

# 14. QR

QR generator:
- SVG
- PNG
- Error correction
- branded frame option

QR에는 redirect token URL 삽입.

목적지 변경 가능.

---

# 15. NFC Encoder Admin

운영 화면:

- Create token
- Assign product
- Assign order
- Assign page
- Test
- Activate
- Revoke
- Replace

출고시 `verified_at` 필수.


---

## Canonical URL Notice

- NFC: `/k/{token}`
- QR: `/q/{token}`
- Page: `/p/{slug}`

전체 URL 규칙은 `11_ARCHITECTURE_SSOT/39_Canonical_Routes_URLs.md`를 따른다.
