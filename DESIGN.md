# Design

## Source of truth
- Status: Active
- Last refreshed: 2026-08-12
- Primary product surfaces: 인증·온보딩, 오늘의 나, Profile 001, Weekly Mirror, Journey, 관계·그룹, 설정·개인정보, NFC 진입
- Evidence reviewed: `.omx/ultragoal/brief.md`; `NABOM_FINAL_v1.0/01_BRAND_PRODUCT/01_NABOM_PRD.md`; `NABOM_FINAL_v1.0/11_ARCHITECTURE_SSOT/39_Canonical_Routes_URLs.md`; `NABOM_FINAL_v1.0/10_GROWTH_QUALITY_DESIGN/34_Design_System_Accessibility_SEO.md`; `frontend-ui/01_onboarding.html`; `frontend-ui/02_profile_001.html`; `frontend-ui/03_today.html`; approved references under `output/imagegen/corrected/` and `output/imagegen/mobile/`.
- Evidence boundary: This foundation records observed product and visual constraints. It does not claim production API behavior, final copy, or final artwork where the reviewed materials do not specify them.

## Brand
- Personality: 차분하고 따뜻한 자기관찰, 오래 기록할수록 선명해지는 감각, 단정하지만 인간적인 한국어 서비스.
- Trust signals: 기록과 가설을 구분하는 문장, 사용자가 확인·수정하는 피드백, 공개 범위의 명시, 처리 상태의 투명성.
- Avoid: 점괘처럼 단정하는 성격 판정, 의료·법률·재무·치료·관계 운명 주장, 과장된 AI 권위, 상업 화면의 우선 노출, 레퍼런스 PNG를 배경이나 UI 오버레이로 사용하는 방식.

## Product goals
- Goals: 짧은 기록을 꾸준히 남기고, 시간에 따라 변하는 Living Profile을 스스로 확인하며, 주간 거울과 작은 실험으로 다음 행동을 선택하게 한다.
- Non-goals: 이 foundation slice에서 상세 코어 화면, 결제·상품·장바구니·그룹구매, 실제 분석 API, 계정 인증, 생산용 데이터 저장을 구현하지 않는다.
- Success signals: 주요 생활 서비스 route가 같은 AppShell에서 도달 가능하고, 모바일·태블릿·데스크톱에서 읽기와 조작이 안정적이며, 주요 상태와 개인정보 경계가 이후 구현의 기준으로 남는다.

## Personas and jobs
- Primary personas: 자기 관찰을 시작하려는 성인 사용자; 여러 기록을 쌓아 자신의 변화 패턴을 확인하려는 사용자.
- User jobs: 오늘의 상태를 30초~3분 안에 남기기, 초기 프로필을 참고하되 직접 맞는지 확인하기, 지난 기록과 이번 주의 흐름을 안전하게 돌아보기.
- Key contexts of use: 하루 중 짧은 모바일 체크인, 집이나 책상에서의 데스크톱 회고, 관계·그룹 화면에서 공개 범위를 확인하는 순간.

## Information architecture
- Primary navigation: 오늘의 나 `/today`; 내 프로필 `/profile`; Weekly Mirror `/mirror`; 나의 여정 `/journey`; 관계 `/relationships`; 그룹 `/groups`; 설정 `/settings`.
- Core routes/screens: `/login`, `/signup`, `/recovery`, `/onboarding`, `/today`, `/journal`, `/profile`, `/mirror`, `/journey`, `/relationships`, `/groups`, `/settings`, `/settings/privacy`, `/settings/nfc`, `/method`, `/report`.
- Content hierarchy: 현재 화면의 목적과 상태를 먼저 제시하고, 사용자가 해야 할 한 가지 행동을 분명히 하며, 설명·근거·개인정보 범위는 그 다음에 배치한다. 상세 화면은 이후 stories에서 확장한다.

