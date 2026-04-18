"""Async HTTP client for PocketSmith API with retry, rate limiting, circuit breaker."""

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from pocketsmith_mcp.client.circuit_breaker import CircuitBreaker
from pocketsmith_mcp.client.rate_limiter import RateLimiter
from pocketsmith_mcp.client.retry import retry_with_backoff
from pocketsmith_mcp.errors import APIError, AuthError, CircuitBreakerOpenError, RateLimitError
from pocketsmith_mcp.logger import get_logger

logger = get_logger("api_client")


@dataclass
class PaginatedResponse:
    """HTTP response body paired with pagination metadata from response headers."""

    data: list[Any] | dict[str, Any]
    total: int | None = None
    per_page: int | None = None
    page: int | None = None
    has_next: bool = False
    next_url: str | None = None
    pages_fetched: int | None = None


def _parse_pagination_headers(headers: Any) -> dict[str, Any]:
    """Parse pagination-related HTTP response headers.

    Args:
        headers: Response headers (dict or httpx Headers).

    Returns:
        Dict with keys: total, per_page, has_next, next_url.
    """
    total: int | None = None
    per_page: int | None = None
    has_next = False
    next_url: str | None = None

    total_str = headers.get("Total")
    if total_str is not None:
        try:
            total = int(total_str)
        except (ValueError, TypeError):
            pass

    per_page_str = headers.get("Per-Page")
    if per_page_str is not None:
        try:
            per_page = int(per_page_str)
        except (ValueError, TypeError):
            pass

    link_header = headers.get("Link")
    if link_header:
        for part in link_header.split(","):
            part = part.strip()
            if 'rel="next"' in part or "rel='next'" in part:
                has_next = True
                url_match = re.match(r"<([^>]+)>", part)
                if url_match:
                    next_url = url_match.group(1)
                break

    return {
        "total": total,
        "per_page": per_page,
        "has_next": has_next,
        "next_url": next_url,
    }


