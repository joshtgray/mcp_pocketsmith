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
def mcp_with_tools(mock_client, user_ctx):
    """Create FastMCP instance with event tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_event_tools(mcp, mock_client, user_ctx)
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
        """Test basic event listing with default pagination."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        result = await tool.fn(start_date="2024-01-01", end_date="2024-12-31")
        result_data = json.loads(result)

        client.get.assert_called_once_with(
            "/users/42/events",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "per_page": 1000,
                "page": 1,
            },
        )
        assert len(result_data) == 1

    @pytest.mark.asyncio
    async def test_list_events_with_date_filter(self, mcp_with_tools, sample_event):
        """Test event listing with date filter."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        await tool.fn(
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        client.get.assert_called_once_with(
            "/users/42/events",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "per_page": 1000,
                "page": 1,
            },
        )

    @pytest.mark.asyncio
    async def test_list_events_custom_per_page(self, mcp_with_tools, sample_event):
        """Test list_events with custom per_page value."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        await tool.fn(start_date="2024-01-01", end_date="2024-12-31", per_page=100)

        client.get.assert_called_once_with(
            "/users/42/events",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "per_page": 100,
                "page": 1,
            },
        )

    @pytest.mark.asyncio
    async def test_list_events_custom_page(self, mcp_with_tools, sample_event):
        """Test list_events with custom page value."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        await tool.fn(start_date="2024-01-01", end_date="2024-12-31", page=2)

        client.get.assert_called_once_with(
            "/users/42/events",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "per_page": 1000,
                "page": 2,
            },
        )

    @pytest.mark.asyncio
    async def test_list_events_per_page_too_low(self, mcp_with_tools):
        """Test per_page below minimum raises ValueError."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_events")
        with pytest.raises(ValueError, match="per_page must be between 10 and 1000"):
            await tool.fn(start_date="2024-01-01", end_date="2024-12-31", per_page=5)

    @pytest.mark.asyncio
    async def test_list_events_per_page_too_high(self, mcp_with_tools):
        """Test per_page above maximum raises ValueError."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_events")
        with pytest.raises(ValueError, match="per_page must be between 10 and 1000"):
            await tool.fn(start_date="2024-01-01", end_date="2024-12-31", per_page=1001)

    @pytest.mark.asyncio
    async def test_list_events_page_too_low(self, mcp_with_tools):
        """Test page below 1 raises ValueError."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_events")
        with pytest.raises(ValueError, match="page must be >= 1"):
            await tool.fn(start_date="2024-01-01", end_date="2024-12-31", page=0)


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


class TestCreateEventNoPhantomParams:
    """Verify create_event does not expose params removed from the API spec."""

    def test_colour_not_in_signature(self, mcp_with_tools):
        """colour is not in the API spec for POST /scenarios/{id}/events."""
        import inspect
        mcp, _ = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_event")
        sig = inspect.signature(tool.fn)
        assert "colour" not in sig.parameters


class TestUpdateEventNoPhantomParams:
    """Verify update_event does not expose params removed from the API spec."""

    def test_category_id_not_in_signature(self, mcp_with_tools):
        """category_id is not in the API spec for PUT /events/{id}."""
        import inspect
        mcp, _ = mcp_with_tools
        tool = mcp._tool_manager._tools.get("update_event")
        sig = inspect.signature(tool.fn)
        assert "category_id" not in sig.parameters

    def test_colour_not_in_signature(self, mcp_with_tools):
        """colour is not in the API spec for PUT /events/{id}."""
        import inspect
        mcp, _ = mcp_with_tools
        tool = mcp._tool_manager._tools.get("update_event")
        sig = inspect.signature(tool.fn)
        assert "colour" not in sig.parameters


class TestListScenarioEvents:
    """Tests for list_scenario_events tool."""

    @pytest.mark.asyncio
    async def test_list_scenario_events_basic(self, mcp_with_tools, sample_event):
        """Test basic scenario event listing with default pagination."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_scenario_events")
        result = await tool.fn(
            scenario_id=200,
            start_date="2024-01-01",
            end_date="2024-12-31",
        )
        result_data = json.loads(result)

        client.get.assert_called_once_with(
            "/scenarios/200/events",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "per_page": 1000,
                "page": 1,
            },
        )
        assert len(result_data) == 1

    @pytest.mark.asyncio
    async def test_list_scenario_events_pagination(self, mcp_with_tools, sample_event):
        """Test list_scenario_events with custom pagination."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_scenario_events")
        await tool.fn(
            scenario_id=200,
            start_date="2024-01-01",
            end_date="2024-12-31",
            per_page=50,
            page=3,
        )

        client.get.assert_called_once_with(
            "/scenarios/200/events",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "per_page": 50,
                "page": 3,
            },
        )

    @pytest.mark.asyncio
    async def test_list_scenario_events_per_page_validation(self, mcp_with_tools):
        """Test per_page validation on list_scenario_events."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_scenario_events")
        with pytest.raises(ValueError, match="per_page must be between 10 and 1000"):
            await tool.fn(
                scenario_id=200, start_date="2024-01-01",
                end_date="2024-12-31", per_page=5,
            )

    @pytest.mark.asyncio
    async def test_list_scenario_events_page_validation(self, mcp_with_tools):
        """Test page validation on list_scenario_events."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_scenario_events")
        with pytest.raises(ValueError, match="page must be >= 1"):
            await tool.fn(scenario_id=200, start_date="2024-01-01", end_date="2024-12-31", page=0)

    @pytest.mark.asyncio
    async def test_list_scenario_events_empty(self, mcp_with_tools):
        """Test scenario event listing with no results."""
        mcp, client = mcp_with_tools
        client.get.return_value = []

        tool = mcp._tool_manager._tools.get("list_scenario_events")
        result = await tool.fn(
            scenario_id=200,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        result_data = json.loads(result)
        assert result_data == []

    @pytest.mark.asyncio
    async def test_list_scenario_events_invalid_id(self, mcp_with_tools):
        """list_scenario_events should reject zero scenario_id."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_scenario_events")
        with pytest.raises(ValueError, match="scenario_id must be a positive integer"):
            await tool.fn(scenario_id=0, start_date="2024-01-01", end_date="2024-12-31")
