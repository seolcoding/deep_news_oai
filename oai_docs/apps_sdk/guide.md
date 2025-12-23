# Apps SDK 종합 가이드

이 문서는 공식 Apps SDK 문서를 기반으로, 앱을 **기획(유스케이스) → 도구/위젯 설계 → 서버 구현(MCP) → 배포/운영 → 메타데이터 튜닝 → 심사/정책 준수** 흐름으로 재구성한 내부 가이드입니다.

## 1) 큰 그림: ChatGPT App의 3요소
Apps SDK 앱은 아래 3개가 맞물려 동작합니다.

- **MCP server**: 도구 정의, 인증/권한, 데이터 반환, UI 템플릿(위젯) 연결
- **Widget/UI bundle**: ChatGPT 내 sandboxed iframe에서 렌더링되는 UI
- **Model**: 어떤 도구를 언제 호출할지 선택하고, `structuredContent`를 읽어 사용자에게 서술

핵심은 “서버·UI·모델의 책임 경계(boundary)”를 명확히 유지하는 것입니다.

## 2) Use case부터 시작하는 이유(Discovery는 모델이 한다)
ChatGPT에서 앱 발견(도구 선택)은 **모델이 메타데이터/설명/사용 이력/프롬프트 맥락**을 기반으로 결정합니다.
따라서 구현에 앞서 아래를 먼저 정리해야 합니다.

- **사용자 작업(Job-to-be-done)**: 사용자가 달성하려는 결과를 한 문장으로 정의
- **Direct / Indirect / Negative prompts**: 유스케이스별 “정답 프롬프트 세트(골든셋)” 준비
- **MLF(Minimum lovable feature)**: 최소로 사랑받을 시나리오(P0)를 정하고 확장

> 이 흐름은 `Optimize metadata`와 직접 연결됩니다. 메타데이터는 기능 설명이 아니라 ‘모델을 위한 제품 카피’에 가깝습니다.
## 3) MCP 서버 구현 핵심(가장 중요한 규칙들)

### 3.1 `text/html+skybridge`와 위젯 템플릿
- 위젯 UI 번들은 MCP 리소스로 등록합니다.
- 리소스의 `mimeType`이 **`text/html+skybridge`**여야 ChatGPT가 이를 “위젯 템플릿”으로 인식하고, iframe 안에 `window.openai` 런타임을 주입합니다.

### 3.2 `window.openai`(위젯 런타임) 개념
위젯은 `window.openai`를 통해 **툴 입출력/상태/호스트 제어**를 수행합니다.

- **State & data**: `toolInput`, `toolOutput`, `toolResponseMetadata`, `widgetState`
- **Tool/messaging**: `callTool`, `sendFollowUpMessage`
- **Files**: `uploadFile`, `getFileDownloadUrl`
- **Layout/host**: `requestDisplayMode`, `requestModal`, `notifyIntrinsicHeight`, `openExternal`
- **Context**: `theme`, `displayMode`, `maxHeight`, `safeArea`, `view`, `userAgent`, `locale`

### 3.3 Tool descriptor(도구 정의)가 “UX”다
모델은 도구를 선택할 때 descriptor를 보고 판단합니다.

- **Name/Title**: 도구가 수행하는 행동을 명확히(보통 동사)
- **Input schema**: 명시적/제약적(가능하면 enum)
- **UI 연결**: `_meta["openai/outputTemplate"]`로 템플릿 URI 지정
- **옵션 메타**: invoking/invoked 문구, widget 호출 허용 등

또한 모델이 재시도할 수 있으므로, 핸들러는 가능한 **멱등(idempotent)** 하게 설계합니다.
### 3.4 Tool response 3형제: `structuredContent` / `content` / `_meta`
서버의 툴 응답은 보통 세 덩어리로 구성됩니다.

- **`structuredContent`**: 모델과 위젯이 모두 읽는 “간결 JSON”(모델에 노출)
- **`content`**: 모델이 응답을 구성할 때 참고하는 텍스트(선택)
- **`_meta`**: 위젯만 읽는 데이터(모델에 절대 전달되지 않음)

가이드라인:
- 모델 성능/정확도/속도에 영향을 주는 건 `structuredContent`이므로 **필요 최소만** 담습니다.
- 크거나 민감한 데이터(혹은 UI 전용 데이터)는 `_meta`로 보냅니다.
- 세 값 모두 사용자에게 노출될 수 있으므로 **토큰/비밀값을 절대 포함하면 안 됩니다**.

