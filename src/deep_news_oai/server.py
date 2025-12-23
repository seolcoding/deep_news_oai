"""FastMCP server for Deep News OAI - OpenAI ChatGPT App."""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp.server.fastmcp import FastMCP

from deep_news_oai.core.client import BigKindsClient
from deep_news_oai.core.trends import GoogleTrendsClient
from deep_news_oai.core.images import resolve_bigkinds_images_batch
from deep_news_oai.responses.builder import OAIResponse, search_response, article_response, trending_response, timeline_response, perspectives_response, report_response

logger = logging.getLogger(__name__)

# Transport security settings for external access
from mcp.server.transport_security import TransportSecuritySettings

transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,  # Allow access via Cloudflare Tunnel
)

# Create FastMCP server
mcp = FastMCP("deep-news-oai", transport_security=transport_security)

# Global clients (initialized in lifespan)
_client: BigKindsClient | None = None
_trends_client: GoogleTrendsClient | None = None


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Server lifecycle management."""
    global _client, _trends_client

    logger.info("Starting Deep News OAI server...")
    _client = BigKindsClient()
    _trends_client = GoogleTrendsClient()

    yield {"client": _client, "trends": _trends_client}

    logger.info("Shutting down Deep News OAI server...")
    if _client:
        await _client.close()


mcp.settings.lifespan = lifespan


# =============================================================================
# TOOLS: Search
# =============================================================================

@mcp.tool(
    annotations={
        "title": "Search Korean News",
        "readOnlyHint": True,
        "openWorldHint": True,  # Calls external BigKinds API
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def search_korean_news(
    keyword: str,
    start_date: str,
    end_date: str,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """
    Search Korean news articles from BigKinds database.

    Use this when the user wants to:
    - Search for news about a topic in Korean media
    - Find articles about events, people, or issues in Korea
    - Research news coverage on specific keywords

    Do not use for:
    - International news not covered by Korean media
    - Real-time breaking news (data has ~1 day delay)

    Args:
        keyword: Search keyword (Korean or English)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        page: Page number (default 1)
        page_size: Results per page (default 20, max 100)

    Returns:
        Search results with articles in OAI format
    """
    if not _client:
        return OAIResponse.error("SERVER_ERROR", "서버가 초기화되지 않았습니다.")

    from deep_news_oai.core.models import SearchRequest

    try:
        request = SearchRequest(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            start_no=page,
            result_number=min(page_size, 100),
        )
        response = await _client.search(request)

        if not response.success:
            return OAIResponse.error(
                "API_ERROR",
                response.error_message or "검색에 실패했습니다.",
            )

        articles = [a.to_full() for a in response.articles]
        return search_response(
            total_count=response.total_count,
            page=page,
            page_size=page_size,
            articles=articles,
            keyword=keyword,
        )

    except Exception as e:
        logger.exception("Search error")
        return OAIResponse.error("SEARCH_ERROR", str(e))


@mcp.tool(
    annotations={
        "title": "Get Article Detail",
        "readOnlyHint": True,
        "openWorldHint": True,  # Calls external BigKinds API
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def get_article_detail(
    news_id: str,
) -> dict[str, Any]:
    """
    Get detailed information about a specific news article.

    Use this when the user wants to:
    - Read the full content of a specific article
    - Get more details about an article from search results
    - View article with proper formatting and metadata

    Args:
        news_id: Article ID from search results (e.g., "01101202.20241220110009001")

    Returns:
        Article detail with title, content, publisher, date, and URL in OAI format
    """
    if not _client:
        return OAIResponse.error("SERVER_ERROR", "서버가 초기화되지 않았습니다.")

    from deep_news_oai.core.models import SearchRequest

    try:
        # Extract provider_code and date from news_id
        # Format: PROVIDERCODE.YYYYMMDD... (e.g., "01101202.20241220110009001")
        parts = news_id.split(".")
        if len(parts) < 2 or len(parts[1]) < 8:
            return OAIResponse.error(
                "INVALID_ID",
                f"잘못된 기사 ID 형식입니다: {news_id}",
            )

        provider_code = parts[0]
        date_str = parts[1][:8]  # YYYYMMDD
        search_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

        # Search by provider_code on the specific date
        request = SearchRequest(
            keyword="",  # Empty keyword to get all articles
            start_date=search_date,
            end_date=search_date,
            start_no=1,
            result_number=200,  # Get more to find the article
            provider_codes=[provider_code],
        )
        response = await _client.search(request)

        # Find the exact article by news_id
        article = None
        for a in response.articles:
            if a.news_id == news_id:
                article = a
                break

        if not article:
            return OAIResponse.error(
                "NOT_FOUND",
                f"기사를 찾을 수 없습니다: {news_id}",
            )

        # Extract image URL if available
        images = []
        if article.raw_data:
            img_url = article.raw_data.get("IMAGES")
            if img_url:
                # Resolve with extension fallback
                from deep_news_oai.core.images import resolve_bigkinds_image_url
                resolved_url = await resolve_bigkinds_image_url(img_url)
                if resolved_url:
                    images.append(resolved_url)

        return article_response(
            news_id=article.news_id or news_id,
            title=article.title,
            content_text=article.content or "",
            publisher=article.publisher or "Unknown",
            published_date=article.news_date or "",
            url=article.url,
            author=article.byline,
            images=images,
        )

    except Exception as e:
        logger.exception("Article detail error")
        return OAIResponse.error("DETAIL_ERROR", str(e))


@mcp.tool(
    annotations={
        "title": "Count News Articles",
        "readOnlyHint": True,
        "openWorldHint": True,  # Calls external BigKinds API
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def count_news_articles(
    keyword: str,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """
    Get the count of news articles without fetching them.

    Use this when the user wants to:
    - Know how many articles exist for a topic
    - Estimate data volume before deep analysis

    Args:
        keyword: Search keyword
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Article count in OAI format
    """
    if not _client:
        return OAIResponse.error("SERVER_ERROR", "서버가 초기화되지 않았습니다.")

    try:
        count = await _client.get_total_count(keyword, start_date, end_date)

        return OAIResponse.inline(
            structured={"keyword": keyword, "count": count, "start_date": start_date, "end_date": end_date},
            content=f"'{keyword}' 관련 뉴스가 {count:,}건 있습니다. ({start_date} ~ {end_date})",
        )

    except Exception as e:
        logger.exception("Count error")
        return OAIResponse.error("COUNT_ERROR", str(e))


# =============================================================================
# TOOLS: Utils
# =============================================================================

@mcp.tool(
    annotations={
        "title": "Get Korean Time",
        "readOnlyHint": True,
        "openWorldHint": False,  # No external API call
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def get_korean_time() -> dict[str, Any]:
    """
    Get current Korean time (KST).

    Use this when the user asks for current time or today's date.

    Returns:
        Current Korean time in OAI format
    """
    from datetime import datetime, timezone, timedelta

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    return OAIResponse.inline(
        structured={
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timezone": "KST (UTC+9)",
        },
        content=f"현재 한국 시간: {now.strftime('%Y년 %m월 %d일 %H시 %M분')}",
    )


@mcp.tool(
    annotations={
        "title": "List News Providers",
        "readOnlyHint": True,
        "openWorldHint": False,  # Static data, no external API
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def list_news_providers() -> dict[str, Any]:
    """
    List available Korean news providers (언론사).

    Use this when the user wants to:
    - Know which news sources are available
    - Filter search by specific publishers

    Returns:
        List of news providers in OAI format
    """
    # Major Korean news providers
    providers = {
        "전국일간지": ["경향신문", "국민일보", "동아일보", "문화일보", "서울신문", "세계일보", "조선일보", "중앙일보", "한겨레", "한국일보"],
        "경제지": ["매일경제", "머니투데이", "서울경제", "아시아경제", "이데일리", "조선비즈", "파이낸셜뉴스", "한국경제"],
        "방송사": ["KBS", "MBC", "SBS", "JTBC", "채널A", "TV조선", "MBN", "YTN"],
        "통신사": ["연합뉴스", "뉴시스", "뉴스1"],
    }

    total_count = sum(len(v) for v in providers.values())

    return OAIResponse.inline(
        structured={"provider_count": total_count, "categories": list(providers.keys())},
        content=f"총 {total_count}개 언론사가 등록되어 있습니다. 주요 언론사: {', '.join(providers['전국일간지'][:5])}...",
    )


@mcp.tool(
    annotations={
        "title": "Find News Category",
        "readOnlyHint": True,
        "openWorldHint": False,  # Static lookup, no external API
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def find_news_category(query: str) -> dict[str, Any]:
    """
    Search for news category or provider code.

    Use this when the user wants to:
    - Find the code for a specific news category
    - Look up provider information

    Args:
        query: Category or provider name to search

    Returns:
        Matching categories/providers in OAI format
    """
    categories = {
        "정치": "001000000",
        "경제": "002000000",
        "사회": "003000000",
        "문화": "004000000",
        "국제": "005000000",
        "지역": "006000000",
        "스포츠": "007000000",
        "IT_과학": "008000000",
    }

    query_lower = query.lower()
    matches = []

    for name, code in categories.items():
        if query_lower in name.lower():
            matches.append({"name": name, "code": code, "type": "category"})

    if matches:
        return OAIResponse.inline(
            structured={"query": query, "matches": matches},
            content=f"'{query}' 검색 결과: {', '.join(m['name'] for m in matches)}",
        )
    else:
        return OAIResponse.inline(
            structured={"query": query, "matches": []},
            content=f"'{query}'에 해당하는 카테고리를 찾을 수 없습니다. 가능한 카테고리: {', '.join(categories.keys())}",
        )


# =============================================================================
# TOOLS: Trending
# =============================================================================

@mcp.tool(
    annotations={
        "title": "Get Trending Now",
        "readOnlyHint": True,
        "openWorldHint": False,  # Uses cached data, no external API call
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def get_trending_now(limit: int = 10) -> dict[str, Any]:
    """
    Get real-time trending search keywords from Google Trends Korea.

    Use this when the user wants to:
    - Know what topics are trending right now in Korea
    - Discover popular search keywords
    - Find hot issues to research further
    - Get inspiration for news topics to explore

    Do not use for:
    - Historical trend analysis (use search_korean_news with date range)
    - Specific news article search (use search_korean_news)

    Args:
        limit: Number of trending items to return (default 10, max 50)

    Returns:
        Trending keywords with search volume and related terms in OAI format
    """
    if not _trends_client:
        return OAIResponse.error("SERVER_ERROR", "트렌드 클라이언트가 초기화되지 않았습니다.")

    try:
        # Get trending items
        trending_items = _trends_client.get_trending(limit=min(limit, 50))

        if not trending_items:
            return OAIResponse.inline(
                structured={"trending": [], "count": 0},
                content="현재 트렌딩 데이터를 가져올 수 없습니다. 캐시를 업데이트해주세요.",
            )

        # Convert to response format
        issues = []
        for item in trending_items:
            issues.append({
                "rank": item.rank,
                "title": item.keyword,
                "keywords": item.related_terms[:5],
                "search_volume": item.search_volume,
                "growth_rate": item.growth_rate,
            })

        # Get cache status for metadata
        cache_status = _trends_client.get_cache_status()
        scraped_at = trending_items[0].scraped_at if trending_items else None

        from datetime import datetime, timezone, timedelta
        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        date_str = now.strftime("%Y-%m-%d")

        return trending_response(
            issues=issues,
            date=date_str,
            extra_meta={
                "cache_valid": cache_status.get("cache_valid", False),
                "scraped_at": scraped_at.isoformat() if scraped_at else None,
            }
        )

    except Exception as e:
        logger.exception("Trending fetch error")
        return OAIResponse.error("TRENDING_ERROR", str(e))


@mcp.tool(
    annotations={
        "title": "Refresh Trends Cache",
        "readOnlyHint": False,
        "openWorldHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def refresh_trends_cache(data_path: str) -> dict[str, Any]:
    """
    Refresh Google Trends cache from a data file.

    Use this when:
    - Trends data is stale and needs updating
    - A new trends CSV file is available

    Args:
        data_path: Path to the Google Trends CSV file

    Returns:
        Cache refresh status in OAI format
    """
    if not _trends_client:
        return OAIResponse.error("SERVER_ERROR", "트렌드 클라이언트가 초기화되지 않았습니다.")

    try:
        success = _trends_client.refresh_cache(data_path)

        if success:
            status = _trends_client.get_cache_status()
            return OAIResponse.inline(
                structured={
                    "success": True,
                    "items_count": status.get("items_count", 0),
                },
                content=f"트렌드 캐시가 업데이트되었습니다. {status.get('items_count', 0)}개 항목 로드.",
            )
        else:
            return OAIResponse.error("CACHE_ERROR", "캐시 업데이트에 실패했습니다.")

    except Exception as e:
        logger.exception("Cache refresh error")
        return OAIResponse.error("CACHE_ERROR", str(e))


# =============================================================================
# TOOLS: Analysis
# =============================================================================

@mcp.tool(
    annotations={
        "title": "Analyze News Timeline",
        "readOnlyHint": True,
        "openWorldHint": True,  # Calls external BigKinds API
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def analyze_timeline(
    keyword: str,
    start_date: str,
    end_date: str,
    granularity: str = "day",
) -> dict[str, Any]:
    """
    Analyze news coverage timeline for a keyword (person, issue, topic).

    Use this when the user wants to:
    - See how news coverage of a topic evolved over time
    - Identify peak coverage dates for a person or event
    - Understand the temporal pattern of news reporting
    - Track the lifecycle of a news story

    Args:
        keyword: Search keyword (person name, topic, or issue)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        granularity: Time grouping - "day", "week", or "month" (default: "day")

    Returns:
        Timeline analysis with daily/weekly/monthly article counts and top headlines
    """
    if not _client:
        return OAIResponse.error("SERVER_ERROR", "서버가 초기화되지 않았습니다.")

    from datetime import datetime, timedelta
    from collections import defaultdict

    from deep_news_oai.core.models import SearchRequest

    try:
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Limit date range to avoid too many API calls
        max_days = 365
        if (end_dt - start_dt).days > max_days:
            return OAIResponse.error(
                "INVALID_RANGE",
                f"날짜 범위가 너무 넓습니다. 최대 {max_days}일까지 분석 가능합니다.",
            )

        # Fetch articles (up to 1000 for analysis)
        request = SearchRequest(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            start_no=1,
            result_number=1000,
            sort_method="date",
        )
        response = await _client.search(request)

        if not response.success:
            return OAIResponse.error(
                "API_ERROR",
                response.error_message or "검색에 실패했습니다.",
            )

        # Group articles by date
        date_groups: dict[str, list] = defaultdict(list)

        for article in response.articles:
            if not article.news_date:
                continue

            # Extract date part (YYYY-MM-DD)
            article_date = article.news_date[:10]

            # Apply granularity
            if granularity == "week":
                dt = datetime.strptime(article_date, "%Y-%m-%d")
                # Get start of week (Monday)
                week_start = dt - timedelta(days=dt.weekday())
                group_key = week_start.strftime("%Y-%m-%d")
            elif granularity == "month":
                group_key = article_date[:7]  # YYYY-MM
            else:  # day
                group_key = article_date

            date_groups[group_key].append(article)

        # Build timeline data
        timeline = []
        for date_key in sorted(date_groups.keys()):
            articles = date_groups[date_key]
            publishers = {}
            for a in articles:
                pub = a.publisher or "Unknown"
                publishers[pub] = publishers.get(pub, 0) + 1

            # Top 3 publishers
            top_publishers = sorted(publishers.items(), key=lambda x: -x[1])[:3]

            # Representative headlines (top 3 by position)
            headlines = [a.title for a in articles[:3]]

            timeline.append({
                "date": date_key,
                "count": len(articles),
                "publishers": [{"name": p[0], "count": p[1]} for p in top_publishers],
                "headlines": headlines,
            })

        return timeline_response(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            timeline=timeline,
            total_articles=response.total_count,
        )

    except ValueError as e:
        return OAIResponse.error("INVALID_DATE", f"날짜 형식 오류: {e}")
    except Exception as e:
        logger.exception("Timeline analysis error")
        return OAIResponse.error("ANALYSIS_ERROR", str(e))


@mcp.tool(
    annotations={
        "title": "Compare Publisher Perspectives",
        "readOnlyHint": True,
        "openWorldHint": True,  # Calls external BigKinds API
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def compare_perspectives(
    keyword: str,
    start_date: str,
    end_date: str,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Compare how different news publishers cover the same topic.

    Use this when the user wants to:
    - Compare coverage across different news outlets
    - Understand media bias or perspective differences
    - See which publishers cover a topic most frequently
    - Analyze headline framing differences between publishers

    Args:
        keyword: Search keyword (topic, person, or issue)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        limit: Maximum number of publishers to compare (default: 10)

    Returns:
        Publisher comparison with article counts, representative headlines, and coverage patterns
    """
    if not _client:
        return OAIResponse.error("SERVER_ERROR", "서버가 초기화되지 않았습니다.")

    from collections import defaultdict

    from deep_news_oai.core.models import SearchRequest

    try:
        # Fetch articles (up to 1000 for analysis)
        request = SearchRequest(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            start_no=1,
            result_number=1000,
            sort_method="date",
        )
        response = await _client.search(request)

        if not response.success:
            return OAIResponse.error(
                "API_ERROR",
                response.error_message or "검색에 실패했습니다.",
            )

        # Group articles by publisher
        publisher_groups: dict[str, list] = defaultdict(list)

        for article in response.articles:
            publisher = article.publisher or "Unknown"
            publisher_groups[publisher].append(article)

        # Build publisher data
        publishers = []
        for pub_name, articles in publisher_groups.items():
            # Sort by date (most recent first)
            articles_sorted = sorted(
                articles,
                key=lambda a: a.news_date or "",
                reverse=True
            )

            # Get date range for this publisher
            dates = [a.news_date[:10] for a in articles_sorted if a.news_date]
            first_date = min(dates) if dates else None
            last_date = max(dates) if dates else None

            # Representative headlines (first 5)
            headlines = [
                {
                    "title": a.title,
                    "date": a.news_date[:10] if a.news_date else None,
                }
                for a in articles_sorted[:5]
            ]

            # Category distribution
            categories: dict[str, int] = {}
            for a in articles:
                cat = a.category or "기타"
                categories[cat] = categories.get(cat, 0) + 1

            top_categories = sorted(categories.items(), key=lambda x: -x[1])[:3]

            publishers.append({
                "name": pub_name,
                "count": len(articles),
                "first_date": first_date,
                "last_date": last_date,
                "headlines": headlines,
                "categories": [{"name": c[0], "count": c[1]} for c in top_categories],
            })

        # Sort by article count (descending) and limit
        publishers = sorted(publishers, key=lambda x: -x["count"])[:limit]

        return perspectives_response(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            publishers=publishers,
            total_articles=response.total_count,
        )

    except Exception as e:
        logger.exception("Perspectives analysis error")
        return OAIResponse.error("ANALYSIS_ERROR", str(e))