## Design principles
- 기록이 판단보다 앞선다: 관찰·가설·사용자 확인을 구분하고 확정적 표현을 피한다.
- 한 번에 한 걸음: 화면마다 주 행동 하나를 강조하고 나머지는 보조 행동으로 둔다.
- 조용한 대비: 한지 아이보리와 깊은 남색을 바탕으로 동·주홍·옥색을 의미가 있을 때만 사용한다.
- Tradeoffs: 장식보다 읽기와 조작을 우선한다. 모바일에서는 데스크톱을 축소하지 않고 정보 순서와 고정 행동을 다시 구성한다. 초기 정적 prototype은 실제 데이터보다 route·상태·컴포넌트 계약을 명확히 한다.

## Visual language
- Color: 한지 아이보리 `#f6efe0`를 기본 표면, 깊은 남색 `#0b1828`을 shell, 동색 `#c9a84c`를 활성·강조, 주홍 `#c04030`을 주요 행동, 옥색 `#5a8a72`를 긍정·동의 상태에 사용한다. 잉크·보조 텍스트·선·표면은 shared.css 토큰에서만 관리한다.
- Typography: 한국어 본문은 시스템 산세리프 스택, 섹션 제목과 브랜드 표기는 한국어 세리프 스택을 사용한다. 본문 최소 크기와 줄간격은 작은 화면의 읽기를 우선한다.
- Spacing/layout rhythm: 4px 기반 간격 토큰과 넉넉한 여백. 데스크톱은 side rail + content column, 태블릿은 축소 rail/top bar, 모바일은 top bar + bottom navigation + 단일 column.
- Shape/radius/elevation: 종이 표면은 낮은 radius, interactive control은 중간 radius, 카드와 shell은 얕은 그림자와 1px 선으로 계층을 만든다. 장식용 둥근 카드 중첩은 피한다.
- Motion: 짧은 opacity/transform 전환만 사용하며 정보 이해를 방해하지 않는다. `prefers-reduced-motion`에서는 즉시 전환한다.
- Imagery/iconography: 외부 이미지 없이 CSS 종이결과 inline SVG 선·도형 모티프를 사용한다. 아이콘은 의미를 보조할 때만 쓰며 텍스트 라벨을 대체하지 않는다.

## Components
- Existing components to reuse: 기존 HTML에는 공통 컴포넌트가 없으므로 기존 세 페이지의 브랜드명, 한지·남색·동색·주홍 톤과 카드/필드 패턴을 shared.css 토큰으로 통합한다.
- New/changed components: `AppShell`, `SideRail`, `TopBar`, `MobileNav`, `Button`, `Card`, `Field`, `Badge`, `StatePanel`, `PaperMotif`, `RoutePlaceholder`.
- Variants and states: 버튼 primary/secondary/ghost; 카드 default/quiet; field normal/invalid/disabled; 상태 loading/empty/error/success/offline; navigation active/focus. 이후 코어 stories는 이 계약을 확장한다.
- Token/component ownership: 모든 색·간격·타이포그래피·radius·shadow·motion·breakpoint는 `frontend-ui/shared.css`의 `:root` 토큰과 컴포넌트 규칙이 소유한다. 페이지는 토큰을 재정의하지 않는다.

## Accessibility
- Target standard: semantic HTML과 WCAG 계열 실용 권고를 기준으로 한다. 검토 문서가 명시한 label, keyboard, focus, contrast, alt, error text, touch target, reduced motion을 foundation에 반영한다.
- Keyboard/focus behavior: skip link, 논리적 문서 순서, 모든 링크·버튼·필드의 `:focus-visible` ring, 키보드로 모든 route와 control 도달을 제공한다.
- Contrast/readability: shell의 밝은 텍스트와 종이 표면의 어두운 텍스트를 분리하고, 보조색만으로 상태를 전달하지 않는다. 작은 본문은 충분한 줄간격을 둔다.
- Screen-reader semantics: `header`, `nav`, `main`, `aside`, `section`, `form`, `label`, `aria-current`, `aria-live`를 의미에 맞게 사용한다. 장식 SVG는 `aria-hidden`으로 둔다.
- Reduced motion and sensory considerations: `prefers-reduced-motion: reduce`에서 모든 전환·스크롤 동작을 줄이고, 색·모션 없이도 상태를 문장과 구조로 파악할 수 있게 한다.

