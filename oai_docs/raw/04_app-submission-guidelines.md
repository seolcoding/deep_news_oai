# Resources — App submission guidelines

- Source: https://developers.openai.com/apps-sdk/app-submission-guidelines
- Captured: 2025-12-22
- Note: condensed capture (요구사항/체크리스트 중심)

## Overview
- ChatGPT 앱 생태계는 **신뢰(trust)** 기반: 안전/유용/프라이버시 존중, 그리고 공정/투명한 심사.
- 제출 전 기반 문서로 **UX principles**, **UI guidelines**를 먼저 읽을 것을 권장.

## App fundamentals
### Purpose and originality
- 명확한 목적 + 약속한 기능을 안정적으로 수행.
- ChatGPT 기본 대화 기능만으로는 제공하기 어려운 **고유 워크플로우/기능**을 제공해야 함.
- IP/저작권 준수, 오해/사칭/스팸/카피캣/의미없는 정적 프레임 금지.
- OpenAI가 만들거나 보증하는 것처럼 암시 금지.

### Quality and reliability
- 예측 가능/신뢰 가능한 동작, 입력에 대한 정확/관련성.
- 에러는 명확한 메시지/대체 동작으로 핸들링.
- 제출 전 폭넓은 시나리오에서 테스트(지연/응답성/안정성). 데모/트라이얼 수준은 거절.

### App name, description, screenshots
- 이름/설명은 명확/정확/이해하기 쉬워야 함.
- 스크린샷은 실제 기능을 정확히 반영 + 요구 규격 준수.

## Tools (MCP tools)
- MCP 도구는 ChatGPT가 앱을 사용하는 “매뉴얼” 역할 → 정의가 명확할수록 안전/신뢰/심사 속도 향상.

### Clear and accurate tool names
- 사람에게 읽히는 구체적 이름(행동을 나타내는 동사 형태 권장: `get_order_status`).
- 앱 내에서 유일해야 함.
- 오해 소지/과장/비교/선동 표현 금지(`pick_me`, `best`, `official` 등).

### Descriptions that match behavior
- 목적을 정확히 설명.
- 다른 앱/서비스를 깎아내리거나 “선택해달라” 유도 금지.
- 과도한 트리거링 유도(광범위한 오발동) 금지.
- 설명이 불명확/불완전하면 거절 사유.

### Correct annotation
- `readOnlyHint`, `openWorldHint`, `destructiveHint` 등을 정확히 설정(오류/누락은 흔한 거절 사유).
- 외부 시스템/계정/공개 플랫폼/공개 콘텐츠 생성은 `openWorldHint`로 명시.

### Minimal and purpose-driven inputs
- 필요한 최소 정보만 요청.
- 전체 대화기록/원문 로그/광범위 컨텍스트를 “혹시 몰라서” 요청 금지.
- 위치가 필요하면 시스템의 거친 위치 신호에 의존(정밀 GPS/주소 요청 금지).

### Predictable, auditable behavior
- 이름/설명/입력에 맞게 동작.
- 부작용(side effects)을 숨기지 말 것.
- 재시도 시 중복 효과가 생길 수 있으면 명확히.

## Authentication and permissions
- 인증이 필요하면 흐름이 투명/명시적이어야 하고, 권한 요청은 최소로 제한.
- 심사용 **데모 계정(샘플 데이터 포함)** 제공 필수. 가입 강제/접근 불가 2FA 등 추가 장벽은 거절.
## Commerce and monetization
- 현재 **물리적 상품(physical goods)**에 한해 커머스 허용.
- 디지털 상품/서비스(구독, 디지털 컨텐츠, 토큰/크레딧 등) 판매는 직접/간접 모두 불가.

### Prohibited goods (요약)
- 성인물/성서비스, 도박, 불법/규제 약물 및 관련 용품
- 처방/연령 제한 의약품
- 불법/위조/도난/사기 도구, 해적판/크랙 도구
- 악성코드/스파이웨어/감시 도구, 담배/니코틴
- 무기/폭발물/유해 물질 및 극단주의 상품/선전

### Prohibited fraudulent, deceptive, or high-risk services (요약)
- 위조문서/가짜 ID, 신용조작/채무조정 사기
- 부정/남용 소지가 큰 금융 서비스 및 거래 실행(송금/투자/암호화폐 전송 등)
- 정부 서비스 악용, 신원 도용/사칭, 소비자 기만형 크립토/NFT
- 동의 회피 결제/텔레마케팅, 고차지백/사기성 여행 서비스 등

### Checkout
- 결제는 **외부 체크아웃(자사 도메인)** 유도 방식이 기본.
- 앱 내부에 제3자 체크아웃을 임베드/호스팅하는 방식은 불가.

### Advertising
- 광고를 제공하면 안 되며, 앱의 주목적이 광고여서도 안 됨(독립적 가치 제공 필수).

## Safety
- OpenAI usage policies 위반 활동을 유도/지원하면 안 됨.
- 일반 аудит 기반(13–17 포함) 적합해야 하며, 13세 미만 타깃 금지.
- 사용자 의도와 무관한 리다이렉트/무관 콘텐츠 삽입/불필요한 데이터 수집 금지.
- **Fair play**: 모델 선택을 조작(“이 앱을 우선 사용” 등)하거나 다른 앱을 방해하는 메타/설명/주석 금지.
- **Third-party integrations**: 허가 없는 스크래핑/약관 위반/제한 우회 금지.
- **Iframes**: `frame_domains`는 꼭 필요할 때만(IDE/노트북 등). 공개 배포 심사에서 추가 검토/거절 가능성이 큼.

## Privacy
- 공개된 프라이버시 정책 필수(수집 데이터 범주/목적/수신자/통제수단).
- **Collection minimization**: 입력 스키마는 최소·좁은 범위.
- **Response minimization**: 응답도 목적 관련 데이터만(진단/텔레메트리/불필요 ID 등 금지).
- **Restricted Data** 수집/처리 금지(PCI/PHI/정부식별자/인증 비밀값 등).
- 풀 채팅 로그 추출/재구성/추론 금지(의도적으로 제공된 스니펫/리소스만 사용).

## Developer verification / Submitting
- 제출자는 검증(verified)된 개인/조직이어야 함.
- 지원 연락처 제공 필수.
- Owner 권한이 대시보드에서 제출 가능. 앱별 리뷰는 동시에 1버전.
