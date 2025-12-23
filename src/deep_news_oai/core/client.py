"""Async BigKinds HTTP API client using httpx."""

import asyncio
import logging
import os

import httpx

from deep_news_oai.core.models import SearchRequest, SearchResponse

logger = logging.getLogger(__name__)


class BigKindsClient:
    """Async HTTP client for BigKinds news API."""

    BASE_URL = "https://www.bigkinds.or.kr"
    API_URL = f"{BASE_URL}/api/news/search.do"

    DEFAULT_HEADERS = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Host": "www.bigkinds.or.kr",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/v2/news/index.do",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    def __init__(
        self,
        timeout: int = 60,
        max_retries: int = 3,
        rate_limit_delay: float = 0.5,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.DEFAULT_HEADERS,
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                verify=False,  # BigKinds has SSL issues
                follow_redirects=True,
            )
        return self._client

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Perform async search request to BigKinds API.

        Args:
            request: Search request parameters

        Returns:
            Search response with articles
        """
        client = await self._get_client()
        payload = request.to_api_payload()

        logger.debug(
            f"BigKinds API request: keyword='{request.keyword}', "
            f"page={request.start_no}, count={request.result_number}"
        )

        last_error = None
        for attempt in range(self.max_retries):
            try:
                await asyncio.sleep(self.rate_limit_delay)

                response = await client.post(self.API_URL, json=payload)
                response.raise_for_status()
                data = response.json()

                search_response = SearchResponse.from_api_response(data, request, raw_response=data)

                logger.debug(
                    f"BigKinds API response: success={search_response.success}, "
                    f"total={search_response.total_count}, "
                    f"fetched={len(search_response.articles)}"
                )

                return search_response

            except httpx.TimeoutException:
                last_error = f"Request timeout after {self.timeout} seconds"
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries}: {last_error}")

            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries}: {last_error}")

            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries}: {last_error}")

            # Exponential backoff
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)

        logger.error(f"All {self.max_retries} attempts failed: {last_error}")
        return SearchResponse(
            success=False,
            error_message=last_error,
            keyword=request.keyword,
            date_range=f"{request.start_date} to {request.end_date}",
        )

    async def get_total_count(self, keyword: str, start_date: str, end_date: str) -> int:
        """Get total count of articles without fetching them."""
        request = SearchRequest(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            start_no=1,
            result_number=1,
        )
        response = await self.search(request)
        return response.total_count if response.success else 0

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            logger.debug("BigKinds client closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
