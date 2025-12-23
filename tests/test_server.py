"""Server and tools tests."""

import pytest
from starlette.testclient import TestClient

from deep_news_oai.server import app, mcp


class TestHealthCheck:
    """Health check endpoint tests."""

    def test_health_endpoint_returns_200(self):
        """Health endpoint should return 200."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self):
        """Health response should have required fields."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "deep-news-oai"


class TestMCPServer:
    """MCP server configuration tests."""

    def test_server_has_name(self):
        """Server should have a name."""
        assert mcp.name == "deep-news-oai"


class TestToolsRegistration:
    """Tool registration tests."""

    def test_tools_are_registered(self):
        """Required tools should be registered."""
        tool_names = [t.name for t in mcp._tool_manager.list_tools()]

        required_tools = [
            "search_korean_news",
            "count_news_articles",
            "get_korean_time",
            "list_news_providers",
            "find_news_category",
        ]

        for tool in required_tools:
            assert tool in tool_names, f"Tool {tool} should be registered"

    def test_search_tool_has_parameters(self):
        """search_korean_news should have required parameters."""
        tools = mcp._tool_manager.list_tools()
        search_tool = next((t for t in tools if t.name == "search_korean_news"), None)

        assert search_tool is not None

        # Check parameters exist in the tool's function signature
        import inspect
        from deep_news_oai.server import search_korean_news

        sig = inspect.signature(search_korean_news)
        params = list(sig.parameters.keys())

        required_params = ["keyword", "start_date", "end_date"]
        for param in required_params:
            assert param in params, f"Parameter {param} should exist"