class PocketSmithClient:
    """
    Production-ready async client for PocketSmith API v2.

    Features:
    - Rate limiting (token bucket algorithm)
    - Retry with exponential backoff and jitter
    - Circuit breaker for fault tolerance
    - Comprehensive error handling
    """

    BASE_URL = "https://api.pocketsmith.com/v2"

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit_per_minute: int = 60,
    ):
        """
        Initialize the PocketSmith API client.

        Args:
            api_key: PocketSmith API key (X-Developer-Key)
            base_url: API base URL (default: https://api.pocketsmith.com/v2)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            rate_limit_per_minute: Maximum requests per minute
        """
        if not api_key:
            raise ValueError("api_key is required")

        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-Developer-Key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

        self._rate_limiter = RateLimiter(
            tokens_per_interval=rate_limit_per_minute,
            interval_seconds=60,
        )

        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            reset_timeout_seconds=60,
        )

    async def _request_with_headers(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any] | list[Any], Any]:
        """
        Make an authenticated API request and return body + response headers.

        This is the core implementation. Use _request() for backward-compatible
        header-discarding behaviour, or get_paginated() for pagination-aware access.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path
            params: Query parameters
            json_data: JSON request body

        Returns:
            Tuple of (parsed JSON body, response headers object).

        Raises:
            AuthError: Authentication failed (401)
            RateLimitError: Rate limit exceeded (429)
            APIError: Other API errors
            CircuitBreakerOpenError: Circuit breaker is open
        """
        # Check circuit breaker
        if not self._circuit_breaker.can_execute():
            raise CircuitBreakerOpenError()

        # Rate limiting
        await self._rate_limiter.acquire()

        # Mutable container to capture headers from the inner closure
        _state: dict[str, Any] = {"headers": None}

        async def execute_request() -> dict[str, Any] | list[Any]:
            # Clean up params - remove None values
            clean_params = None
            if params:
                clean_params = {k: v for k, v in params.items() if v is not None}

            logger.debug(f"Request: {method} {path} params={clean_params}")

            response = await self._client.request(
                method=method,
                url=path,
                params=clean_params,
                json=json_data,
            )

            logger.debug(f"Response: {response.status_code}")

            # Handle errors
            if response.status_code == 401:
                raise AuthError("Invalid API key")

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise RateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after}s",
                    retry_after=int(retry_after),
                )

            if response.status_code >= 500:
                self._circuit_breaker.record_failure()
                raise APIError(
                    f"Server error: {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                )

            if response.status_code >= 400:
                error_body = response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_body = error_json["error"]
                except Exception:
                    pass
                raise APIError(
                    f"Client error: {response.status_code}",
                    status_code=response.status_code,
                    response_body=error_body,
                )

            # Record success and capture headers for the caller
            self._circuit_breaker.record_success()
            _state["headers"] = response.headers

            # Handle empty responses
            if response.status_code == 204:
                return {}

            result: dict[str, Any] | list[Any] = response.json()
            return result

        # Retry with backoff for retryable errors
        body = await retry_with_backoff(
            execute_request,
            max_attempts=self.max_retries,
            base_delay=1.0,
            max_delay=30.0,
            retryable_errors=(httpx.TimeoutException, httpx.NetworkError),
        )

        return body, _state["headers"]

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make an authenticated API request with retry, rate limiting, and circuit breaker.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path
            params: Query parameters
            json_data: JSON request body

        Returns:
            Parsed JSON response

        Raises:
            AuthError: Authentication failed (401)
            RateLimitError: Rate limit exceeded (429)
            APIError: Other API errors
            CircuitBreakerOpenError: Circuit breaker is open
        """
        body, _ = await self._request_with_headers(
            method, path, params=params, json_data=json_data
        )
        return body

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make a GET request.

        Args:
            path: API endpoint path
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        return await self._request("GET", path, params=params)

    async def get_paginated(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> PaginatedResponse:
        """
        Make a GET request and return response body with pagination metadata.

        Reads Total, Per-Page, and Link response headers from PocketSmith and
        returns them alongside the response body. Use this instead of get() when
        you need to detect truncation or follow pagination.

        Args:
            path: API endpoint path
            params: Query parameters (page number extracted from params["page"])

        Returns:
            PaginatedResponse with data and pagination metadata.
        """
        body, headers = await self._request_with_headers("GET", path, params=params)

        pagination = _parse_pagination_headers(headers if headers is not None else {})

        page: int | None = None
        if params:
            raw_page = params.get("page")
            if raw_page is not None:
                try:
                    page = int(raw_page)
                except (ValueError, TypeError):
                    pass

        return PaginatedResponse(
            data=body,
            total=pagination["total"],
            per_page=pagination["per_page"],
            page=page,
            has_next=pagination["has_next"],
            next_url=pagination["next_url"],
        )

    async def get_all_paginated(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        max_pages: int = 10,
    ) -> PaginatedResponse:
        """
        Fetch all pages for a paginated endpoint and return merged results.

        Follows pagination by incrementing the ``page`` parameter on each request
        until either no more pages exist (``has_next=False``) or the safety limit
        is reached.

        NOTE: Auto-pagination makes multiple API calls back-to-back. With the
        default 60 req/min rate limit, fetching 10 pages takes up to ~10 seconds
        as the rate limiter throttles the burst.

        Args:
            path: API endpoint path
            params: Query parameters (``page`` will be incremented automatically)
            max_pages: Maximum number of pages to fetch (default: 10, cap: 10,000
                transactions at per_page=1000). When the limit is reached,
                ``has_next=True`` in the returned response.

        Returns:
            PaginatedResponse with merged data from all pages, ``has_next=True``
            if the safety limit was hit (more results may exist), and
            ``pages_fetched`` set to the number of pages actually retrieved.
        """
        merged_data: list[Any] = []
        current_params: dict[str, Any] = dict(params) if params else {}
        pages_fetched = 0
        last_resp: PaginatedResponse | None = None
        limit_reached = False

        while pages_fetched < max_pages:
            last_resp = await self.get_paginated(path, params=current_params)
            data = last_resp.data
            if isinstance(data, list):
                merged_data.extend(data)
            pages_fetched += 1

            if not last_resp.has_next:
                break

            # More pages exist — advance to the next page
            if last_resp.next_url is not None:
                parsed = urlparse(last_resp.next_url)
                qs = parse_qs(parsed.query)
                next_page_values = qs.get("page")
                if next_page_values:
                    current_params = {**current_params, "page": int(next_page_values[0])}
                else:
                    current_page = int(current_params.get("page", 1))
                    current_params = {**current_params, "page": current_page + 1}
            else:
                current_page = int(current_params.get("page", 1))
                current_params = {**current_params, "page": current_page + 1}
        else:
            # while condition became False: pages_fetched reached max_pages
            if last_resp is not None and last_resp.has_next:
                limit_reached = True

        return PaginatedResponse(
            data=merged_data,
            total=last_resp.total if last_resp is not None else None,
            per_page=last_resp.per_page if last_resp is not None else None,
            has_next=limit_reached,
            next_url=None,
            pages_fetched=pages_fetched,
        )

    async def post(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make a POST request.

        Args:
            path: API endpoint path
            json_data: JSON request body

        Returns:
            Parsed JSON response
        """
        return await self._request("POST", path, json_data=json_data)

    async def put(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make a PUT request.

        Args:
            path: API endpoint path
            json_data: JSON request body

        Returns:
            Parsed JSON response
        """
        return await self._request("PUT", path, json_data=json_data)

    async def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """
        Make a DELETE request.

        Args:
            path: API endpoint path
            params: Query parameters

        Returns:
            Parsed JSON response (usually empty)
        """
        return await self._request("DELETE", path, params=params)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "PocketSmithClient":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    def get_stats(self) -> dict[str, Any]:
        """
        Get client statistics.

        Returns:
            Dictionary with rate limiter and circuit breaker stats
        """
        return {
            "rate_limiter": {
                "available_tokens": self._rate_limiter.available_tokens,
                "max_tokens": self._rate_limiter.max_tokens,
            },
            "circuit_breaker": self._circuit_breaker.get_stats(),
        }
