---
doc_id: LEGACY-60ED173C93
package_version: 1.0
status: BASELINE_IMPORTED
updated_at: 2026-08-11
source_path: 09_FULFILLMENT_SUPPORT_B2B/30_Account_Guest_Checkout_Gift_Ownership.md
---

# NABOM Account / Guest Checkout / Gift Ownership 설계 v1.0

## 1. 목표

구매를 위해 불필요한 회원가입을 강제하지 않되,
NFC/페이지/Living Service 사용권은 안전하게 계정에 연결한다.

---

## 2. Guest Checkout

자체몰 Physical Product:
비회원 구매 허용 후보.

필수:
- email/phone
- order lookup token
- delivery info

Digital-only / Subscription:
계정 필요를 권장.

---

## 3. Guest → Account Claim

구매 후:
`주문을 계정에 연결하기`

- 주문 이메일 검증
- one-time claim link
- 이미 다른 계정에 연결된 경우 보호

---

## 4. Account Merge

소셜로그인/이메일 중복 시:
- identity verification
- orders/pages/NFC merge
- duplicate subscription 처리

자동 merge 금지.

---

## 5. Gift Roles

### Purchaser
돈을 냄.

### Recipient
제품/페이지를 소유.

### Viewer
공개/초대 페이지를 봄.

Purchaser가 Recipient의 private journal/profile을 볼 권리는 없다.

---

## 6. Gift Claim

```text
Order
→ Gift Token
→ Recipient Tap/QR
→ Claim
→ Account
→ Ownership Transfer
```

claim:
- expiry
- resend
- wrong claim report
- recovery

---

## 7. Ownership Transfer

NFC/Page는 상황에 따라 이전 가능.

- gift
- resale? 기본 미지원
- organizer → participant

민감한 Living Profile은 자동 이전 금지.

---

## 8. Account Deletion

active:
- order
- subscription
- claim
- refund

상태를 확인 후 삭제 흐름.

거래기록과 개인기록의 처리 분리.

---

## 9. Authentication UX

- 이메일
- Google/Apple/Kakao/Naver 후보
- 비밀번호 없는 magic link 후보

MVP는 인증 복잡도를 낮추되 계정 복구가 쉬워야 한다.
