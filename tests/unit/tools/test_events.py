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
        """Test basic event listing."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        result = await tool.fn()
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/42/events", params={})
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
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )


class TestGetEvent:
    """Tests for get_event tool."""

    @pytest.mark.asyncio
    async def test_get_event_success(self, mcp_with_tools, sample_event):
        """Test successful event retrieval with plain string ID."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_event

        tool = mcp._tool_manager._tools.get("get_event")
        result = await tool.fn(event_id="600")
        result_data = json.loads(result)

        client.get.assert_called_once_with("/events/600")
        assert result_data["id"] == 600

    @pytest.mark.asyncio
    async def test_get_event_with_composite_id(self, mcp_with_tools, sample_event):
        """Test event retrieval with composite series_id-timestamp string ID."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_event

        tool = mcp._tool_manager._tools.get("get_event")
        result = await tool.fn(event_id="26074572-1614556800")
        json.loads(result)

        client.get.assert_called_once_with("/events/26074572-1614556800")

    @pytest.mark.asyncio
    async def test_get_event_with_plain_id(self, mcp_with_tools, sample_event):
        """Test event retrieval with plain integer string ID."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_event

        tool = mcp._tool_manager._tools.get("get_event")
        await tool.fn(event_id="600")

        client.get.assert_called_once_with("/events/600")

    @pytest.mark.asyncio
    async def test_get_event_invalid_id(self, mcp_with_tools):
        """Test that invalid event ID raises ValueError."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("get_event")

        with pytest.raises(ValueError):
            await tool.fn(event_id="not-valid-id")


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
        """Test updating event amount with plain string ID."""
        mcp, client = mcp_with_tools
        updated = {**sample_event, "amount": -75.00}
        client.put.return_value = updated

        tool = mcp._tool_manager._tools.get("update_event")
        await tool.fn(event_id="600", amount=-75.00)

        client.put.assert_called_once_with(
            "/events/600",
            json_data={"amount": -75.00, "behaviour": "one"}
        )

    @pytest.mark.asyncio
    async def test_update_event_no_fields(self, mcp_with_tools):
        """Test error when no fields provided."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("update_event")

        with pytest.raises(ValueError, match="At least one field must be provided"):
            await tool.fn(event_id="600")

    @pytest.mark.asyncio
    async def test_update_event_with_composite_id(self, mcp_with_tools, sample_event):
        """Test update_event with composite series_id-timestamp ID."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_event

        tool = mcp._tool_manager._tools.get("update_event")
        await tool.fn(event_id="26074572-1614556800", amount=-75.00)

        client.put.assert_called_once_with(
            "/events/26074572-1614556800",
            json_data={"amount": -75.00, "behaviour": "one"}
        )

    @pytest.mark.asyncio
    async def test_update_event_behaviour_one(self, mcp_with_tools, sample_event):
        """Test that default behaviour is 'one' and is included in body."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_event

        tool = mcp._tool_manager._tools.get("update_event")
        await tool.fn(event_id="600", amount=-50.00)

        call_body = client.put.call_args[1]["json_data"]
        assert call_body["behaviour"] == "one"

    @pytest.mark.asyncio
    async def test_update_event_behaviour_all(self, mcp_with_tools, sample_event):
        """Test that behaviour='all' is passed in request body."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_event

        tool = mcp._tool_manager._tools.get("update_event")
        await tool.fn(event_id="600", amount=-50.00, behaviour="all")

        call_body = client.put.call_args[1]["json_data"]
        assert call_body["behaviour"] == "all"

    @pytest.mark.asyncio
    async def test_update_event_behaviour_forward(self, mcp_with_tools, sample_event):
        """Test that behaviour='forward' is passed in request body."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_event

        tool = mcp._tool_manager._tools.get("update_event")
        await tool.fn(event_id="600", amount=-50.00, behaviour="forward")

        call_body = client.put.call_args[1]["json_data"]
        assert call_body["behaviour"] == "forward"

    @pytest.mark.asyncio
    async def test_update_event_invalid_behaviour(self, mcp_with_tools):
        """Test that invalid behaviour raises ValueError."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("update_event")

        with pytest.raises(ValueError):
            await tool.fn(event_id="600", amount=-50.00, behaviour="invalid")

    @pytest.mark.asyncio
    async def test_update_event_invalid_event_id(self, mcp_with_tools):
        """Test that invalid event ID raises ValueError."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("update_event")

        with pytest.raises(ValueError):
            await tool.fn(event_id="not-valid-id", amount=-50.00)

    @pytest.mark.asyncio
    async def test_update_event_amount_and_note(self, mcp_with_tools, sample_event):
        """Test that only specified fields plus behaviour appear in body."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_event

        tool = mcp._tool_manager._tools.get("update_event")
        await tool.fn(event_id="600", amount=-99.00, note="Updated note")

        call_body = client.put.call_args[1]["json_data"]
        assert call_body == {
            "amount": -99.00,
            "note": "Updated note",
            "behaviour": "one"
        }

    @pytest.mark.asyncio
    async def test_update_event_no_date_parameter(self, mcp_with_tools, sample_event):
        """Test that update_event does not accept a date parameter."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_event

        tool = mcp._tool_manager._tools.get("update_event")
        import inspect
        sig = inspect.signature(tool.fn)
        assert "date" not in sig.parameters


