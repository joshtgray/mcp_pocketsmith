"""Unit tests for label MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.labels import register_label_tools


@pytest.fixture
def mock_client():
    """Create a mock PocketSmith client."""
    client = MagicMock()
    client.get = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with label tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_label_tools(mcp, mock_client)
    return mcp, mock_client


class TestListLabels:
    """Tests for list_labels tool."""

    @pytest.mark.asyncio
    async def test_list_labels_success(self, mcp_with_tools):
        """Test successful label listing."""
        mcp, client = mcp_with_tools
        labels = ["groceries", "entertainment", "work"]
        client.get.return_value = labels

        tool = mcp._tool_manager._tools.get("list_labels")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/123/labels")
        assert len(result_data) == 3
        assert "groceries" in result_data

    @pytest.mark.asyncio
    async def test_list_labels_empty(self, mcp_with_tools):
        """Test empty label list."""
        mcp, client = mcp_with_tools
        client.get.return_value = []

        tool = mcp._tool_manager._tools.get("list_labels")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        assert result_data == []

    @pytest.mark.asyncio
    async def test_list_labels_error(self, mcp_with_tools):
        """Test error handling for label listing."""
        mcp, client = mcp_with_tools
        client.get.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("list_labels")

        with pytest.raises(ValueError, match="Failed to list labels"):
            await tool.fn(user_id=123)


class TestListSavedSearches:
    """Tests for list_saved_searches tool."""

    @pytest.mark.asyncio
    async def test_list_saved_searches_success(self, mcp_with_tools):
        """Test successful saved search listing."""
        mcp, client = mcp_with_tools
        saved_searches = [
            {"id": 1, "title": "Recent purchases", "query": "date:last_month"},
            {"id": 2, "title": "Large expenses", "query": "amount:>100"}
        ]
        client.get.return_value = saved_searches

        tool = mcp._tool_manager._tools.get("list_saved_searches")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/123/saved_searches")
        assert len(result_data) == 2

    @pytest.mark.asyncio
    async def test_list_saved_searches_empty(self, mcp_with_tools):
        """Test empty saved searches list."""
        mcp, client = mcp_with_tools
        client.get.return_value = []

        tool = mcp._tool_manager._tools.get("list_saved_searches")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        assert result_data == []

    @pytest.mark.asyncio
    async def test_list_saved_searches_error(self, mcp_with_tools):
        """Test error handling."""
        mcp, client = mcp_with_tools
        client.get.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("list_saved_searches")

        with pytest.raises(ValueError, match="Failed to list saved searches"):
            await tool.fn(user_id=123)
