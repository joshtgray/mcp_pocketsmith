"""Unit tests for API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.errors import APIError, AuthError, RateLimitError


class TestPocketSmithClient:
    """Tests for the PocketSmithClient class."""

    def test_init_valid_params(self):
        """Test initialization with valid parameters."""
        client = PocketSmithClient(api_key="test_key")

        assert client.api_key == "test_key"
        assert client.base_url == "https://api.pocketsmith.com/v2"
        assert client.timeout == 30.0
        assert client.max_retries == 3

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        client = PocketSmithClient(
            api_key="test_key",
            base_url="https://custom.api.com",
            timeout=60.0,
            max_retries=5,
            rate_limit_per_minute=30,
        )

        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60.0
        assert client.max_retries == 5

    def test_init_missing_api_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="api_key is required"):
            PocketSmithClient(api_key="")

    @pytest.mark.asyncio
    async def test_get_success(self):
        """Test successful GET request."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": 1, "name": "test"}

            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.get("/users/1")

            assert result == {"id": 1, "name": "test"}
            mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_success(self):
        """Test successful POST request."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": 1, "created": True}

            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.post("/transactions", json_data={"amount": 100})

            assert result == {"id": 1, "created": True}

    @pytest.mark.asyncio
    async def test_put_success(self):
        """Test successful PUT request."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": 1, "updated": True}

            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.put("/transactions/1", json_data={"amount": 200})

            assert result == {"id": 1, "updated": True}

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """Test successful DELETE request."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 204

            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.delete("/transactions/1")

            assert result == {}

    @pytest.mark.asyncio
    async def test_auth_error(self):
        """Test 401 raises AuthError."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"

            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="bad_key")

            with pytest.raises(AuthError, match="Invalid API key"):
                await client.get("/me")

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test 429 raises RateLimitError."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "30"}

            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")

            with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                await client.get("/me")

    @pytest.mark.asyncio
    async def test_server_error(self):
        """Test 500 raises APIError."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key", max_retries=1)

            with pytest.raises(APIError, match="Server error"):
                await client.get("/me")

    @pytest.mark.asyncio
    async def test_client_error(self):
        """Test 4xx client errors raise APIError."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_response.json.return_value = {"error": "Resource not found"}

            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")

            with pytest.raises(APIError) as exc_info:
                await client.get("/users/99999")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_params_cleaned(self):
        """Test None params are removed from request."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []

            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            await client.get("/users/1/transactions", params={
                "page": 1,
                "start_date": None,
                "end_date": "2024-01-31",
            })

            # Check that None values were filtered out
            call_args = mock_client.request.call_args
            assert call_args.kwargs["params"] == {"page": 1, "end_date": "2024-01-31"}

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client works as async context manager."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            async with PocketSmithClient(api_key="test_key") as client:
                assert client is not None

            mock_client.aclose.assert_called_once()

    def test_get_stats(self):
        """Test get_stats returns client statistics."""
        client = PocketSmithClient(api_key="test_key", rate_limit_per_minute=60)

        stats = client.get_stats()

        assert "rate_limiter" in stats
        assert "circuit_breaker" in stats
        assert stats["rate_limiter"]["max_tokens"] == 60.0
        assert stats["circuit_breaker"]["state"] == "closed"
