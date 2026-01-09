"""Async HTTP client for PocketSmith API with retry, rate limiting, circuit breaker."""

from typing import Any

import httpx

from pocketsmith_mcp.client.circuit_breaker import CircuitBreaker
from pocketsmith_mcp.client.rate_limiter import RateLimiter
from pocketsmith_mcp.client.retry import retry_with_backoff
from pocketsmith_mcp.errors import APIError, AuthError, CircuitBreakerOpenError, RateLimitError
from pocketsmith_mcp.logger import get_logger

logger = get_logger("api_client")


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
        # Check circuit breaker
        if not self._circuit_breaker.can_execute():
            raise CircuitBreakerOpenError()

        # Rate limiting
        await self._rate_limiter.acquire()

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

            # Record success
            self._circuit_breaker.record_success()

            # Handle empty responses
            if response.status_code == 204:
                return {}

            result: dict[str, Any] | list[Any] = response.json()
            return result

        # Retry with backoff for retryable errors
        return await retry_with_backoff(
            execute_request,
            max_attempts=self.max_retries,
            base_delay=1.0,
            max_delay=30.0,
            retryable_errors=(httpx.TimeoutException, httpx.NetworkError),
        )

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

    async def delete(self, path: str) -> dict[str, Any] | list[Any]:
        """
        Make a DELETE request.

        Args:
            path: API endpoint path

        Returns:
            Parsed JSON response (usually empty)
        """
        return await self._request("DELETE", path)

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
