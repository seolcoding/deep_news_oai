# Build — Build your MCP server

- Source: https://developers.openai.com/apps-sdk/build/mcp-server
- Captured: 2025-12-22
- Note: condensed capture (outline + 핵심 규칙/키워드)

## Section outline
- Overview
  - What an MCP server does for your app
  - Before you begin
- Architecture flow
- Understand the `window.openai` widget runtime
- Pick an SDK
- Build your MCP server
  - Step 1 – Register a component template
  - Step 2 – Describe tools
  - Step 3 – Return structured data and metadata
  - Step 4 – Run locally
  - Step 5 – Expose an HTTPS endpoint
- Example
- Troubleshooting
- Advanced capabilities
  - Component-initiated tool calls
  - Tool visibility
  - Files out (file params)
  - Content security policy (CSP)
  - Widget domains
  - Component descriptions
  - Localized content
  - Client context hints
- Security reminders

## 핵심 개념(요약)
- ChatGPT Apps는 **(1) MCP server (백엔드)**, **(2) widget/UI bundle (iframe)**, **(3) model (도구 선택/서술)**의 3요소로 구성.
- 서버는 **도구(tool) 정의 + 인증/권한 + 데이터 반환 + UI 템플릿 연결**을 담당.
- 위젯은 sandboxed iframe에서 `window.openai` 런타임을 통해 **입력/출력/상태/도구호출**을 처리.

## 필수 키워드/규칙(문서에서 강조)
- `text/html+skybridge`: ChatGPT가 **위젯 템플릿**으로 취급하고 `window.openai`를 주입하는 MIME 타입.
- `structuredContent`: **모델이 읽는** 간결 JSON(= 모델 성능/결정에 영향을 줌). 필요 최소만.
- `_meta`: **위젯만 읽는** 데이터(모델로 전달되지 않음). 크거나 민감한 데이터는 여기에.
- Idempotency: 모델이 **tool call을 재시도**할 수 있으므로 핸들러는 가능한 멱등하게 설계.
## `window.openai` 런타임(핵심 능력)
- **State & data**: `toolInput`, `toolOutput`, `toolResponseMetadata`, `widgetState`
- **Tool/messaging**: `callTool`, `sendFollowUpMessage`
- **Files**: `uploadFile`, `getFileDownloadUrl`
- **Layout/host controls**: `requestDisplayMode`, `requestModal`, `notifyIntrinsicHeight`, `openExternal`
- **Context signals**: `theme`, `displayMode`, `maxHeight`, `safeArea`, `view`, `userAgent`, `locale`

## Tool descriptor(도구 정의) 체크리스트
- **Name/Title**: 모델이 “언제 이 도구를 쓰는지” 판단하는 핵심 힌트
- **Input schema**: 가능한 명시적, 제약 가능한 필드는 enum 등으로 제한
- **UI 연결**: `_meta["openai/outputTemplate"]`로 위젯 템플릿 URI 지정
- **옵션 메타**: invoking/invoked 문자열, `openai/widgetAccessible`, read-only 힌트 등

## Tool response 3형제(서버 응답 구조)
- **`structuredContent`**: 모델+위젯이 모두 읽음(모델에 노출)
- **`content`**: 모델 응답용 텍스트/마크다운(선택)
- **`_meta`**: 위젯 전용 데이터(모델에 절대 안 감)

## 위젯에서 tool call을 하려면
- tool descriptor에 `_meta["openai/widgetAccessible"] = true` 설정 → 위젯에서 `window.openai.callTool` 사용 가능

## Tool visibility
- `_meta["openai/visibility"] = "private"` → **위젯에서는 호출 가능**하지만, **모델에게는 숨김**(프롬프트/UX 안전성 향상)

## File params
- `_meta["openai/fileParams"]`에 **최상위 input 필드명** 리스트 지정
- 각 파일 필드는 `{ download_url, file_id }` 형태

## Widget CSP / 도메인 allowlist
- 위젯 리소스 `_meta["openai/widgetCSP"]`에 도메인 allowlist 선언
  - `connect_domains`: fetch/XHR/WebSocket 등 연결 대상
  - `resource_domains`: 이미지/폰트/스크립트 등 정적 리소스
  - `redirect_domains`: `openExternal` 리다이렉트 대상(옵션)
  - `frame_domains`: iframe 임베드 허용(옵션, **심사 강화/리스크**)

## Widget domains / 설명
- `_meta["openai/widgetDomain"]`: 전용 오리진 필요 시 설정(예: allowlist)
- `_meta["openai/widgetDescription"]`: 위젯 자체 설명(아래 중복 텍스트 줄임)

## Locale / client hints
- 요청 메타에 `_meta["openai/locale"]` 등 힌트가 올 수 있으나 **권한/인증 판단에 사용 금지**

## Security reminders
- `structuredContent`/`content`/`_meta`/widget state는 **사용자에게 보일 수 있음** → 토큰/비밀값 절대 포함 금지
- HTTPS 필수(개발은 터널링, 운영은 HTTPS 배포)
