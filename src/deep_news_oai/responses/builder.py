"""OpenAI Apps SDK response builder.

Builds the "3형제" response format:
- structuredContent: Minimal JSON for the model (affects token usage)
- content: Text summary for model response composition
- _meta: Widget-only data (not exposed to model)
"""

from typing import Any


# Widget CSP: Allowed domains for external resources
# Korean news publishers for images, plus common CDNs
WIDGET_CSP_DOMAINS = [
    "*.bigkinds.or.kr",
    "*.chosun.com",
    "*.donga.com",
    "*.joongang.co.kr",
    "*.hankyung.com",
    "*.mk.co.kr",
    "*.hani.co.kr",
    "*.khan.co.kr",
    "*.kbs.co.kr",
    "*.sbs.co.kr",
    "*.mbc.co.kr",
    "*.yna.co.kr",
]


class OAIResponse:
    """Builder for OpenAI Apps SDK native responses."""

    @staticmethod
    def success(
        structured: dict[str, Any],
        content: str,
        full_data: dict[str, Any] | None = None,
        widget: str | None = None,
        extra_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build a success response in OAI 3형제 format.

        Args:
            structured: Minimal JSON for model consumption (keep small!)
            content: Human-readable text summary
            full_data: Complete data for widget rendering (goes to _meta)
            widget: Widget template name (e.g., "search_results")
            extra_meta: Additional _meta fields

        Returns:
            Dict with structuredContent, content, _meta
        """
        meta: dict[str, Any] = {}

        if widget:
            meta["openai/outputTemplate"] = f"widget://{widget}"
            # Add CSP for widget security - allows external images from news sites
            meta["openai/widgetCSP"] = WIDGET_CSP_DOMAINS

        if full_data:
            meta["full_data"] = full_data

        if extra_meta:
            meta.update(extra_meta)

        return {
            "structuredContent": structured,
            "content": content,
            "_meta": meta,
        }

    @staticmethod
    def error(
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build an error response in OAI 3형제 format.

        Args:
            code: Error code (e.g., "INVALID_DATE", "API_ERROR")
            message: Human-readable error message (Korean)
            details: Additional error details

        Returns:
            Dict with error info in OAI format
        """
        structured = {
            "error": True,
            "code": code,
        }

        if details:
            structured["details"] = details

        return {
            "structuredContent": structured,
            "content": f"오류: {message}",
            "_meta": {
                "error_code": code,
                "error_message": message,
            },
        }

    @staticmethod
    def inline(
        structured: dict[str, Any],
        content: str,
    ) -> dict[str, Any]:
        """
        Build an inline response (no widget, just text).

        Used for simple utility tools like get_korean_time.

        Args:
            structured: Minimal JSON for model
            content: Text response

        Returns:
            Dict with structuredContent and content only
        """
        return {
            "structuredContent": structured,
            "content": content,
            "_meta": {},
        }


# Convenience functions for common response patterns

def search_response(
    total_count: int,
    page: int,
    page_size: int,
    articles: list[dict],
    keyword: str,
) -> dict[str, Any]:
    """Build search results response."""
    has_next = total_count > page * page_size

    # Structured: minimal for model
    structured = {
        "total_count": total_count,
        "page": page,
        "has_next": has_next,
        "top_articles": [
            {"title": a.get("title"), "publisher": a.get("publisher"), "date": a.get("date")}
            for a in articles[:5]  # Only top 5 for model
        ],
    }

    # Content: readable summary
    content = f"'{keyword}' 관련 뉴스 {total_count:,}건을 찾았습니다."
    if articles:
        content += f" 상위 결과: {articles[0].get('title', '')[:50]}"

    return OAIResponse.success(
        structured=structured,
        content=content,
        full_data={"articles": articles, "page": page, "total_count": total_count},
        widget="search_results",
    )


def article_response(
    news_id: str,
    title: str,
    content_text: str,
    publisher: str,
    published_date: str,
    url: str | None = None,
    author: str | None = None,
    images: list[str] | None = None,
) -> dict[str, Any]:
    """Build article detail response."""
    structured = {
        "news_id": news_id,
        "title": title,
        "publisher": publisher,
        "date": published_date[:10] if published_date else None,
        "summary": content_text[:200] if content_text else None,
    }

    full_article = {
        "news_id": news_id,
        "title": title,
        "content": content_text,
        "publisher": publisher,
        "published_date": published_date,
        "url": url,
        "author": author,
        "images": images or [],
    }

    return OAIResponse.success(
        structured=structured,
        content=f"[{publisher}] {title}",
        full_data=full_article,
        widget="article_detail",
    )


def report_response(
    keyword: str,
    start_date: str,
    end_date: str,
    summary: dict[str, Any],
    timeline: list[dict],
    publishers: list[dict],
    key_events: list[dict],
    images: list[dict],
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build comprehensive analysis report response."""
    structured = {
        "keyword": keyword,
        "period": f"{start_date} ~ {end_date}",
        "total_articles": summary.get("total_articles", 0),
        "publisher_count": summary.get("publisher_count", 0),
        "peak_date": summary.get("peak_date"),
        "peak_count": summary.get("peak_count", 0),
        "top_publishers": [
            {"name": p.get("name"), "count": p.get("count")}
            for p in publishers[:3]
        ],
    }

    content = f"'{keyword}' 심층 분석 리포트: {start_date} ~ {end_date}"
    content += f"\n총 {summary.get('total_articles', 0):,}건, {summary.get('publisher_count', 0)}개 언론사"
    if summary.get("peak_date"):
        content += f"\n피크: {summary.get('peak_date')} ({summary.get('peak_count', 0)}건)"

    return OAIResponse.success(
        structured=structured,
        content=content,
        full_data={
            "keyword": keyword,
            "start_date": start_date,
            "end_date": end_date,
            "summary": summary,
            "timeline": timeline,
            "publishers": publishers,
            "key_events": key_events,
            "images": images,
        },
        widget="report",
        extra_meta=extra_meta,
    )


def perspectives_response(
    keyword: str,
    start_date: str,
    end_date: str,
    publishers: list[dict],
    total_articles: int,
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build publisher perspectives comparison response."""
    structured = {
        "keyword": keyword,
        "period": f"{start_date} ~ {end_date}",
        "total_articles": total_articles,
        "publisher_count": len(publishers),
        "top_publishers": [
            {"name": p.get("name"), "count": p.get("count")}
            for p in publishers[:5]
        ],
    }

    content = f"'{keyword}' 언론사별 보도 비교: {len(publishers)}개 언론사, 총 {total_articles:,}건"
    if publishers:
        top = publishers[0]
        content += f" (최다: {top.get('name')} {top.get('count')}건)"

    return OAIResponse.success(
        structured=structured,
        content=content,
        full_data={
            "keyword": keyword,
            "start_date": start_date,
            "end_date": end_date,
            "publishers": publishers,
            "total_articles": total_articles,
        },
        widget="perspectives",
        extra_meta=extra_meta,
    )


def timeline_response(
    keyword: str,
    start_date: str,
    end_date: str,
    timeline: list[dict],
    total_articles: int,
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build timeline analysis response."""
    structured = {
        "keyword": keyword,
        "period": f"{start_date} ~ {end_date}",
        "total_articles": total_articles,
        "data_points": len(timeline),
        "peak_date": max(timeline, key=lambda x: x.get("count", 0)).get("date") if timeline else None,
        "peak_count": max(t.get("count", 0) for t in timeline) if timeline else 0,
    }

    content = f"'{keyword}' 타임라인 분석: {start_date} ~ {end_date}, 총 {total_articles:,}건"
    if timeline:
        peak = max(timeline, key=lambda x: x.get("count", 0))
        content += f" (피크: {peak.get('date')} {peak.get('count')}건)"

    return OAIResponse.success(
        structured=structured,
        content=content,
        full_data={
            "keyword": keyword,
            "start_date": start_date,
            "end_date": end_date,
            "timeline": timeline,
            "total_articles": total_articles,
        },
        widget="timeline",
        extra_meta=extra_meta,
    )


def trending_response(
    issues: list[dict],
    date: str,
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build trending issues response."""
    structured = {
        "date": date,
        "issue_count": len(issues),
        "top_issues": [
            {"rank": i.get("rank"), "title": i.get("title"), "keywords": i.get("keywords", [])[:3]}
            for i in issues[:5]
        ],
    }

    content = f"{date} 인기 이슈 {len(issues)}개"
    if issues:
        content += f": {issues[0].get('title', '')[:30]}"

    return OAIResponse.success(
        structured=structured,
        content=content,
        full_data={"issues": issues, "date": date},
        widget="trending_issues",
        extra_meta=extra_meta,
    )
