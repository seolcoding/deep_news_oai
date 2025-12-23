# OpenAI Apps SDK Python 구현 패턴

> 이 문서는 openai/openai-apps-sdk-examples 리포지토리 분석을 통해 도출한 권장 패턴입니다.

## 1. 핵심 아키텍처 패턴

### 1.1 Widget 데이터 구조 (dataclass 활용)

```python
from dataclasses import dataclass

@dataclass
class Widget:
    identifier: str  # 도구에서 참조하는 ID
    title: str
    template_uri: str  # "widget://{identifier}" 형식
    html: str  # 위젯 HTML 콘텐츠
```

**장점**: 위젯 메타데이터와 HTML을 하나의 엔티티로 관리

### 1.2 위젯 레지스트리 패턴

```python
WIDGETS_BY_ID: dict[str, Widget] = {}
WIDGETS_BY_URI: dict[str, Widget] = {}

def _register_widget(w: Widget) -> None:
    WIDGETS_BY_ID[w.identifier] = w
    WIDGETS_BY_URI[w.template_uri] = w
```

**장점**: ID와 URI 양방향 조회 가능, 도구/리소스 간 일관성 보장

### 1.3 캐싱된 HTML 로딩

```python
from functools import lru_cache

@lru_cache(maxsize=32)
def _load_widget_html(name: str) -> str:
    """위젯 HTML을 캐싱하여 로드"""
    path = ASSETS_DIR / f"{name}.html"
    return path.read_text() if path.exists() else fallback_html
```

**장점**: 반복 호출 시 I/O 비용 절감

## 2. MCP Tool 정의 패턴

### 2.1 도구 힌트 필수 사용

```python
@mcp.tool(
    annotations={
        "title": "Human-readable title",
        "readOnlyHint": True,  # 읽기 전용 여부
        "openWorldHint": True,  # 외부 API 호출 여부
        "destructiveHint": False,  # 파괴적 변경 여부
        "idempotentHint": True,  # 멱등성 여부
    }
)
```

**이유**: 모델이 도구 선택 시 이 힌트를 참고함

### 2.2 도구 설명 패턴 (Use this when... / Do not use for...)

```python
async def search_korean_news(...):
    """
    Search Korean news articles from BigKinds database.

    Use this when the user wants to:
    - Search for news about a topic in Korean media
    - Find articles about events, people, or issues

    Do not use for:
    - International news not covered by Korean media
    - Real-time breaking news (data has ~1 day delay)
    """
```

**이유**: 모델이 정확한 도구 선택을 하도록 경계를 명확히 함

### 2.3 입력 검증 (Pydantic 활용)

```python
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    keyword: str = Field(..., description="검색 키워드")
    start_date: str = Field(..., description="시작일 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료일 (YYYY-MM-DD)")
```

## 3. 응답 구조 패턴 (OAI 3형제)

### 3.1 표준 응답 구조

```python
{
    "structuredContent": {
        # 모델용 최소 JSON - 토큰 비용에 영향
        "total_count": 100,
        "top_articles": [...]  # 상위 5개만
    },
    "content": "검색 결과 100건",  # 텍스트 요약
    "_meta": {
        "openai/outputTemplate": "widget://search_results",
        "openai/widgetCSP": [...],  # 위젯 보안 정책
        "full_data": {...}  # 위젯 전용 전체 데이터
    }
}
```

### 3.2 structuredContent 최소화 원칙

- 모델이 응답 구성에 필요한 최소 정보만 포함
- 큰 데이터는 `_meta.full_data`로 이동
- 민감 정보 절대 포함 금지

### 3.3 위젯 접근성 설정

```python
# 위젯에서 호출 가능한 도구
_meta["openai/widgetAccessible"] = True

# 모델에게 숨기는 private 도구 (위젯 전용)
_meta["openai/visibility"] = "private"
```

## 4. 리소스 정의 패턴

### 4.1 위젯 리소스 등록

```python
@mcp.resource(
    "widget://search_results",
    mime_type="text/html+skybridge",  # 필수: ChatGPT 위젯 인식
    description="뉴스 검색 결과를 카드 UI로 표시"
)
def search_results_widget() -> str:
    return load_widget_html("search_results")
```

