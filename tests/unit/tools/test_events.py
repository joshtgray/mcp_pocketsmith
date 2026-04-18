"""Unit tests for event MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.events import _MAX_WINDOWS, _split_date_range, register_event_tools


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
        """Test basic event listing with a narrow (single-window) date range."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        result = await tool.fn(start_date="2024-01-01", end_date="2024-01-31")
        result_data = json.loads(result)

        client.get.assert_called_once_with(
            "/users/42/events",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
        )
        assert len(result_data) == 1

    @pytest.mark.asyncio
    async def test_list_events_with_date_filter(self, mcp_with_tools, sample_event):
        """Test event listing with a narrow date filter."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        await tool.fn(
            start_date="2024-01-01",
            end_date="2024-01-31"
        )

        client.get.assert_called_once_with(
            "/users/42/events",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
        )

    @pytest.mark.asyncio
    async def test_list_events_no_pagination_params(self, mcp_with_tools, sample_event):
        """list_events must not send per_page or page — the API ignores them."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        await tool.fn(start_date="2024-01-01", end_date="2024-01-31")

        call_params = client.get.call_args[1]["params"]
        assert "per_page" not in call_params
        assert "page" not in call_params
        assert call_params["start_date"] == "2024-01-01"
        assert call_params["end_date"] == "2024-01-31"


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
        """Test basic scenario event listing with a narrow (single-window) range."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_scenario_events")
        result = await tool.fn(
            scenario_id=200,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        result_data = json.loads(result)

        client.get.assert_called_once_with(
            "/scenarios/200/events",
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
        )
        assert len(result_data) == 1

    @pytest.mark.asyncio
    async def test_list_scenario_events_no_pagination_params(self, mcp_with_tools, sample_event):
        """list_scenario_events must not send per_page or page — the API ignores them."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_scenario_events")
        await tool.fn(scenario_id=200, start_date="2024-01-01", end_date="2024-01-31")

        call_params = client.get.call_args[1]["params"]
        assert "per_page" not in call_params
        assert "page" not in call_params
        assert call_params["start_date"] == "2024-01-01"
        assert call_params["end_date"] == "2024-01-31"

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


class TestSplitDateRange:
    """Tests for the _split_date_range helper function."""

    def test_single_window_narrow_range(self):
        """A range of ≤31 days returns a single window unchanged."""
        windows = _split_date_range("2024-01-01", "2024-01-31")
        assert windows == [("2024-01-01", "2024-01-31")]

    def test_single_window_exactly_31_days(self):
        """A 31-day difference (end - start = 31) triggers windowing into 2 windows."""
        # 2024-01-01 to 2024-02-01 is exactly 31 days difference — should be windowed
        windows = _split_date_range("2024-01-01", "2024-02-01")
        assert len(windows) == 2
        assert windows[0] == ("2024-01-01", "2024-01-31")
        assert windows[1] == ("2024-02-01", "2024-02-01")

    def test_multi_month_range_produces_calendar_windows(self):
        """A range spanning multiple months produces calendar-month windows."""
        windows = _split_date_range("2025-01-15", "2025-04-10")
        assert len(windows) == 4
        assert windows[0] == ("2025-01-15", "2025-01-31")
        assert windows[1] == ("2025-02-01", "2025-02-28")
        assert windows[2] == ("2025-03-01", "2025-03-31")
        assert windows[3] == ("2025-04-01", "2025-04-10")

    def test_exact_calendar_month_boundaries(self):
        """A range aligned on month boundaries produces clean windows."""
        windows = _split_date_range("2024-01-01", "2024-03-31")
        assert len(windows) == 3
        assert windows[0] == ("2024-01-01", "2024-01-31")
        assert windows[1] == ("2024-02-01", "2024-02-29")  # 2024 is leap year
        assert windows[2] == ("2024-03-01", "2024-03-31")

    def test_leap_year_february(self):
        """February in a leap year ends on the 29th."""
        windows = _split_date_range("2024-02-01", "2024-03-15")
        assert windows[0] == ("2024-02-01", "2024-02-29")
        assert windows[1] == ("2024-03-01", "2024-03-15")

    def test_non_leap_year_february(self):
        """February in a non-leap year ends on the 28th."""
        windows = _split_date_range("2025-02-01", "2025-03-15")
        assert windows[0] == ("2025-02-01", "2025-02-28")
        assert windows[1] == ("2025-03-01", "2025-03-15")

    def test_exactly_24_windows_succeeds(self):
        """Exactly 24 monthly windows (2-year limit) is allowed."""
        # 2024-01-01 to 2025-12-31 = exactly 24 full months
        windows = _split_date_range("2024-01-01", "2025-12-31")
        assert len(windows) == 24
        assert windows[0] == ("2024-01-01", "2024-01-31")
        assert windows[-1] == ("2025-12-01", "2025-12-31")

    def test_safety_limit_exceeded_raises(self):
        """A range requiring >24 windows raises ValueError."""
        # 25 months: 2024-01-01 to 2026-01-15 = 25 windows
        with pytest.raises(ValueError, match="safety limit"):
            _split_date_range("2024-01-01", "2026-01-15")

    def test_safety_limit_error_mentions_max_windows(self):
        """The safety limit error references the 24-window constant."""
        with pytest.raises(ValueError, match=str(_MAX_WINDOWS)):
            _split_date_range("2020-01-01", "2023-01-01")