### 3.5 위젯에서 툴 호출하기
- 기본적으로 툴은 모델이 호출하지만, UI에서 직접 새로고침/상호작용을 위해 **위젯이 툴을 호출**할 수 있습니다.
- 이때 tool descriptor에 `_meta["openai/widgetAccessible"] = true`를 설정합니다.

### 3.6 모델에게 숨기는 “private tool”
- `_meta["openai/visibility"] = "private"`로 설정하면
  - **위젯에서는 호출 가능**
  - **모델의 자동 선택 대상에서는 숨김**

### 3.7 파일 입력(file params)
- 사용자 제공 파일을 받는 툴은 `_meta["openai/fileParams"]`에 **최상위 입력 필드명 리스트**를 지정합니다.
- 파일 객체는 `{ download_url, file_id }` 형태를 사용합니다.
### 3.8 위젯 CSP(도메인 allowlist)는 “필수 인프라”
ChatGPT 위젯은 sandbox 환경이므로, 네트워크/리소스/프레임이 기본적으로 차단됩니다.
위젯 리소스에 `_meta["openai/widgetCSP"]`를 설정해 허용 도메인을 명시합니다.

- **`connect_domains`**: fetch/XHR/WebSocket 등 연결 대상
- **`resource_domains`**: 이미지/폰트/스크립트 등 정적 리소스
- **`redirect_domains`**: `openExternal` 리다이렉트 대상(옵션)
- **`frame_domains`**: iframe 임베드 허용(옵션)

특히 `frame_domains`는 심사에서 추가 검토 대상이며, 공개 배포에서 거절될 가능성이 큽니다.

### 3.9 위젯 전용 도메인 / 설명
- `_meta["openai/widgetDomain"]`: 전용 오리진이 필요할 때 설정(예: API allowlist)
- `_meta["openai/widgetDescription"]`: 위젯 자체 설명(중복 설명 줄이기)

### 3.10 Locale / client hints
- 요청 메타로 locale/userAgent/userLocation 등의 힌트가 올 수 있지만
  - **권한/인증 판단에 사용하면 안 됩니다.**
  - 인증/권한은 서버에서 강제하세요.
## 4) 배포(Deploy): /mcp 안정성과 스트리밍

배포의 핵심 체크포인트는 단순히 HTTPS가 아니라, **`/mcp` 엔드포인트 품질**입니다.

- **HTTPS**: ChatGPT 연결은 HTTPS가 필요
- **`/mcp` 응답성**: 느리거나 불안정하면 UX가 무너짐
- **Streaming 지원**: 플랫폼 선택 시 streaming HTTP / SSE 특성을 고려
- **에러 코드/메시지**: 적절한 HTTP 상태 코드와 명확한 에러 페이로드

권장 배포 옵션(문서 예시)
- Managed containers: Fly.io / Render / Railway
- Cloud serverless: Cloud Run / Azure Container Apps (cold start 주의)
- Kubernetes: SSE를 지원하는 ingress 필요

개발 중에는 ngrok 같은 터널로 로컬을 연결하고, 코드 변경 시
- UI 번들 재빌드
- MCP 서버 재시작
- ChatGPT 설정에서 커넥터 리프레시(메타데이터 갱신)

운영 설정
- **Secrets**: repo 밖(Secret manager + env)
- **Logging**: tool-call ID, latency, error payload
- **Observability**: CPU/mem/request 모니터링
## 5) UX/UI: “대화 기반 경험”에 맞게 설계하기

### 5.1 UX principles 요약
좋은 앱은 “ChatGPT 안에 있기 때문에 더 좋은” 최소 1개 장점을 가져야 합니다.

- **Conversational leverage**: 자연어/문맥/멀티턴 가이던스
- **Native fit**: 모델과 툴 사이 자연스러운 핸드오프
- **Composability**: 작은 액션(툴)을 조합해 더 큰 작업을 해결

실무 원칙
- **Extract, don’t port**: 웹/앱 전체를 포팅하지 말고 핵심 작업을 “원자적 도구”로 추출
- **Conversational entry**: 사용자는 대화 중간에 들어올 수 있음(직접 명령/모호한 의도/온보딩)
- **Conversation > navigation**: 대시보드/내비게이션보다 대화 흐름을 유지

### 5.2 UI guidelines 요약: display mode를 표준처럼 사용
- **Inline**: 대화 흐름 속 카드/캐러셀(기본)
- **Fullscreen**: 리치/멀티스텝(단, 시스템 composer가 항상 존재)
- **PiP**: 라이브/세션형 경험(대화와 병렬)

