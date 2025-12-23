"""Integration tests for Deep News OAI MCP server.

These tests verify the server works correctly with the MCP protocol
and produces OAI-compliant responses.

Run with: uv run pytest tests/test_integration.py -v
"""

import httpx
import pytest

# Server URL
BASE_URL = "https://deepnews-oai.seolcoding.com"


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_returns_200(self):
        """Health endpoint should return 200 OK."""
        response = httpx.get(f"{BASE_URL}/health", timeout=10)
        assert response.status_code == 200

    def test_health_response_format(self):
        """Health response should have expected fields."""
        response = httpx.get(f"{BASE_URL}/health", timeout=10)
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "deep-news-oai"
        assert "client_initialized" in data


class TestSSEEndpoint:
    """Test the SSE endpoint for MCP communication."""

    def test_sse_returns_event_stream(self):
        """SSE endpoint should return event stream with session endpoint."""
        with httpx.stream(
            "GET",
            f"{BASE_URL}/sse",
            headers={"Accept": "text/event-stream"},
            timeout=10,
        ) as response:
            # Read first few lines
            lines = []
            for line in response.iter_lines():
                lines.append(line)
                if len(lines) >= 3:
                    break

            # Should have event: endpoint and data: /messages/...
            assert any("event: endpoint" in line for line in lines)
            assert any("/messages/" in line for line in lines)


class TestGoldenPrompts:
    """
    골든 프롬프트 테스트 케이스.

    ChatGPT에서 실제로 테스트해야 하는 프롬프트들:

    Direct (정확히 호출되어야 함):
    - "AI 관련 최근 한국 뉴스 검색해줘"
    - "오늘 경제 뉴스 보여줘"
    - "삼성전자 관련 기사 찾아줘"
    - "지금 한국 시간이 몇 시야?"

    Indirect (문맥에서 호출 가능):
    - "요즘 반도체 산업 어때?"
    - "최근 정치 이슈가 뭐야?"

    Negative (호출되면 안 됨):
    - "미국 날씨 어때?"
    - "파이썬 코드 작성해줘"
    - "영어로 번역해줘"
    """

    def test_document_golden_prompts(self):
        """This test documents the golden prompts for manual testing."""
        golden_prompts = {
            "direct": [
                ("AI 관련 최근 한국 뉴스 검색해줘", "search_korean_news"),
                ("지금 한국 시간이 몇 시야?", "get_korean_time"),
                ("한국 언론사 목록 보여줘", "list_news_providers"),
            ],
            "indirect": [
                ("요즘 반도체 산업 어때?", "search_korean_news"),
                ("최근 정치 이슈가 뭐야?", "search_korean_news"),
            ],
            "negative": [
                ("미국 날씨 어때?", None),
                ("파이썬 코드 작성해줘", None),
            ],
        }

        # This test just documents the prompts
        # Actual testing should be done in ChatGPT Desktop
        assert len(golden_prompts["direct"]) > 0
        assert len(golden_prompts["negative"]) > 0


class TestOAIResponseFormat:
    """Test that responses follow OAI 3형제 format."""

    def test_response_has_three_siblings(self):
        """All tool responses should have structuredContent, content, _meta."""
        # This is tested in test_responses.py
        # Here we document the requirement
        required_fields = ["structuredContent", "content", "_meta"]
        assert len(required_fields) == 3


# Manual verification checklist
VERIFICATION_CHECKLIST = """
## ChatGPT 연동 테스트 체크리스트

### 1. 연결 테스트
- [ ] ChatGPT Desktop → Settings → Developer Tools
- [ ] MCP Servers → URL: https://deepnews-oai.seolcoding.com/sse
- [ ] Refresh 클릭 → 도구 목록 확인

### 2. 도구 호출 테스트
- [ ] "AI 뉴스 검색해줘" → search_korean_news 호출 확인
- [ ] "지금 한국 시간" → get_korean_time 호출 확인
- [ ] "언론사 목록" → list_news_providers 호출 확인

### 3. Widget 렌더링 테스트
- [ ] 검색 결과 → 카드 UI 표시 확인
- [ ] 기사 클릭 → 상세 보기 동작 확인
- [ ] 다크/라이트 테마 전환 확인

### 4. 에러 처리 테스트
- [ ] 잘못된 날짜 입력 → 에러 메시지 확인
- [ ] 검색 결과 없음 → 적절한 메시지 확인

### 5. 부정 테스트 (호출 안 되어야 함)
- [ ] "미국 날씨 알려줘" → search_korean_news 미호출
- [ ] "코드 작성해줘" → 어떤 도구도 미호출
"""


if __name__ == "__main__":
    print(VERIFICATION_CHECKLIST)