class TestListEventsAutoWindowing:
    """Tests for auto date-windowing in list_events."""

    @pytest.mark.asyncio
    async def test_single_month_makes_one_request(self, mcp_with_tools, sample_event):
        """A ≤31-day range makes exactly one API request."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        result = await tool.fn(start_date="2024-03-01", end_date="2024-03-31")

        assert client.get.call_count == 1
        result_data = json.loads(result)
        assert len(result_data) == 1

    @pytest.mark.asyncio
    async def test_multi_month_splits_into_windows(self, mcp_with_tools):
        """A 3-month range results in 3 separate API requests with correct params."""
        mcp, client = mcp_with_tools
        client.get.side_effect = [
            [{"id": 1, "date": "2024-01-20"}],
            [{"id": 2, "date": "2024-02-10"}],
            [{"id": 3, "date": "2024-03-05"}],
        ]

        tool = mcp._tool_manager._tools.get("list_events")
        result = await tool.fn(start_date="2024-01-15", end_date="2024-03-15")
        result_data = json.loads(result)

        assert client.get.call_count == 3
        assert len(result_data) == 3

        calls = client.get.call_args_list
        assert calls[0][1]["params"] == {"start_date": "2024-01-15", "end_date": "2024-01-31"}
        assert calls[1][1]["params"] == {"start_date": "2024-02-01", "end_date": "2024-02-29"}
        assert calls[2][1]["params"] == {"start_date": "2024-03-01", "end_date": "2024-03-15"}

    @pytest.mark.asyncio
    async def test_deduplication_by_event_id(self, mcp_with_tools):
        """An event appearing in two adjacent windows is included only once."""
        mcp, client = mcp_with_tools
        boundary_event = {"id": 99, "date": "2024-01-31"}
        client.get.side_effect = [
            [{"id": 1, "date": "2024-01-15"}, boundary_event],
            [boundary_event, {"id": 2, "date": "2024-02-10"}],
        ]

        # 2024-01-01 to 2024-02-29 = 59 days → 2 windows: [Jan 1-31, Feb 1-29]
        tool = mcp._tool_manager._tools.get("list_events")
        result = await tool.fn(start_date="2024-01-01", end_date="2024-02-29")
        result_data = json.loads(result)

        assert len(result_data) == 3
        ids = [e["id"] for e in result_data]
        assert ids.count(99) == 1

    @pytest.mark.asyncio
    async def test_auto_window_false_single_request(self, mcp_with_tools, sample_event):
        """auto_window=False makes a single request regardless of date range."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_events")
        await tool.fn(
            start_date="2024-01-01",
            end_date="2024-12-31",
            auto_window=False,
        )

        client.get.assert_called_once_with(
            "/users/42/events",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )

    @pytest.mark.asyncio
    async def test_safety_limit_exceeded_raises_error(self, mcp_with_tools):
        """A date range requiring >24 windows raises ValueError."""
        mcp, _client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("list_events")
        with pytest.raises(ValueError, match="safety limit"):
            await tool.fn(start_date="2024-01-01", end_date="2026-01-15")


class TestListScenarioEventsAutoWindowing:
    """Tests for auto date-windowing in list_scenario_events."""

    @pytest.mark.asyncio
    async def test_multi_month_splits_into_windows(self, mcp_with_tools):
        """A 2-month range results in 2 separate requests for scenario events."""
        mcp, client = mcp_with_tools
        client.get.side_effect = [
            [{"id": 10, "date": "2024-05-15"}],
            [{"id": 11, "date": "2024-06-10"}],
        ]

        tool = mcp._tool_manager._tools.get("list_scenario_events")
        result = await tool.fn(
            scenario_id=200,
            start_date="2024-05-01",
            end_date="2024-06-30",
        )
        result_data = json.loads(result)

        assert client.get.call_count == 2
        assert len(result_data) == 2
        calls = client.get.call_args_list
        assert calls[0][1]["params"] == {"start_date": "2024-05-01", "end_date": "2024-05-31"}
        assert calls[1][1]["params"] == {"start_date": "2024-06-01", "end_date": "2024-06-30"}

    @pytest.mark.asyncio
    async def test_deduplication_by_event_id(self, mcp_with_tools):
        """Duplicate event IDs across windows are deduplicated."""
        mcp, client = mcp_with_tools
        dup = {"id": 50, "date": "2024-05-31"}
        client.get.side_effect = [
            [dup, {"id": 51, "date": "2024-05-20"}],
            [dup, {"id": 52, "date": "2024-06-05"}],
        ]

        tool = mcp._tool_manager._tools.get("list_scenario_events")
        result = await tool.fn(
            scenario_id=200,
            start_date="2024-05-01",
            end_date="2024-06-30",
        )
        result_data = json.loads(result)

        assert len(result_data) == 3
        assert [e["id"] for e in result_data].count(50) == 1

    @pytest.mark.asyncio
    async def test_auto_window_false_single_request(self, mcp_with_tools, sample_event):
        """auto_window=False bypasses windowing for scenario events."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_event]

        tool = mcp._tool_manager._tools.get("list_scenario_events")
        await tool.fn(
            scenario_id=200,
            start_date="2024-01-01",
            end_date="2024-12-31",
            auto_window=False,
        )

        client.get.assert_called_once_with(
            "/scenarios/200/events",
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        )

    @pytest.mark.asyncio
    async def test_safety_limit_exceeded_raises_error(self, mcp_with_tools):
        """A >24-month range raises ValueError for scenario events."""
        mcp, _client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("list_scenario_events")
        with pytest.raises(ValueError, match="safety limit"):
            await tool.fn(
                scenario_id=200,
                start_date="2024-01-01",
                end_date="2026-01-15",
            )