class TestDeleteEvent:
    """Tests for delete_event tool."""

    @pytest.mark.asyncio
    async def test_delete_event_success(self, mcp_with_tools):
        """Test successful event deletion with plain string ID."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_event")
        result = await tool.fn(event_id="600")
        result_data = json.loads(result)

        client.delete.assert_called_once_with("/events/600", params={"behaviour": "one"})
        assert result_data["deleted"] is True

    @pytest.mark.asyncio
    async def test_delete_event_with_composite_id(self, mcp_with_tools):
        """Test deletion with composite series_id-timestamp ID."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_event")
        result = await tool.fn(event_id="407124074-1773792000")
        result_data = json.loads(result)

        client.delete.assert_called_once_with(
            "/events/407124074-1773792000", params={"behaviour": "one"}
        )
        assert result_data["deleted"] is True
        assert result_data["event_id"] == "407124074-1773792000"

    @pytest.mark.asyncio
    async def test_delete_event_behaviour_one(self, mcp_with_tools):
        """Test that default behaviour is 'one' (query param)."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_event")
        await tool.fn(event_id="600")

        client.delete.assert_called_once_with("/events/600", params={"behaviour": "one"})

    @pytest.mark.asyncio
    async def test_delete_event_behaviour_all(self, mcp_with_tools):
        """Test behaviour='all' is passed as query param."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_event")
        await tool.fn(event_id="600", behaviour="all")

        client.delete.assert_called_once_with("/events/600", params={"behaviour": "all"})

    @pytest.mark.asyncio
    async def test_delete_event_behaviour_forward(self, mcp_with_tools):
        """Test behaviour='forward' is passed as query param."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_event")
        await tool.fn(event_id="600", behaviour="forward")

        client.delete.assert_called_once_with("/events/600", params={"behaviour": "forward"})

    @pytest.mark.asyncio
    async def test_delete_event_invalid_behaviour(self, mcp_with_tools):
        """Test that invalid behaviour raises ValueError."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("delete_event")
        with pytest.raises(ValueError, match="behaviour"):
            await tool.fn(event_id="600", behaviour="invalid")

    @pytest.mark.asyncio
    async def test_delete_event_invalid_event_id(self, mcp_with_tools):
        """Test that invalid event_id raises ValueError."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("delete_event")
        with pytest.raises(ValueError, match="event_id"):
            await tool.fn(event_id="not-valid-id")


class TestWhitespaceTrimming:
    """Tests verifying whitespace-padded event_ids produce clean API URLs."""

    @pytest.mark.asyncio
    async def test_get_event_trims_whitespace_from_plain_id(self, mcp_with_tools, sample_event):
        """Whitespace-padded plain ID is trimmed before building the GET URL."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_event

        tool = mcp._tool_manager._tools.get("get_event")
        await tool.fn(event_id="  600  ")

        client.get.assert_called_once_with("/events/600")

    @pytest.mark.asyncio
    async def test_get_event_trims_whitespace_from_composite_id(self, mcp_with_tools, sample_event):
        """Whitespace-padded composite ID is trimmed before building the GET URL."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_event

        tool = mcp._tool_manager._tools.get("get_event")
        await tool.fn(event_id="  26074572-1614556800  ")

        client.get.assert_called_once_with("/events/26074572-1614556800")

    @pytest.mark.asyncio
    async def test_update_event_trims_whitespace_from_event_id(self, mcp_with_tools, sample_event):
        """Whitespace-padded event_id is trimmed before building the PUT URL."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_event

        tool = mcp._tool_manager._tools.get("update_event")
        await tool.fn(event_id="  600  ", amount=-50.00)

        client.put.assert_called_once_with(
            "/events/600",
            json_data={"amount": -50.00, "behaviour": "one"}
        )

    @pytest.mark.asyncio
    async def test_delete_event_trims_whitespace_from_event_id(self, mcp_with_tools):
        """Whitespace-padded event_id is trimmed before building the DELETE URL."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_event")
        await tool.fn(event_id="  600  ")

        client.delete.assert_called_once_with("/events/600", params={"behaviour": "one"})
