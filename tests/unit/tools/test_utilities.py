"""Unit tests for utility MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.utilities import register_utility_tools


@pytest.fixture
def mock_client():
    """Create a mock PocketSmith client."""
    client = MagicMock()
    client.get = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with utility tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_utility_tools(mcp, mock_client)
    return mcp, mock_client


class TestListCurrencies:
    """Tests for list_currencies tool."""

    @pytest.mark.asyncio
    async def test_list_currencies_success(self, mcp_with_tools):
        """Test successful currency listing."""
        mcp, client = mcp_with_tools
        currencies = [
            {
                "id": "USD", "name": "US Dollar", "symbol": "$",
                "minor_unit": 2, "separators": {"major": ",", "minor": "."},
            },
            {
                "id": "EUR", "name": "Euro", "symbol": "€",
                "minor_unit": 2, "separators": {"major": ".", "minor": ","},
            },
            {
                "id": "NZD", "name": "New Zealand Dollar", "symbol": "$",
                "minor_unit": 2, "separators": {"major": ",", "minor": "."},
            },
        ]
        client.get.return_value = currencies

        tool = mcp._tool_manager._tools.get("list_currencies")
        result = await tool.fn()
        result_data = json.loads(result)

        client.get.assert_called_once_with("/currencies")
        assert len(result_data) == 3
        assert result_data[0]["id"] == "USD"

    @pytest.mark.asyncio
    async def test_list_currencies_error(self, mcp_with_tools):
        """Test error handling for currency listing."""
        mcp, client = mcp_with_tools
        client.get.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("list_currencies")

        with pytest.raises(ValueError, match="Failed to list currencies"):
            await tool.fn()


class TestListTimeZones:
    """Tests for list_time_zones tool."""

    @pytest.mark.asyncio
    async def test_list_time_zones_success(self, mcp_with_tools):
        """Test successful time zone listing."""
        mcp, client = mcp_with_tools
        time_zones = [
            {
                "id": "Pacific/Auckland",
                "name": "Auckland",
                "formatted_offset": "+13:00",
                "offset_minutes": 780
            },
            {
                "id": "America/New_York",
                "name": "Eastern Time (US & Canada)",
                "formatted_offset": "-05:00",
                "offset_minutes": -300
            }
        ]
        client.get.return_value = time_zones

        tool = mcp._tool_manager._tools.get("list_time_zones")
        result = await tool.fn()
        result_data = json.loads(result)

        client.get.assert_called_once_with("/time_zones")
        assert len(result_data) == 2
        assert result_data[0]["id"] == "Pacific/Auckland"

    @pytest.mark.asyncio
    async def test_list_time_zones_error(self, mcp_with_tools):
        """Test error handling for time zone listing."""
        mcp, client = mcp_with_tools
        client.get.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("list_time_zones")

        with pytest.raises(ValueError, match="Failed to list time zones"):
            await tool.fn()


# ── Phase 6: get_currency ──────────────────────────────────────────────────


class TestGetCurrency:
    """Tests for get_currency tool."""

    @pytest.mark.asyncio
    async def test_get_currency_success(self, mcp_with_tools):
        """Test successful currency retrieval."""
        mcp, client = mcp_with_tools
        currency = {
            "id": "nzd",
            "name": "New Zealand Dollar",
            "symbol": "$",
            "minor_unit": 2,
            "separators": {"major": ",", "minor": "."},
        }
        client.get.return_value = currency

        tool = mcp._tool_manager._tools.get("get_currency")
        result = await tool.fn(currency_id="nzd")
        result_data = json.loads(result)

        client.get.assert_called_once_with("/currencies/nzd")
        assert result_data["id"] == "nzd"
        assert result_data["name"] == "New Zealand Dollar"

    @pytest.mark.asyncio
    async def test_get_currency_error(self, mcp_with_tools):
        """Test error handling for currency retrieval."""
        mcp, client = mcp_with_tools
        client.get.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("get_currency")

        with pytest.raises(ValueError, match="Failed to get currency"):
            await tool.fn(currency_id="nzd")