**중요**: `text/html+skybridge` MIME 타입 필수

### 4.2 CSP(Content Security Policy) 설정

```python
WIDGET_CSP_DOMAINS = [
    "*.bigkinds.or.kr",  # API 도메인
    "*.chosun.com",  # 이미지 등 리소스 도메인
]

_meta["openai/widgetCSP"] = WIDGET_CSP_DOMAINS
```

## 5. 위젯 JavaScript 패턴

### 5.1 window.openai 런타임 사용

```javascript
(function() {
    const { toolOutput, theme, displayMode } = window.openai || {};
    
    // 테마 적용
    document.body.classList.add(theme === 'dark' ? 'dark' : 'light');
    
    // 데이터 접근 (우선순위: _meta.full_data > structuredContent)
    const data = toolOutput?._meta?.full_data || toolOutput?.structuredContent || {};
    
    // 렌더링 로직...
})();
```

### 5.2 도구 호출 (위젯 → 서버)

```javascript
// 후속 메시지 전송
window.openai.sendFollowUpMessage(`기사 상세 조회: ${newsId}`);

// 직접 도구 호출 (widgetAccessible=true 필요)
window.openai.callTool('get_article_detail', { news_id: newsId });
```

### 5.3 intrinsicHeight 알림

```javascript
// 위젯 높이 변경 시 호스트에 알림
window.openai.notifyIntrinsicHeight(document.body.scrollHeight);
```

## 6. 서버 구성 패턴

### 6.1 lifespan 관리 (비동기 클라이언트)

```python
@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[dict[str, Any]]:
    global _client
    _client = AsyncAPIClient()
    
    yield {"client": _client}
    
    await _client.close()

mcp.settings.lifespan = lifespan
```

### 6.2 상태 비저장 모드

```python
mcp = FastMCP("app-name", stateless_http=True)
```

**장점**: 확장성 향상, 서버 인스턴스 간 상태 공유 불필요

### 6.3 Health Check 엔드포인트

```python
from starlette.applications import Starlette
from starlette.routing import Route, Mount

async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "app-name"})

app = Starlette(routes=[
    Route("/health", health_check),
    Mount("/", app=mcp.sse_app()),
])
```

## 7. 에러 처리 패턴

### 7.1 표준 에러 응답

```python
class OAIResponse:
    @staticmethod
    def error(code: str, message: str) -> dict:
        return {
            "structuredContent": {"error": True, "code": code},
            "content": f"오류: {message}",
            "_meta": {"error_code": code, "error_message": message}
        }
```

### 7.2 재시도 로직 (Exponential Backoff)

```python
for attempt in range(max_retries):
    try:
        # API 호출
        break
    except Exception:
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)
```

## 8. 안티패턴 (피해야 할 것들)

### 8.1 ❌ structuredContent에 전체 데이터 포함
```python
# Bad: 모델 토큰 낭비
"structuredContent": {"articles": [...100개...]}

# Good: 요약만 포함
"structuredContent": {"total": 100, "top_5": [...]}
```

### 8.2 ❌ 도구 힌트 누락
```python
# Bad: 힌트 없음
@mcp.tool()

# Good: 힌트 명시
@mcp.tool(annotations={"readOnlyHint": True, ...})
```

### 8.3 ❌ 위젯에서 직접 외부 API 호출
```javascript
// Bad: CORS/CSP 문제 발생
fetch('https://external-api.com/data')

// Good: 서버 도구 통해 호출
window.openai.callTool('fetch_external_data', {...})
```

### 8.4 ❌ 민감 정보 응답에 포함
```python
# Bad: API 키 노출 위험
"structuredContent": {"api_key": "...", ...}

# Good: 서버에서만 처리
```

---

## 참고 자료
- [openai/openai-apps-sdk-examples](https://github.com/openai/openai-apps-sdk-examples)
- [Apps SDK 공식 문서](https://developers.openai.com/apps-sdk)
- 프로젝트 내 `oai_docs/apps_sdk/guide.md`
