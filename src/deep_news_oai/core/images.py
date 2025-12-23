"""Image extraction utilities for news articles."""

import asyncio
import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Regex pattern for og:image meta tag
OG_IMAGE_PATTERN = re.compile(
    r'<meta\s+(?:property=["\']og:image["\']\s+content=["\']([^"\']+)["\']|content=["\']([^"\']+)["\']\s+property=["\']og:image["\'])',
    re.IGNORECASE
)

# Alternative patterns for other image meta tags
TWITTER_IMAGE_PATTERN = re.compile(
    r'<meta\s+(?:name=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']|content=["\']([^"\']+)["\']\s+name=["\']twitter:image["\'])',
    re.IGNORECASE
)


async def extract_og_image(url: str, timeout: float = 5.0) -> str | None:
    """
    Extract og:image from an article URL.

    Args:
        url: Article URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Image URL if found, None otherwise
    """
    if not url:
        return None

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            verify=False,  # Some news sites have SSL issues
        ) as client:
            # Only fetch the head portion to save bandwidth
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; DeepNewsBot/1.0)",
                    "Accept": "text/html",
                }
            )

            if response.status_code != 200:
                return None

            # Only read first 50KB to find meta tags (they're usually in <head>)
            html = response.text[:50000]

            # Try og:image first
            match = OG_IMAGE_PATTERN.search(html)
            if match:
                return match.group(1) or match.group(2)

            # Fallback to twitter:image
            match = TWITTER_IMAGE_PATTERN.search(html)
            if match:
                return match.group(1) or match.group(2)

            return None

    except Exception as e:
        logger.debug(f"Failed to extract og:image from {url}: {e}")
        return None


async def extract_images_batch(
    articles: list[dict[str, Any]],
    max_images: int = 6,
    timeout: float = 3.0,
) -> list[dict[str, Any]]:
    """
    Extract og:images from multiple articles in parallel.

    Args:
        articles: List of article dicts with 'url', 'title', 'publisher', 'date' fields
        max_images: Maximum number of images to extract
        timeout: Timeout per request

    Returns:
        List of image dicts with 'url', 'title', 'publisher', 'date'
    """
    if not articles:
        return []

    # Limit articles to check
    articles_to_check = articles[:max_images * 2]  # Check 2x to account for failures

    async def fetch_image(article: dict) -> dict | None:
        url = article.get("url")
        if not url:
            return None

        img_url = await extract_og_image(url, timeout=timeout)
        if not img_url:
            return None

        return {
            "url": img_url,
            "title": article.get("title", "")[:50],
            "publisher": article.get("publisher"),
            "date": article.get("date"),
            "article_url": url,
        }

    # Run in parallel
    tasks = [fetch_image(a) for a in articles_to_check]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter successful results
    images = []
    for result in results:
        if isinstance(result, dict) and result.get("url"):
            images.append(result)
            if len(images) >= max_images:
                break

    return images


# BigKinds image extensions to try (in order of priority)
BIGKINDS_IMAGE_EXTENSIONS = [".jpg", ".png", ".jpeg", ".gif", ".webp"]


async def resolve_bigkinds_image_url(
    base_url: str,
    timeout: float = 2.0,
) -> str | None:
    """
    Try different image extensions for BigKinds image URLs.

    BigKinds returns image URLs without extensions, but the actual images
    require extensions like .jpg, .png, etc. This function tries each
    extension and returns the first one that works.

    Args:
        base_url: BigKinds image URL (without extension)
        timeout: Request timeout in seconds

    Returns:
        Working image URL with extension, or None if all fail
    """
    if not base_url or "bigkinds.or.kr" not in base_url:
        return base_url if base_url else None

    # If already has an extension, validate it
    if any(base_url.lower().endswith(ext) for ext in BIGKINDS_IMAGE_EXTENSIONS):
        return base_url

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        follow_redirects=True,
    ) as client:
        for ext in BIGKINDS_IMAGE_EXTENSIONS:
            test_url = f"{base_url}{ext}"
            try:
                response = await client.head(test_url)
                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    if "image" in content_type:
                        logger.debug(f"BigKinds image resolved: {test_url}")
                        return test_url
            except Exception:
                continue

    logger.debug(f"Failed to resolve BigKinds image: {base_url}")
    return None


async def resolve_bigkinds_images_batch(
    image_urls: list[str],
    timeout: float = 2.0,
) -> list[str]:
    """
    Resolve multiple BigKinds image URLs in parallel.

    Args:
        image_urls: List of BigKinds image URLs to resolve
        timeout: Timeout per request

    Returns:
        List of resolved URLs (empty string for failed ones)
    """
    if not image_urls:
        return []

    tasks = [resolve_bigkinds_image_url(url, timeout) for url in image_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [
        result if isinstance(result, str) and result else ""
        for result in results
    ]


def validate_image_url(url: str) -> bool:
    """
    Basic validation of image URL.

    Args:
        url: URL to validate

    Returns:
        True if URL looks like a valid image URL
    """
    if not url or not isinstance(url, str):
        return False

    url_lower = url.lower()

    # Must be http(s)
    if not url_lower.startswith(('http://', 'https://')):
        return False

    # Check for common image extensions or image CDN patterns
    image_patterns = [
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '/image/', '/images/', '/img/', '/photo/',
        'wimg.', 'img.', 'image.', 'cdn.',
    ]

    return any(pattern in url_lower for pattern in image_patterns)
