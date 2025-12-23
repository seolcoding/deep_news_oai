"""Widget loading tests."""

from pathlib import Path

import pytest

from deep_news_oai.widgets.loader import load_widget, clear_widget_cache, WIDGET_DIR


class TestWidgetLoader:
    """Widget loader tests."""

    def test_widget_dir_exists(self):
        """Widget directory should exist."""
        assert WIDGET_DIR.exists()
        assert WIDGET_DIR.is_dir()

    def test_load_search_results_widget(self):
        """Should load search_results widget."""
        html = load_widget("search_results")
        assert "<!DOCTYPE html>" in html
        assert "window.openai" in html
        assert "search" in html.lower() or "articles" in html.lower()

    def test_load_article_detail_widget(self):
        """Should load article_detail widget."""
        html = load_widget("article_detail")
        assert "<!DOCTYPE html>" in html
        assert "window.openai" in html
        assert "article" in html.lower()

    def test_load_trending_issues_widget(self):
        """Should load trending_issues widget."""
        html = load_widget("trending_issues")
        assert "<!DOCTYPE html>" in html
        assert "window.openai" in html
        assert "issues" in html.lower() or "이슈" in html

    def test_load_timeline_widget(self):
        """Should load timeline widget."""
        html = load_widget("timeline")
        assert "<!DOCTYPE html>" in html
        assert "window.openai" in html
        assert "timeline" in html.lower() or "타임라인" in html

    def test_load_perspectives_widget(self):
        """Should load perspectives widget."""
        html = load_widget("perspectives")
        assert "<!DOCTYPE html>" in html
        assert "window.openai" in html
        assert "publisher" in html.lower() or "언론사" in html

    def test_load_report_widget(self):
        """Should load report widget."""
        html = load_widget("report")
        assert "<!DOCTYPE html>" in html
        assert "window.openai" in html
        assert "report" in html.lower() or "리포트" in html or "분석" in html

    def test_load_nonexistent_widget(self):
        """Should return fallback for nonexistent widget."""
        html = load_widget("nonexistent_widget")
        assert "not found" in html.lower()

    def test_widgets_have_theme_support(self):
        """All widgets should support dark/light themes."""
        widgets = ["search_results", "article_detail", "trending_issues", "timeline", "perspectives", "report"]
        for name in widgets:
            html = load_widget(name)
            assert "dark" in html, f"{name} should support dark theme"
            assert "light" in html, f"{name} should support light theme"

    def test_widgets_have_korean_content(self):
        """Widgets should have Korean UI text."""
        widgets = ["search_results", "article_detail", "trending_issues", "timeline", "perspectives", "report"]
        for name in widgets:
            html = load_widget(name)
            # Check for Korean characters
            has_korean = any('\uac00' <= c <= '\ud7a3' for c in html)
            assert has_korean, f"{name} should have Korean content"

    def test_widget_caching(self):
        """Widget loader should cache results."""
        clear_widget_cache()  # Start fresh

        # First call should cache
        html1 = load_widget("search_results")
        # Second call should return cached value
        html2 = load_widget("search_results")

        assert html1 is html2, "Cached widget should be same object"

        # Check cache info
        cache_info = load_widget.cache_info()
        assert cache_info.hits >= 1, "Should have cache hits"

    def test_clear_widget_cache(self):
        """clear_widget_cache should clear the LRU cache."""
        load_widget("search_results")
        clear_widget_cache()

        cache_info = load_widget.cache_info()
        assert cache_info.currsize == 0, "Cache should be empty after clear"

    def test_widgets_have_intrinsic_height(self):
        """All widgets should notify host of intrinsic height."""
        widgets = ["search_results", "article_detail", "trending_issues", "timeline", "perspectives", "report"]
        for name in widgets:
            html = load_widget(name)
            assert "notifyIntrinsicHeight" in html, f"{name} should call notifyIntrinsicHeight"
