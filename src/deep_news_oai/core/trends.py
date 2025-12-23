"""Google Trends integration for real-time trending keywords.

Provides trending search data from Google Trends Korea,
with optional BigKinds news context integration.
"""

import csv
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TrendingItem:
    """Single trending search item."""

    rank: int
    keyword: str
    search_volume: str | None = None  # e.g., "2만+"
    growth_rate: str | None = None    # e.g., "+1000%"
    related_terms: list[str] = field(default_factory=list)
    scraped_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "rank": self.rank,
            "keyword": self.keyword,
            "search_volume": self.search_volume,
            "growth_rate": self.growth_rate,
            "related_terms": self.related_terms[:5],  # Limit to 5
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
        }


class GoogleTrendsClient:
    """Client for Google Trends data.

    Supports multiple data sources:
    1. CSV cache (fastest, for pre-scraped data)
    2. External API (future: dedicated trends service)
    """

    # Default cache file location (can be overridden)
    # Path: core/trends.py -> core -> deep_news_oai -> src -> deep_news_oai (project root)
    DEFAULT_CACHE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "google_trends_cache.csv"

    def __init__(
        self,
        cache_path: Path | str | None = None,
        cache_max_age_hours: int = 6,
    ):
        """
        Initialize Google Trends client.

        Args:
            cache_path: Path to CSV cache file
            cache_max_age_hours: Maximum age of cache before considered stale
        """
        self.cache_path = Path(cache_path) if cache_path else self.DEFAULT_CACHE_PATH
        self.cache_max_age = timedelta(hours=cache_max_age_hours)
        self._cache: list[TrendingItem] | None = None
        self._cache_loaded_at: datetime | None = None

    def _parse_csv_row(self, row: dict) -> TrendingItem | None:
        """Parse a CSV row into TrendingItem."""
        try:
            # Parse related terms from raw_text if available
            related_terms = []
            raw_text = row.get("raw_text", "")
            additional_info = row.get("additional_info", "")

            # Extract related keywords from raw_text
            # Format: "keyword\nvolume\n...\nrelated1\nrelated2\n외 N개"
            if raw_text:
                lines = raw_text.split("\n")
                for line in lines:
                    line = line.strip()
                    # Skip metadata lines
                    if any(skip in line for skip in ["만+", "arrow_", "%", "일 전", "trending_", "활성", "외 ", "개"]):
                        continue
                    # Skip the main keyword
                    if line == row.get("search_term", ""):
                        continue
                    if line and len(line) > 1:
                        related_terms.append(line)

            # Parse volume and growth from additional_info
            # Format: "2만+\narrow_upward\n1,000%"
            search_volume = None
            growth_rate = None
            if additional_info:
                parts = additional_info.split("\n")
                for part in parts:
                    part = part.strip()
                    if "만+" in part or "천+" in part:
                        search_volume = part
                    elif "%" in part:
                        growth_rate = part

            # Parse scraped_at
            scraped_at = None
            if row.get("scraped_at"):
                try:
                    scraped_at = datetime.fromisoformat(row["scraped_at"])
                except (ValueError, TypeError):
                    pass

            return TrendingItem(
                rank=int(row.get("rank", 0)),
                keyword=row.get("search_term", "").strip(),
                search_volume=search_volume,
                growth_rate=growth_rate,
                related_terms=related_terms[:10],  # Limit
                scraped_at=scraped_at,
            )
        except Exception as e:
            logger.warning(f"Failed to parse CSV row: {e}")
            return None

    def _load_cache(self) -> list[TrendingItem]:
        """Load trending data from CSV cache."""
        if not self.cache_path.exists():
            logger.warning(f"Cache file not found: {self.cache_path}")
            return []

        items = []
        try:
            with open(self.cache_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    item = self._parse_csv_row(row)
                    if item and item.keyword:
                        items.append(item)

            logger.info(f"Loaded {len(items)} trending items from cache")
            self._cache = items
            self._cache_loaded_at = datetime.now()

        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return []

        return items

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache is None or self._cache_loaded_at is None:
            return False
        return datetime.now() - self._cache_loaded_at < self.cache_max_age

    def get_trending(self, limit: int = 20) -> list[TrendingItem]:
        """
        Get trending search keywords.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of TrendingItem sorted by rank
        """
        # Use cache if valid
        if not self._is_cache_valid():
            self._load_cache()

        if not self._cache:
            return []

        # Sort by rank and limit
        sorted_items = sorted(self._cache, key=lambda x: x.rank)
        return sorted_items[:limit]

    def get_trending_with_context(
        self,
        limit: int = 10,
        news_client: Any = None,  # BigKindsClient
    ) -> list[dict[str, Any]]:
        """
        Get trending keywords with news context.

        Args:
            limit: Maximum number of items
            news_client: Optional BigKindsClient for news context

        Returns:
            List of dicts with trending data and news summary
        """
        trending = self.get_trending(limit)

        results = []
        for item in trending:
            result = item.to_dict()

            # Add placeholder for news context
            # (Will be filled by the tool with GPT analysis)
            result["news_hint"] = f"'{item.keyword}' 관련 뉴스 검색 가능"

            results.append(result)

        return results

    def refresh_cache(self, data_path: Path | str) -> bool:
        """
        Refresh cache from a new data file.

        Args:
            data_path: Path to new CSV data file

        Returns:
            True if successful
        """
        try:
            data_path = Path(data_path)
            if not data_path.exists():
                logger.error(f"Data file not found: {data_path}")
                return False

            # Copy to cache location
            import shutil
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(data_path, self.cache_path)

            # Reload cache
            self._cache = None
            self._load_cache()

            logger.info(f"Cache refreshed from {data_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to refresh cache: {e}")
            return False

    def get_cache_status(self) -> dict[str, Any]:
        """Get cache status information."""
        return {
            "cache_path": str(self.cache_path),
            "cache_exists": self.cache_path.exists(),
            "cache_valid": self._is_cache_valid(),
            "items_count": len(self._cache) if self._cache else 0,
            "loaded_at": self._cache_loaded_at.isoformat() if self._cache_loaded_at else None,
            "max_age_hours": self.cache_max_age.total_seconds() / 3600,
        }
