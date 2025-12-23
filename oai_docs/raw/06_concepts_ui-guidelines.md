# Concepts — UI guidelines

- Source: https://developers.openai.com/apps-sdk/concepts/ui-guidelines
- Captured: 2025-12-22
- Note: long page → condensed capture (구조/규칙 위주)

## Section outline
- Overview
- Design system
- Display modes
  - Inline
    - Inline card
    - Inline carousel
  - Fullscreen
  - Picture-in-picture (PiP)
- Visual design guidelines
  - Why this matters
  - Color
  - Typography
  - Spacing & layout
  - Icons & imagery
  - Accessibility

## 핵심 요지
- 앱은 대화 흐름을 깨지 않으면서, 카드/캐러셀/풀스크린/PiP 등 **표준 display mode**로 ChatGPT UI에 통합됨.
- 시각 디자인은 “브랜드 표현”보다 **명료성/일관성/접근성**이 우선.

## Design system
- ChatGPT에 네이티브하게 보이도록 [Apps SDK UI](https://openai.github.io/apps-sdk-ui/) 디자인 시스템을 활용 가능(필수는 아님).
- Tailwind 기반, CSS 변수 토큰, 접근성 고려 컴포넌트 제공.
- 초기 디자인은 Figma 컴포넌트 라이브러리에서 시작 권장.
## Display modes
### Inline
- 대화 흐름 속에 직접 나타나는 모드. **모델 응답보다 먼저** 나타남. 모든 앱은 기본적으로 inline에서 시작.
- 구성 요소(권장)
  - **Icon & tool call**: 앱 이름/아이콘 라벨
  - **Inline display**: 카드/캐러셀 등 경량 위젯
  - **Follow-up**: 위젯 뒤에 붙는 짧은 모델 응답(중복 설명은 피하기)

#### Inline card
- 목적: 빠른 확인/단순 액션/시각적 요약
- When to use
  - 단일 결정(예약 확인)
  - 적은 양의 구조화 데이터(맵/주문요약/상태)
  - 완전 자급자족 위젯(오디오 플레이어 등)
- Layout / rules of thumb
  - **Primary action은 최대 2개**(1 primary + 1 secondary)
  - 카드 안에 **깊은 내비게이션/다중 뷰 금지**(탭/드릴다운 등)
  - **중첩 스크롤 금지**(콘텐츠에 맞춰 높이 자동 확장)
  - ChatGPT 기능을 **중복 구현 금지**

#### Inline carousel
- 목적: 여러 옵션을 좌우 스캔/선택
- Rules of thumb
  - **3–8개 아이템** 권장
  - 메타데이터는 핵심만(텍스트 2–3줄 이내)
  - 각 아이템은 **가능하면 단일 CTA**
  - 카드 간 시각적 계층(위계) 일관 유지

### Fullscreen
- 목적: 카드로 표현하기 어려운 리치/멀티스텝 경험(탐색형 맵, 편집 캔버스, 인터랙티브 다이어그램 등)
- 특징: 풀스크린에서도 **시스템 composer는 항상 존재** → “대화로 앱을 계속 조작”할 수 있어야 함
- Rules of thumb
  - 시스템 composer와 함께 동작하도록 UX 설계
  - 네이티브 앱을 그대로 복제하지 말고, 대화 기반 경험을 확장하는 용도로 사용

### Picture-in-picture (PiP)
- 목적: 게임/영상/라이브 세션처럼 대화와 병렬로 지속되는 경험
- Rules of thumb
  - composer 입력에 반응/업데이트 가능해야 함
  - 세션 종료 시 PiP 자동 종료
  - 컨트롤 과다/정적 콘텐츠 과다 금지
## Visual design guidelines
### Color
- 시스템 컬러를 텍스트/아이콘/구조 요소에 사용(일관성 유지)
- 브랜드 컬러는 **accent/버튼/배지** 수준으로 제한
- 커스텀 그라데이션/패턴으로 미니멀 룩 훼손 금지

### Typography
- 시스템 폰트 스택 상속(SF Pro/Roboto 등), 가독성과 접근성 우선
- 커스텀 폰트 사용 금지(풀스크린 포함)
- 폰트 크기 변형 최소화(가능하면 body/body-small 중심)

### Spacing & layout
- 일관된 패딩/마진/정렬로 스캔 가능성 유지
- 시스템 그리드/코너 라운드 등 가이드 존중
- 헤드라인→보조텍스트→CTA 순으로 명확한 위계

### Icons & imagery
- 시스템 아이콘 또는 ChatGPT 세계관과 맞는 단색/아웃라인 스타일 권장
- 로고를 응답/콘텐츠 자체에 넣지 말 것(호스트가 앱명/로고를 자동 표시)
- 이미지 비율 준수(왜곡 방지)

### Accessibility
- WCAG AA 대비 준수
- 모든 이미지에 alt text 제공
- 텍스트 리사이즈에서도 레이아웃이 깨지지 않게 설계
