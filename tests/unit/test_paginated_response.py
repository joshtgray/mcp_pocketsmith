"""Unit tests for PaginatedResponse dataclass and paginated API client methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pocketsmith_mcp.client.api_client import (
    PaginatedResponse,
    PocketSmithClient,
    _parse_pagination_headers,
)


class TestPaginatedResponseDataclass:
    """Tests for PaginatedResponse dataclass."""

    def test_defaults(self):
        """PaginatedResponse has correct defaults for optional fields."""
        response = PaginatedResponse(data=[])

        assert response.data == []
        assert response.total is None
        assert response.per_page is None
        assert response.page is None
        assert response.has_next is False
        assert response.next_url is None

    def test_with_all_fields(self):
        """PaginatedResponse stores all explicitly-provided fields correctly."""
        response = PaginatedResponse(
            data=[{"id": 1}, {"id": 2}],
            total=500,
            per_page=100,
            page=2,
            has_next=True,
            next_url="https://api.pocketsmith.com/v2/users/1/transactions?page=3",
        )

        assert response.data == [{"id": 1}, {"id": 2}]
        assert response.total == 500
        assert response.per_page == 100
        assert response.page == 2
        assert response.has_next is True
        assert "page=3" in response.next_url

    def test_data_can_be_dict(self):
        """PaginatedResponse data can hold a dict (non-list responses)."""
        response = PaginatedResponse(data={"id": 1, "name": "test"})

        assert response.data == {"id": 1, "name": "test"}


class TestParsePaginationHeaders:
    """Tests for _parse_pagination_headers() module-level helper."""

    def test_parses_total_header(self):
        """Parses Total header as int."""
        result = _parse_pagination_headers({"Total": "500"})

        assert result["total"] == 500

    def test_parses_per_page_header(self):
        """Parses Per-Page header as int."""
        result = _parse_pagination_headers({"Per-Page": "100"})

        assert result["per_page"] == 100

    def test_parses_both_count_headers(self):
        """Parses both Total and Per-Page together."""
        result = _parse_pagination_headers({"Total": "2345", "Per-Page": "1000"})

        assert result["total"] == 2345
        assert result["per_page"] == 1000

    def test_link_header_with_next_sets_has_next_true(self):
        """Detects rel="next" in Link header and sets has_next=True."""
        link = (
            '<https://api.pocketsmith.com/v2/users/1/transactions?page=2>; rel="next", '
            '<https://api.pocketsmith.com/v2/users/1/transactions?page=5>; rel="last"'
        )
        result = _parse_pagination_headers({"Link": link})

        assert result["has_next"] is True

    def test_link_header_with_next_extracts_next_url(self):
        """Extracts the next URL from the Link header."""
        next_page_url = "https://api.pocketsmith.com/v2/users/1/transactions?page=2"
        link = f'<{next_page_url}>; rel="next"'
        result = _parse_pagination_headers({"Link": link})

        assert result["next_url"] == next_page_url

    def test_link_header_without_next_sets_has_next_false(self):
        """Returns has_next=False when Link header has no rel="next"."""
        link = '<https://api.pocketsmith.com/v2/users/1/transactions?page=1>; rel="prev"'
        result = _parse_pagination_headers({"Link": link})

        assert result["has_next"] is False
        assert result["next_url"] is None

    def test_link_header_only_last_relation(self):
        """Returns has_next=False when Link header only has rel="last"."""
        link = '<https://api.pocketsmith.com/v2/users/1/transactions?page=5>; rel="last"'
        result = _parse_pagination_headers({"Link": link})

        assert result["has_next"] is False

    def test_empty_headers_returns_none_defaults(self):
        """All fields return None/False when no headers are provided."""
        result = _parse_pagination_headers({})

        assert result["total"] is None
        assert result["per_page"] is None
        assert result["has_next"] is False
        assert result["next_url"] is None

    def test_malformed_total_header_returns_none(self):
        """Ignores non-integer Total header value."""
        result = _parse_pagination_headers({"Total": "not-a-number"})

        assert result["total"] is None

    def test_malformed_per_page_header_returns_none(self):
        """Ignores non-integer Per-Page header value."""
        result = _parse_pagination_headers({"Per-Page": "abc"})

        assert result["per_page"] is None

    def test_no_link_header_sets_has_next_false(self):
        """Returns has_next=False when Link header is absent."""
        result = _parse_pagination_headers({"Total": "50", "Per-Page": "100"})

        assert result["has_next"] is False
        assert result["next_url"] is None

    def test_malformed_link_header_does_not_crash(self):
        """Malformed Link header string returns has_next=False and next_url=None without raising."""
        result = _parse_pagination_headers({"Link": "not a valid link header >>>!!!<<<"})

        assert result["has_next"] is False
        assert result["next_url"] is None


class TestGetPaginated:
    """Tests for PocketSmithClient.get_paginated() method."""

    @pytest.mark.asyncio
    async def test_returns_paginated_response_instance(self):
        """get_paginated() returns a PaginatedResponse instance."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"id": 1}, {"id": 2}]
            mock_response.headers = {
                "Total": "500",
                "Per-Page": "100",
                "Link": '<https://api.pocketsmith.com/v2/users/1/transactions?page=2>; rel="next"',
            }
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.get_paginated(
                "/users/1/transactions", params={"page": 1, "per_page": 100}
            )

            assert isinstance(result, PaginatedResponse)

    @pytest.mark.asyncio
    async def test_returns_correct_data_and_metadata(self):
        """get_paginated() populates all PaginatedResponse fields correctly."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"id": 1}, {"id": 2}]
            mock_response.headers = {
                "Total": "500",
                "Per-Page": "100",
                "Link": '<https://api.pocketsmith.com/v2/users/1/transactions?page=2>; rel="next"',
            }
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.get_paginated(
                "/users/1/transactions", params={"page": 1, "per_page": 100}
            )

            assert result.data == [{"id": 1}, {"id": 2}]
            assert result.total == 500
            assert result.per_page == 100
            assert result.page == 1
            assert result.has_next is True

    @pytest.mark.asyncio
    async def test_has_next_false_when_no_link_header(self):
        """get_paginated() sets has_next=False when no Link header present."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"id": 1}]
            mock_response.headers = {"Total": "1", "Per-Page": "100"}
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.get_paginated("/users/1/transactions")

            assert result.has_next is False

    @pytest.mark.asyncio
    async def test_missing_headers_returns_none_metadata(self):
        """get_paginated() returns None for all metadata when headers are absent."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"id": 1}]
            mock_response.headers = {}
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.get_paginated("/users/1/transactions")

            assert result.total is None
            assert result.per_page is None
            assert result.page is None
            assert result.has_next is False
            assert result.next_url is None

    @pytest.mark.asyncio
    async def test_extracts_page_number_from_params(self):
        """get_paginated() extracts the page number from request params."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.headers = {}
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.get_paginated(
                "/users/1/transactions", params={"page": 3}
            )

            assert result.page == 3

    @pytest.mark.asyncio
    async def test_page_is_none_when_no_params(self):
        """get_paginated() sets page=None when no params are provided."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.headers = {}
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.get_paginated("/users/1/transactions")

            assert result.page is None

    @pytest.mark.asyncio
    async def test_has_next_true_with_next_link_relation(self):
        """get_paginated() sets has_next=True when Link header contains rel="next"."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.headers = {
                "Link": (
                    '<https://api.pocketsmith.com/v2/users/1/transactions?page=2>; rel="next", '
                    '<https://api.pocketsmith.com/v2/users/1/transactions?page=10>; rel="last"'
                )
            }
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.get_paginated("/users/1/transactions")

            assert result.has_next is True

    @pytest.mark.asyncio
    async def test_next_url_extracted_from_link_header(self):
        """get_paginated() extracts next_url from Link header."""
        with patch("httpx.AsyncClient") as mock_client_class:
            next_url = "https://api.pocketsmith.com/v2/users/1/transactions?page=2"
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.headers = {"Link": f'<{next_url}>; rel="next"'}
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.get_paginated("/users/1/transactions")

            assert result.next_url == next_url


class TestExistingGetUnchanged:
    """Regression tests: existing get() behaviour must not change."""

    @pytest.mark.asyncio
    async def test_get_returns_raw_list_not_paginated_response(self):
        """get() still returns raw list, not a PaginatedResponse."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"id": 1}, {"id": 2}]
            mock_response.headers = {"Total": "2", "Per-Page": "100"}
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.get("/users/1/transactions")

            assert result == [{"id": 1}, {"id": 2}]
            assert not isinstance(result, PaginatedResponse)

    @pytest.mark.asyncio
    async def test_get_returns_raw_dict_not_paginated_response(self):
        """get() still returns a raw dict for single-resource responses."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": 1, "name": "Test User"}
            mock_response.headers = {}
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = PocketSmithClient(api_key="test_key")
            result = await client.get("/users/1")

            assert result == {"id": 1, "name": "Test User"}
            assert not isinstance(result, PaginatedResponse)
