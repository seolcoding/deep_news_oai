# Deep News OAI - OpenAI ChatGPT App

## 프로젝트 개요

BigKinds API를 활용한 **OpenAI ChatGPT App** (MCP 서버)

| 항목 | 값 |
|------|-----|
| 배포 서버 | 100.114.192.51 |
| 포트 | 58003 |
| URL | https://deepnews-oai.seolcoding.com |
| 응답 형식 | OAI 3형제 (structuredContent, content, _meta) |

## 프로젝트 구조

```
deep_news_oai/
├── src/deep_news_oai/
│   ├── server.py           # FastMCP 서버 + Tools
│   ├── core/               # BigKinds API 클라이언트
│   │   ├── client.py       # Async HTTP 클라이언트
│   │   └── models.py       # Pydantic 모델
│   ├── responses/          # OAI 응답 빌더
│   │   └── builder.py      # OAIResponse 클래스
│   └── widgets/            # HTML 위젯
│       ├── search_results.html
│       ├── article_detail.html
│       └── trending_issues.html
├── tests/
├── Dockerfile
├── docker-compose.yml
└── DEPLOY.md              # 배포 가이드
```

## 명령어

```bash
# 의존성 설치
uv sync

# 테스트 실행
uv sync --extra dev && uv run pytest

# 서버 실행 (개발)
uv run python -m deep_news_oai

# Docker 빌드 및 실행
docker-compose up -d --build
```

## Tools (5개)

| Tool | 설명 |
|------|------|
| `search_korean_news` | 한국 뉴스 검색 |
| `count_news_articles` | 기사 건수 조회 |
| `get_korean_time` | 현재 한국 시간 |
| `list_news_providers` | 언론사 목록 |
| `find_news_category` | 카테고리 검색 |

## OAI 응답 형식

```python
# 모든 Tool 응답은 OAI 3형제 형식:
{
    "structuredContent": {...},  # 모델용 최소 JSON
    "content": "텍스트 요약",     # 텍스트 응답
    "_meta": {                    # 위젯 전용 데이터
        "openai/outputTemplate": "widget://search_results",
        "full_data": {...}
    }
}
```

## 핵심 구현 패턴 (Must Follow)

> 상세 패턴은 Serena Memory `openai-apps-sdk-patterns.md` 참조

### Tool 정의 필수사항

```python
@mcp.tool(
    annotations={
        "title": "Human-readable title",
        "readOnlyHint": True,      # 읽기 전용 여부
        "openWorldHint": True,     # 외부 API 호출 여부
        "destructiveHint": False,  # 파괴적 변경 여부
        "idempotentHint": True,    # 멱등성 여부
    }
)
```

### Tool 설명 패턴

```python
"""
Use this when the user wants to:
- [사용 케이스 1]
- [사용 케이스 2]

Do not use for:
- [안 되는 케이스]
"""
```

### 위젯 리소스 필수사항

- MIME 타입: `text/html+skybridge` (필수)
- CSP 설정: `_meta["openai/widgetCSP"]` 도메인 목록
- intrinsicHeight 알림: `window.openai.notifyIntrinsicHeight()`

### structuredContent 최소화

- 모델 토큰 비용에 직접 영향
- 상위 5개 등 요약만 포함
- 전체 데이터는 `_meta.full_data`로 이동

## 참고 문서

| 문서 | 위치 |
|------|------|
| OAI Apps SDK 가이드 | `oai_docs/apps_sdk/guide.md` |
| SDK 패턴 (Serena Memory) | `openai-apps-sdk-patterns.md` |
| MCP 서버 구현 | `oai_docs/raw/02_build_mcp-server.md` |
| 배포 가이드 | `DEPLOY.md` |
| bigkinds-mcp (참조) | `../bigkinds` |
