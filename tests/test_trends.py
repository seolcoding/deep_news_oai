"""Google Trends integration tests."""

from datetime import datetime
from pathlib import Path
import pytest

from deep_news_oai.core.trends import GoogleTrendsClient, TrendingItem


class TestTrendingItem:
    """TrendingItem dataclass tests."""

    def test_trending_item_to_dict(self):
        """Should convert to dictionary correctly."""
        item = TrendingItem(
            rank=1,
            keyword="테스트",
            search_volume="2만+",
            growth_rate="+500%",
            related_terms=["관련1", "관련2", "관련3"],
            scraped_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        result = item.to_dict()

        assert result["rank"] == 1
        assert result["keyword"] == "테스트"
        assert result["search_volume"] == "2만+"
        assert result["growth_rate"] == "+500%"
        assert len(result["related_terms"]) <= 5
        assert result["scraped_at"] == "2024-01-01T12:00:00"

    def test_trending_item_limits_related_terms(self):
        """Should limit related terms to 5."""
        item = TrendingItem(
            rank=1,
            keyword="테스트",
            related_terms=["a", "b", "c", "d", "e", "f", "g"],
        )

        result = item.to_dict()

        assert len(result["related_terms"]) == 5

    def test_trending_item_handles_none_scraped_at(self):
        """Should handle None scraped_at."""
        item = TrendingItem(rank=1, keyword="테스트")

        result = item.to_dict()

        assert result["scraped_at"] is None


class TestGoogleTrendsClient:
    """GoogleTrendsClient tests."""

    def test_default_cache_path_exists(self):
        """Default cache path should be in project data directory."""
        client = GoogleTrendsClient()

        assert "data" in str(client.cache_path)
        assert "google_trends_cache.csv" in str(client.cache_path)

    def test_get_trending_returns_list(self):
        """Should return list of TrendingItem."""
        client = GoogleTrendsClient()

        result = client.get_trending(limit=5)

        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], TrendingItem)

    def test_get_trending_respects_limit(self):
        """Should respect the limit parameter."""
        client = GoogleTrendsClient()

        result = client.get_trending(limit=3)

        assert len(result) <= 3

    def test_get_trending_sorted_by_rank(self):
        """Results should be sorted by rank."""
        client = GoogleTrendsClient()

        result = client.get_trending(limit=10)

        if len(result) > 1:
            ranks = [item.rank for item in result]
            assert ranks == sorted(ranks)

    def test_get_cache_status(self):
        """Should return cache status dictionary."""
        client = GoogleTrendsClient()

        status = client.get_cache_status()

        assert "cache_path" in status
        assert "cache_exists" in status
        assert "cache_valid" in status
        assert "items_count" in status
        assert "max_age_hours" in status

    def test_cache_validation(self):
        """Cache should be validated based on max_age."""
        client = GoogleTrendsClient(cache_max_age_hours=6)

        # Initially cache is not valid (not loaded)
        assert not client._is_cache_valid()

        # After loading, cache should be valid
        client.get_trending(limit=1)
        assert client._is_cache_valid()

    def test_get_trending_with_context(self):
        """Should return list of dicts with news hints."""
        client = GoogleTrendsClient()

        result = client.get_trending_with_context(limit=3)

        assert isinstance(result, list)
        if result:
            assert "keyword" in result[0]
            assert "news_hint" in result[0]


class TestGoogleTrendsClientWithMissingFile:
    """Tests for missing cache file scenario."""

    def test_missing_cache_returns_empty(self, tmp_path):
        """Should return empty list if cache file missing."""
        client = GoogleTrendsClient(cache_path=tmp_path / "nonexistent.csv")

        result = client.get_trending()

        assert result == []

    def test_cache_status_shows_not_exists(self, tmp_path):
        """Should show cache doesn't exist."""
        client = GoogleTrendsClient(cache_path=tmp_path / "nonexistent.csv")

        status = client.get_cache_status()

        assert status["cache_exists"] is False
        assert status["cache_valid"] is False
