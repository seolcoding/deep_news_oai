"""Widget file loader with caching.

Following OpenAI Apps SDK examples pattern:
- Use functools.lru_cache for efficient widget loading
- Reduce I/O overhead on repeated calls
"""

from functools import lru_cache
from pathlib import Path

WIDGET_DIR = Path(__file__).parent

# Fallback HTML when widget not found
_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"></head>
<body style="font-family: system-ui; padding: 16px; color: #666;">
<p>Widget not found</p>
</body>
</html>"""


@lru_cache(maxsize=16)
def load_widget(name: str) -> str:
    """
    Load widget HTML by name with caching.

    Uses LRU cache to avoid repeated file I/O.
    Cache size of 16 is sufficient for typical widget count.

    Args:
        name: Widget name without extension (e.g., "search_results")

    Returns:
        Widget HTML content or fallback HTML if not found
    """
    widget_path = WIDGET_DIR / f"{name}.html"
    if widget_path.exists():
        return widget_path.read_text(encoding="utf-8")
    return _FALLBACK_HTML


def clear_widget_cache() -> None:
    """Clear the widget cache. Useful for development/testing."""
    load_widget.cache_clear()
