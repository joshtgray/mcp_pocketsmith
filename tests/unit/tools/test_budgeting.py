"""Unit tests for budgeting MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.budgeting import register_budgeting_tools


@pytest.fixture
def mock_client():
    """Create a mock PocketSmith client."""
    client = MagicMock()
    client.get = AsyncMock()
    client.delete = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with budgeting tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_budgeting_tools(mcp, mock_client)
    return mcp, mock_client


class TestGetBudget:
    """Tests for get_budget tool."""

    @pytest.mark.asyncio
    async def test_get_budget_basic(self, mcp_with_tools):
        """Test basic budget retrieval."""
        mcp, client = mcp_with_tools
        budget_data = {
            "forecast_cache_age": 3600,
            "income": 5000.00,
            "expense": -3500.00
        }
        client.get.return_value = budget_data

        tool = mcp._tool_manager._tools.get("get_budget")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        client.get.assert_called_once_with(
            "/users/123/budget",
            params={"roll_up": 0}
        )
        assert result_data["income"] == 5000.00

    @pytest.mark.asyncio
    async def test_get_budget_with_roll_up(self, mcp_with_tools):
        """Test budget retrieval with roll_up option."""
        mcp, client = mcp_with_tools
        client.get.return_value = {"income": 5000.00}

        tool = mcp._tool_manager._tools.get("get_budget")
        await tool.fn(user_id=123, roll_up=True)

        client.get.assert_called_once_with(
            "/users/123/budget",
            params={"roll_up": 1}
        )


class TestGetBudgetSummary:
    """Tests for get_budget_summary tool."""

    @pytest.mark.asyncio
    async def test_get_budget_summary_basic(self, mcp_with_tools):
        """Test basic budget summary retrieval."""
        mcp, client = mcp_with_tools
        summary_data = {
            "total_income": 5000.00,
            "total_expense": -3500.00,
            "categories": []
        }
        client.get.return_value = summary_data

        tool = mcp._tool_manager._tools.get("get_budget_summary")
        result = await tool.fn(
            user_id=123,
            start_date="2024-01-01",
            end_date="2024-01-31",
            period="months",
            interval=1
        )
        result_data = json.loads(result)

        assert result_data["total_income"] == 5000.00


class TestGetTrendAnalysis:
    """Tests for get_trend_analysis tool."""

    @pytest.mark.asyncio
    async def test_get_trend_analysis_basic(self, mcp_with_tools):
        """Test basic trend analysis retrieval."""
        mcp, client = mcp_with_tools
        trend_data = {
            "periods": [],
            "categories": []
        }
        client.get.return_value = trend_data

        tool = mcp._tool_manager._tools.get("get_trend_analysis")
        result = await tool.fn(
            user_id=123,
            period="months",
            interval=1,
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        result_data = json.loads(result)

        assert "periods" in result_data


class TestClearForecastCache:
    """Tests for clear_forecast_cache tool."""

    @pytest.mark.asyncio
    async def test_clear_forecast_cache_success(self, mcp_with_tools):
        """Test successful forecast cache clearing."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("clear_forecast_cache")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        client.delete.assert_called_once_with("/users/123/forecast_cache")
        assert result_data["success"] is True
