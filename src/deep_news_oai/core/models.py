"""Data models for BigKinds news API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NewsArticle(BaseModel):
    """Model for a single news article."""

    news_id: str | None = Field(None, description="Article ID")
    title: str = Field(..., description="Article title")
    content: str | None = Field(None, description="Article content/summary")

    publisher: str | None = Field(None, description="Publisher name")
    provider_code: str | None = Field(None, description="Provider code")
    category: str | None = Field(None, description="News category")
    category_code: str | None = Field(None, description="Category code")

    news_date: str | None = Field(None, description="Publication date")
    url: str | None = Field(None, description="Article URL")
    byline: str | None = Field(None, description="Author/reporter")

    analysis_flag: str | None = Field(None, description="Analysis availability flag")
    is_analysis: bool | None = Field(None, description="Whether article is analyzed")

    raw_data: dict | None = Field(None, description="Original API response data")

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_api_response(cls, data: dict) -> "NewsArticle":
        """Create NewsArticle from API response data."""
        mapped = {
            "news_id": data.get("NEWS_ID") or data.get("newsId"),
            "title": data.get("TITLE") or data.get("title", ""),
            "content": data.get("CONTENT") or data.get("content") or data.get("SUMMARY"),
            "publisher": data.get("PROVIDER") or data.get("PUBLISHER") or data.get("publisher"),
            "provider_code": data.get("PROVIDER_CODE") or data.get("providerCode"),
            "category": data.get("CATEGORY") or data.get("category"),
            "category_code": data.get("CATEGORY_CODE") or data.get("categoryCode"),
            "news_date": data.get("NEWS_DATE") or data.get("DATE") or data.get("newsDate"),
            "url": data.get("PROVIDER_LINK_PAGE") or data.get("URL") or data.get("url"),
            "byline": data.get("BYLINE") or data.get("byline") or data.get("byLine"),
            "analysis_flag": data.get("ANALYSIS_FLAG") or data.get("analysisFlag"),
            "is_analysis": data.get("IS_ANALYSIS") or data.get("isAnalysis"),
            "raw_data": data,
        }
        return cls(**{k: v for k, v in mapped.items() if v is not None})

    def to_structured(self) -> dict:
        """Convert to minimal structured format for OAI."""
        return {
            "news_id": self.news_id,
            "title": self.title,
            "publisher": self.publisher,
            "date": self.news_date[:10] if self.news_date else None,
        }

    def to_full(self) -> dict:
        """Convert to full format for widget _meta."""
        return {
            "news_id": self.news_id,
            "title": self.title,
            "summary": self.content,
            "publisher": self.publisher,
            "category": self.category,
            "published_date": self.news_date,
            "url": self.url,
            "author": self.byline,
        }


class SearchRequest(BaseModel):
    """Model for BigKinds API search request."""

    keyword: str = Field(..., description="Search keyword")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")

    start_no: int = Field(1, description="Starting page number")
    result_number: int = Field(100, description="Number of results per page")

    provider_codes: list[str] = Field(default_factory=list, description="Provider codes filter")
    category_codes: list[str] = Field(default_factory=list, description="Category codes filter")

    search_scope_type: str = Field("1", description="Search scope type")
    search_filter_type: str = Field("1", description="Search filter type")
    sort_method: str = Field("date", description="Sort method")

    is_tm_usable: bool = Field(False, description="Text mining usable")
    is_not_tm_usable: bool = Field(False, description="Text mining not usable")
    editorial_is: bool = Field(False, description="Editorial filter")

    def to_api_payload(self) -> dict[str, Any]:
        """Convert to BigKinds API payload format."""
        return {
            "indexName": "news",
            "searchKey": self.keyword,
            "searchKeys": [{}],
            "byLine": "",
            "searchFilterType": self.search_filter_type,
            "searchScopeType": self.search_scope_type,
            "searchSortType": "date",
            "sortMethod": self.sort_method,
            "mainTodayPersonYn": "",
            "startDate": self.start_date,
            "endDate": self.end_date,
            "newsIds": [],
            "categoryCodes": self.category_codes,
            "providerCodes": self.provider_codes,
            "incidentCodes": [],
            "networkNodeType": "",
            "topicOrigin": "",
            "dateCodes": [],
            "editorialIs": self.editorial_is,
            "startNo": self.start_no,
            "resultNumber": self.result_number,
            "isTmUsable": self.is_tm_usable,
            "isNotTmUsable": self.is_not_tm_usable,
        }


class SearchResponse(BaseModel):
    """Model for BigKinds API search response."""

    success: bool = Field(..., description="Request success status")
    total_count: int = Field(0, description="Total number of articles found")
    articles: list[NewsArticle] = Field(default_factory=list, description="List of articles")

    page_number: int = Field(1, description="Current page number")
    per_page: int = Field(100, description="Results per page")

    keyword: str | None = Field(None, description="Search keyword")
    date_range: str | None = Field(None, description="Date range searched")
    search_time: datetime = Field(
        default_factory=datetime.now, description="When search was performed"
    )

    error_message: str | None = Field(None, description="Error message if failed")
    error_code: str | None = Field(None, description="Error code if failed")

    raw_response: dict | None = Field(None, description="Original API response")

    @classmethod
    def from_api_response(
        cls, data: dict, request: SearchRequest, raw_response: dict | None = None
    ) -> "SearchResponse":
        """Create SearchResponse from API response data."""
        articles = []
        if data.get("resultList"):
            articles = [
                NewsArticle.from_api_response(article_data) for article_data in data["resultList"]
            ]

        return cls(
            success=data.get("success", False),
            total_count=data.get("totalCount", 0),
            articles=articles,
            page_number=request.start_no,
            per_page=request.result_number,
            keyword=request.keyword,
            date_range=f"{request.start_date} to {request.end_date}",
            error_message=data.get("errorMessage"),
            error_code=data.get("errorCode"),
            raw_response=raw_response or data,
        )