## Responsive behavior
- Supported breakpoints/devices: 1536×1024 desktop, 1280×720 desktop, 1024×1366 tablet, 390×844 mobile, 360×800 compact mobile. CSS breakpoints are 1200px, 900px, 640px.
- Layout adaptations: 1200px 이상은 고정 side rail과 넓은 content; 900–1199px은 좁은 rail과 top context; 640–899px은 top bar 중심; 640px 미만은 단일 column과 bottom navigation으로 재구성한다.
- Touch/hover differences: 모바일 control은 최소 44px hit area와 hover 없는 pressed/focus 상태를 갖는다. 데스크톱 hover는 보조 피드백일 뿐 핵심 의미를 대체하지 않는다.

## Interaction states
- Loading: `aria-live` 상태 문장과 skeleton-like neutral blocks로 처리하며, 이후 데이터 연결 시 같은 `StatePanel` 계약을 사용한다.
- Empty: 현재 비어 있는 이유와 시작할 수 있는 다음 행동을 함께 보여준다.
- Error: 무엇이 실패했는지 짧게 말하고 retry 또는 돌아가기 행동을 제공한다.
- Success: 저장·동의·완료 결과를 문장으로 확인하고 다음 위치를 안내한다.
- Disabled: 비활성 이유를 label 또는 설명으로 제공하고 색만으로 구분하지 않는다.
- Offline/slow network, if applicable: 네트워크가 느리거나 끊긴 상태임을 숨기지 않고 마지막으로 확인된 기록과 재시도 행동을 안내한다. 실제 오프라인 저장은 이후 구현 범위다.

## Content voice
- Tone: 존댓말을 기본으로 하되, 가까이 관찰하는 차분한 1인칭·2인칭 한국어. 짧고 구체적으로 쓴다.
- Terminology: 나봄, 오늘의 나, 기록, 근거, 가설, 피드백, Weekly Mirror, 나의 여정, 공개 범위. `Profile 001`은 버전 표기로 유지한다.
- Microcopy rules: 불확실하면 불확실하다고 말하고, 사용자가 확인·수정·삭제할 수 있음을 알린다. “당신은 반드시…” 같은 결정론적 표현과 평가받는 느낌의 문구를 쓰지 않는다.

## Implementation constraints
- Framework/styling system: dependency 없는 static HTML/CSS/JavaScript. `frontend-ui/index.html`의 작은 history/hash fallback router와 기존 entry HTML이 shared.css를 직접 사용한다.
- Design-token constraints: token은 shared.css 한 곳에만 둔다. 색·간격·타이포그래피에 페이지별 inline system을 만들지 않는다. reference PNG는 배경·overlay로 사용하지 않는다.
- Performance constraints: 외부 font/CDN·런타임 dependency 없이 첫 화면 DOM을 작게 유지하고, 장식은 inline SVG/CSS로 한정한다.
- Compatibility constraints: file hosting과 단순 static server에서 route 링크가 작동해야 하며, 직접 진입 시 pathname과 hash를 모두 읽는다. safe-area inset을 지원하고 360px 폭에서 가로 overflow를 만들지 않는다.
- Test/screenshot expectations: 이후 verification story에서 1536×1024, 1280×720, 1024×1366, 390×844, 360×800 브라우저 smoke 및 route/state 전환을 확인한다. 이 foundation slice에서는 프로젝트 테스트·린터·포맷터를 실행하지 않는다.

## Open questions
- [ ] 실제 계정·API 연결 시 정적 placeholder 상태를 어떤 서버 상태 모델에 매핑할지 / product+engineering / core stories 전 영향
- [ ] 최종 브랜드 서체와 실제 생성 이미지 사용 범위를 확정할지 / brand / visual polish 전 영향
- [ ] 인증된 사용자의 기본 landing route와 localStorage/session 복원 정책 / product+engineering / router 전 영향
