"""Unit tests for event MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.events import register_event_tools


@pytest.fixture
def mock_client():
    """Create a mock PocketSmith client."""
    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with event tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_event_tools(mcp, mock_client)
    return mcp, mock_client


@pytest.fixture
def sample_event():
    """Sample event data."""
    return {
        "id": 600,
        "category_id": 100,
        "amount": -50.00,
        "date": "2024-01-15",
        "repeat_type": "monthly",
        "repeat_interval": 1,
        "note": "Monthly subscription"
    }


class TestListEvents:
    """Tests for list_events tool."""

    @pytest.mark.asyncio
    async def test_list_events_basic(self, mcp_with_tools, sample_event):
        """Test basic event listing."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/123/events", params={})
        assert len(result_data) == 1

    @pytest.mark.asyncio
    async def test_list_events_with_date_filter(self, mcp_with_tools, sample_event):
        """Test event listing with date filter."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        await tool.fn(
            user_id=123,
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        client.get.assert_called_once_with(
            "/users/123/events",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )


class TestGetEvent:
    """Tests for get_event tool."""

    @pytest.mark.asyncio
    async def test_get_event_success(self, mcp_with_tools, sample_event):
        """Test successful event retrieval."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_event

        tool = mcp._tool_manager._tools.get("get_event")
        result = await tool.fn(event_id=600)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/events/600")
        assert result_data["id"] == 600


class TestCreateEvent:
    """Tests for create_event tool."""

    @pytest.mark.asyncio
    async def test_create_event_basic(self, mcp_with_tools, sample_event):
        """Test basic event creation."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_event

        tool = mcp._tool_manager._tools.get("create_event")
        _result = await tool.fn(
            scenario_id=200,
            category_id=100,
            amount=-50.00,
            date="2024-01-15"
        )

        client.post.assert_called_once_with(
            "/scenarios/200/events",
            json_data={
                "category_id": 100,
                "amount": -50.00,
                "date": "2024-01-15",
                "repeat_type": "once",
                "repeat_interval": 1
            }
        )

    @pytest.mark.asyncio
    async def test_create_event_recurring(self, mcp_with_tools, sample_event):
        """Test recurring event creation."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_event

        tool = mcp._tool_manager._tools.get("create_event")
        await tool.fn(
            scenario_id=200,
            category_id=100,
            amount=-50.00,
            date="2024-01-15",
            repeat_type="monthly",
            repeat_interval=1,
            note="Monthly subscription"
        )

        call_args = client.post.call_args[1]["json_data"]
        assert call_args["repeat_type"] == "monthly"
        assert call_args["note"] == "Monthly subscription"


class TestUpdateEvent:
    """Tests for update_event tool."""

    @pytest.mark.asyncio
    async def test_update_event_amount(self, mcp_with_tools, sample_event):
        """Test updating event amount."""
        mcp, client = mcp_with_tools
        updated = {**sample_event, "amount": -75.00}
        client.put.return_value = updated

        tool = mcp._tool_manager._tools.get("update_event")
        await tool.fn(event_id=600, amount=-75.00)

        client.put.assert_called_once_with(
            "/events/600",
            json_data={"amount": -75.00}
        )

    @pytest.mark.asyncio
    async def test_update_event_no_fields(self, mcp_with_tools):
        """Test error when no fields provided."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("update_event")

        with pytest.raises(ValueError, match="At least one field must be provided"):
            await tool.fn(event_id=600)


class TestDeleteEvent:
    """Tests for delete_event tool."""

    @pytest.mark.asyncio
    async def test_delete_event_success(self, mcp_with_tools):
        """Test successful event deletion."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_event")
        result = await tool.fn(event_id=600)
        result_data = json.loads(result)

        client.delete.assert_called_once_with("/events/600")
        assert result_data["deleted"] is True