@mcp.tool(
    annotations={
        "title": "Generate Deep Analysis Report",
        "readOnlyHint": True,
        "openWorldHint": True,  # Calls external BigKinds API
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def generate_report(
    keyword: str,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """
    Generate a comprehensive deep analysis report combining timeline and publisher perspectives.

    Use this when the user wants to:
    - Get a complete overview of news coverage for a topic/person/issue
    - See both temporal trends AND publisher comparison in one view
    - Understand key events and turning points in news coverage
    - Generate a visual report with charts and article images

    This combines:
    - Timeline analysis (vertical: how coverage evolved over time)
    - Publisher comparison (horizontal: how different outlets covered it)
    - Key events detection (significant spikes in coverage)
    - Article images gallery

    Args:
        keyword: Search keyword (person, topic, or issue)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Comprehensive report with timeline, publishers, events, and images
    """
    if not _client:
        return OAIResponse.error("SERVER_ERROR", "서버가 초기화되지 않았습니다.")

    from datetime import datetime, timedelta
    from collections import defaultdict

    from deep_news_oai.core.models import SearchRequest

    try:
        # Fetch articles (up to 1000 for analysis)
        request = SearchRequest(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            start_no=1,
            result_number=1000,
            sort_method="date",
        )
        response = await _client.search(request)

        if not response.success:
            return OAIResponse.error(
                "API_ERROR",
                response.error_message or "검색에 실패했습니다.",
            )

        if not response.articles:
            return OAIResponse.error(
                "NO_DATA",
                f"'{keyword}' 관련 기사를 찾을 수 없습니다.",
            )

        # ========== Timeline Analysis ==========
        date_groups: dict[str, list] = defaultdict(list)
        for article in response.articles:
            if article.news_date:
                date_key = article.news_date[:10]
                date_groups[date_key].append(article)

        timeline = []
        for date_key in sorted(date_groups.keys()):
            articles = date_groups[date_key]
            timeline.append({
                "date": date_key,
                "count": len(articles),
                "headlines": [a.title for a in articles[:2]],
            })

        # ========== Publisher Analysis ==========
        publisher_groups: dict[str, list] = defaultdict(list)
        for article in response.articles:
            pub = article.publisher or "Unknown"
            publisher_groups[pub].append(article)

        publishers = []
        for pub_name, articles in publisher_groups.items():
            publishers.append({
                "name": pub_name,
                "count": len(articles),
                "headlines": [a.title for a in articles[:3]],
            })
        publishers = sorted(publishers, key=lambda x: -x["count"])[:10]

        # ========== Key Events (spikes) ==========
        key_events = []
        if len(timeline) >= 3:
            counts = [t["count"] for t in timeline]
            avg_count = sum(counts) / len(counts)
            threshold = avg_count * 2  # 2x average = significant event

            for i, t in enumerate(timeline):
                if t["count"] >= threshold:
                    # Calculate growth from previous day
                    prev_count = timeline[i-1]["count"] if i > 0 else 0
                    growth = ((t["count"] - prev_count) / prev_count * 100) if prev_count > 0 else 0

                    key_events.append({
                        "date": t["date"],
                        "count": t["count"],
                        "growth": f"+{growth:.0f}%" if growth > 0 else f"{growth:.0f}%",
                        "headline": t["headlines"][0] if t["headlines"] else None,
                        "is_peak": False,
                    })

        # Mark absolute peak
        if timeline:
            peak = max(timeline, key=lambda x: x["count"])
            peak_event = next((e for e in key_events if e["date"] == peak["date"]), None)
            if peak_event:
                peak_event["is_peak"] = True
            else:
                key_events.insert(0, {
                    "date": peak["date"],
                    "count": peak["count"],
                    "growth": "PEAK",
                    "headline": peak["headlines"][0] if peak["headlines"] else None,
                    "is_peak": True,
                })

        key_events = sorted(key_events, key=lambda x: -x["count"])[:5]

        # ========== Article Images (with extension fallback) ==========
        # Collect raw image URLs and article metadata
        raw_image_data = []
        seen_urls = set()
        for article in response.articles:
            if article.raw_data and len(raw_image_data) < 12:  # Collect extra for fallbacks
                img_url = (
                    article.raw_data.get("IMAGES") or
                    article.raw_data.get("images") or
                    article.raw_data.get("IMAGE_URL") or
                    article.raw_data.get("imageUrl") or
                    article.raw_data.get("THUMBNAIL") or
                    article.raw_data.get("thumbnail")
                )
                if img_url and img_url not in seen_urls:
                    seen_urls.add(img_url)
                    raw_image_data.append({
                        "raw_url": img_url,
                        "title": article.title[:50],
                        "publisher": article.publisher,
                        "date": article.news_date[:10] if article.news_date else None,
                    })

        # Resolve BigKinds URLs with extension fallback (parallel)
        raw_urls = [d["raw_url"] for d in raw_image_data]
        resolved_urls = await resolve_bigkinds_images_batch(raw_urls, timeout=2.0)

        # Build final images list (only successfully resolved)
        images = []
        for i, resolved_url in enumerate(resolved_urls):
            if resolved_url and len(images) < 6:  # Max 6 images
                images.append({
                    "url": resolved_url,
                    "title": raw_image_data[i]["title"],
                    "publisher": raw_image_data[i]["publisher"],
                    "date": raw_image_data[i]["date"],
                })

        # ========== Summary ==========
        peak_item = max(timeline, key=lambda x: x["count"]) if timeline else {}
        summary = {
            "total_articles": response.total_count,
            "fetched_articles": len(response.articles),
            "publisher_count": len(publisher_groups),
            "date_range_days": len(timeline),
            "peak_date": peak_item.get("date"),
            "peak_count": peak_item.get("count", 0),
            "avg_daily": round(len(response.articles) / max(len(timeline), 1), 1),
        }

        return report_response(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            summary=summary,
            timeline=timeline,
            publishers=publishers,
            key_events=key_events,
            images=images,
        )

    except Exception as e:
        logger.exception("Report generation error")
        return OAIResponse.error("REPORT_ERROR", str(e))


# =============================================================================
# WIDGETS: Resource registration (with LRU caching)
# =============================================================================

from deep_news_oai.widgets.loader import load_widget


@mcp.resource(
    "widget://search_results",
    mime_type="text/html+skybridge",
    description="뉴스 검색 결과를 카드 UI로 표시합니다. 기사 제목, 언론사, 날짜를 보여주며 클릭하면 상세 조회를 요청합니다."
)
def search_results_widget() -> str:
    """Search results widget template - displays news articles in card format."""
    return load_widget("search_results")


@mcp.resource(
    "widget://article_detail",
    mime_type="text/html+skybridge",
    description="뉴스 기사 상세 내용을 표시합니다. 제목, 본문, 언론사, 날짜, 원문 링크를 포함합니다."
)
def article_detail_widget() -> str:
    """Article detail widget template - displays full article content."""
    return load_widget("article_detail")


@mcp.resource(
    "widget://trending_issues",
    mime_type="text/html+skybridge",
    description="오늘의 인기 뉴스 이슈를 순위별로 표시합니다. 키워드와 관련 기사 수를 포함합니다."
)
def trending_issues_widget() -> str:
    """Trending issues widget template - displays top news topics ranked by popularity."""
    return load_widget("trending_issues")


@mcp.resource(
    "widget://timeline",
    mime_type="text/html+skybridge",
    description="뉴스 타임라인 분석을 차트와 리스트로 표시합니다. 일별/주별/월별 기사량과 주요 헤드라인을 포함합니다."
)
def timeline_widget() -> str:
    """Timeline widget template - displays news coverage over time with chart and details."""
    return load_widget("timeline")


@mcp.resource(
    "widget://perspectives",
    mime_type="text/html+skybridge",
    description="언론사별 보도 비교를 표시합니다. 기사 수, 대표 헤드라인, 카테고리 분포를 포함합니다."
)
def perspectives_widget() -> str:
    """Perspectives widget template - displays publisher comparison with headlines and stats."""
    return load_widget("perspectives")


@mcp.resource(
    "widget://report",
    mime_type="text/html+skybridge",
    description="심층 분석 리포트를 표시합니다. 타임라인 차트, 언론사 비교, 주요 이벤트, 기사 이미지를 포함하며 인포그래픽 생성을 요청할 수 있습니다."
)
def report_widget() -> str:
    """Report widget template - comprehensive analysis with images, charts, and infographic generation."""
    return load_widget("report")


# =============================================================================
# HEALTH CHECK
# =============================================================================

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount


async def health_check(request):
    """Health check endpoint for Docker/K8s."""
    return JSONResponse({
        "status": "healthy",
        "service": "deep-news-oai",
        "client_initialized": _client is not None,
    })


# Create combined app with health check
health_routes = [
    Route("/health", health_check),
]

# Middleware to allow any host
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Wrap MCP server with health check
app = Starlette(
    routes=[
        *health_routes,
        Mount("/", app=mcp.sse_app()),
    ],
    middleware=[
        Middleware(TrustedHostMiddleware, allowed_hosts=["*"]),
    ],
)


# =============================================================================
# SERVER ENTRY POINT
# =============================================================================

def run_server():
    """Run the MCP server."""
    import uvicorn
    uvicorn.run(
        "deep_news_oai.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    run_server()