Inline card 룰(중요)
- Primary action 최대 2개
- 깊은 내비게이션/탭/드릴다운 금지
- 중첩 스크롤 금지
- ChatGPT 시스템 기능(입력창 등) 복제 금지
### 5.3 Visual/Accessibility 요약
- **Color**: 시스템 컬러 유지, 브랜드는 accent/버튼/배지 정도로 제한
- **Typography**: 시스템 폰트 상속, 커스텀 폰트 금지
- **Spacing**: 일관된 패딩/마진/정렬로 스캔 가능성 확보
- **Icons/imagery**: 단색/아웃라인 스타일 권장, 로고를 콘텐츠에 넣지 말 것
- **Accessibility**: WCAG AA 대비, alt text, 텍스트 리사이즈 대응

## 6) Optimize metadata: 발견(Discovery) 튜닝 방법

메타데이터는 “모델을 위한 제품 카피”입니다.

- **골든 프롬프트 세트**를 만든다: direct / indirect / negative
- 프롬프트별 기대 행동을 라벨링한다(툴 호출/미호출/대안)
- 툴별로 다음을 다듬는다
  - **Name**: `domain.action` 스타일
  - **Description**: “Use this when…” + “Do not use for …”로 경계 명확화
  - **Parameter docs**: 예시 포함, enum 적극 활용
  - **Hints**: `readOnlyHint`, `destructiveHint`, `openWorldHint` 적절히 설정
- Developer mode에서 precision/recall을 기록하며 반복
- 운영 후에는 툴 호출 분석을 주기적으로 보고(오발동 스파이크 = drift)
## 7) App submission guidelines(심사): 가장 흔한 거절 포인트

### 7.1 도구 정의(툴) 관련
- **툴 이름**: 행동을 정확히 반영(과장/선동/비교/“공식” 금지)
- **툴 설명**: 실제 동작과 일치해야 하며, 모델 선택을 조작하는 문구 금지
- **주석/힌트**: `readOnlyHint`, `openWorldHint`, `destructiveHint` 누락/오류는 흔한 거절 사유
- **입력 최소화**: “혹시 몰라서” 넓게 받지 말 것(대화 로그 전체/불필요 컨텍스트 금지)
- **부작용 투명성**: 외부로 데이터가 나가거나 공개 콘텐츠가 생성되면 정의에서 명시

### 7.2 인증/권한
- 인증 흐름은 투명/명시적이어야 하며 권한은 최소.
- 심사 시 **샘플 데이터가 있는 데모 계정** 제공이 필요(가입 강제/접근 불가 2FA는 거절).

### 7.3 프라이버시
- 공개된 privacy policy 필수.
- 입력/응답 모두 **목적 관련 최소 데이터**만.
- Restricted Data(PCI/PHI/정부식별자/인증 비밀값 등) 수집 금지.
- 풀 채팅 로그를 재구성/추론하려고 하면 안 됨.

### 7.4 커머스/광고
- 현재 커머스는 **물리적 상품** 중심 제한.
- 디지털 상품/서비스(구독/토큰 등) 판매 금지.
- 광고 제공/광고가 주목적이면 거절.

> 심사 관점에서 `frame_domains` 사용은 리스크가 크므로, 가능하면 iframe 임베드 없이 설계하세요.
## 8) 최소 용어집(Glossary)
- **MCP server**: 모델이 호출하는 도구(tool) 제공 서버
- **Tool descriptor**: 모델이 도구 선택에 사용하는 스키마/설명/메타데이터
- **Widget template**: ChatGPT가 iframe에서 렌더링할 HTML 엔트리(보통 `text/html+skybridge`)
- **`window.openai`**: 위젯 런타임 글로벌(입출력/상태/툴 호출/호스트 제어)
- **`structuredContent`**: 모델+위젯이 읽는 간결 JSON
- **`_meta`**: 위젯 전용 데이터(모델 비노출)
- **CSP allowlist**: 위젯이 연결/리소스/리다이렉트/iframe에 접근 가능한 도메인 목록

## 참고(원문 링크)
- Apps SDK: https://developers.openai.com/apps-sdk
- Use cases: https://developers.openai.com/apps-sdk/plan/use-case
- MCP server: https://developers.openai.com/apps-sdk/build/mcp-server
- Deploy: https://developers.openai.com/apps-sdk/deploy
- Submission guidelines: https://developers.openai.com/apps-sdk/app-submission-guidelines
- UX principles: https://developers.openai.com/apps-sdk/concepts/ux-principles
- UI guidelines: https://developers.openai.com/apps-sdk/concepts/ui-guidelines
- Optimize metadata: https://developers.openai.com/apps-sdk/guides/optimize-metadata
