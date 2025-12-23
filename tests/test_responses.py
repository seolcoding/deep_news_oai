"""Tests for OAI response builder."""

import pytest
from deep_news_oai.responses.builder import (
    OAIResponse,
    search_response,
    article_response,
    trending_response,
)


class TestOAIResponse:
    """Test OAIResponse builder class."""

    def test_success_has_three_fields(self):
        """Success response must have 3형제 structure."""
        response = OAIResponse.success(
            structured={"count": 10},
            content="Found 10 items",
        )

        assert "structuredContent" in response
        assert "content" in response
        assert "_meta" in response

    def test_success_with_widget(self):
        """Success response includes widget template reference."""
        response = OAIResponse.success(
            structured={"data": "test"},
            content="Test content",
            widget="search_results",
        )

        assert response["_meta"]["openai/outputTemplate"] == "widget://search_results"

    def test_success_with_full_data(self):
        """Full data goes to _meta, not structuredContent."""
        full_data = {"articles": [{"id": 1}, {"id": 2}]}
        response = OAIResponse.success(
            structured={"count": 2},
            content="Found 2 articles",
            full_data=full_data,
        )

        # Full data should be in _meta only
        assert response["_meta"]["full_data"] == full_data
        assert "articles" not in response["structuredContent"]

    def test_error_response(self):
        """Error response has correct structure."""
        response = OAIResponse.error(
            code="INVALID_DATE",
            message="날짜 형식이 올바르지 않습니다.",
        )

        assert response["structuredContent"]["error"] is True
        assert response["structuredContent"]["code"] == "INVALID_DATE"
        assert "오류:" in response["content"]

    def test_inline_response(self):
        """Inline response has empty _meta."""
        response = OAIResponse.inline(
            structured={"time": "2025-01-01 12:00:00"},
            content="현재 시간: 2025-01-01 12:00:00",
        )

        assert response["_meta"] == {}
        assert "time" in response["structuredContent"]


class TestWidgetCSP:
    """Test Widget CSP configuration."""

    def test_success_with_widget_includes_csp(self):
        """Widget responses should include CSP domains."""
        response = OAIResponse.success(
            structured={"test": "data"},
            content="Test content",
            widget="search_results",
        )
        assert "openai/widgetCSP" in response["_meta"]
        csp_domains = response["_meta"]["openai/widgetCSP"]
        assert isinstance(csp_domains, list)
        assert len(csp_domains) > 0
        # Should include major Korean news domains
        assert any("chosun.com" in d for d in csp_domains)
        assert any("bigkinds.or.kr" in d for d in csp_domains)

    def test_inline_response_no_csp(self):
        """Inline responses without widget should not have CSP."""
        response = OAIResponse.inline(
            structured={"test": "data"},
            content="Test content",
        )
        assert "openai/widgetCSP" not in response["_meta"]


class TestSearchResponse:
    """Test search response builder."""

    def test_search_response_structure(self):
        """Search response has correct OAI structure."""
        articles = [
            {"title": "AI News 1", "publisher": "경향신문", "date": "2025-01-01"},
            {"title": "AI News 2", "publisher": "조선일보", "date": "2025-01-02"},
        ]
        response = search_response(
            total_count=100,
            page=1,
            page_size=20,
            articles=articles,
            keyword="AI",
        )

        # Check 3형제
        assert "structuredContent" in response
        assert "content" in response
        assert "_meta" in response

        # Check structuredContent is minimal
        sc = response["structuredContent"]
        assert sc["total_count"] == 100
        assert sc["has_next"] is True
        assert len(sc["top_articles"]) <= 5

        # Check widget reference
        assert response["_meta"]["openai/outputTemplate"] == "widget://search_results"

        # Check full data in _meta
        assert response["_meta"]["full_data"]["articles"] == articles

    def test_search_response_pagination(self):
        """Search response correctly calculates has_next."""
        response = search_response(
            total_count=15,
            page=1,
            page_size=20,
            articles=[],
            keyword="test",
        )

        assert response["structuredContent"]["has_next"] is False


class TestArticleResponse:
    """Test article response builder."""

    def test_article_response_structure(self):
        """Article response has correct structure."""
        response = article_response(
            news_id="123",
            title="Test Article",
            content_text="This is the article content" * 20,
            publisher="경향신문",
            published_date="2025-01-01T12:00:00",
            url="https://example.com/article/123",
        )

        # Check 3형제
        assert "structuredContent" in response
        assert "content" in response
        assert "_meta" in response

        # Check structured has summary (truncated)
        sc = response["structuredContent"]
        assert len(sc.get("summary", "")) <= 200

        # Check widget
        assert response["_meta"]["openai/outputTemplate"] == "widget://article_detail"


class TestTrendingResponse:
    """Test trending issues response builder."""

    def test_trending_response_structure(self):
        """Trending response has correct structure."""
        issues = [
            {"rank": 1, "title": "Hot Topic 1", "keywords": ["AI", "Tech", "News"]},
            {"rank": 2, "title": "Hot Topic 2", "keywords": ["Economy"]},
        ]
        response = trending_response(
            issues=issues,
            date="2025-01-01",
        )

        # Check 3형제
        sc = response["structuredContent"]
        assert sc["date"] == "2025-01-01"
        assert sc["issue_count"] == 2
        assert len(sc["top_issues"]) <= 5

        # Keywords should be truncated
        assert len(sc["top_issues"][0]["keywords"]) <= 3

        # Check widget
        assert response["_meta"]["openai/outputTemplate"] == "widget://trending_issues"
