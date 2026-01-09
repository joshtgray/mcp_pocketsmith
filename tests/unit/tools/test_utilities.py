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
            {"id": "USD", "name": "US Dollar", "symbol": "$", "decimal_places": 2},
            {"id": "EUR", "name": "Euro", "symbol": "€", "decimal_places": 2},
            {"id": "NZD", "name": "New Zealand Dollar", "symbol": "$", "decimal_places": 2}
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
