"""Event management MCP tools."""

import calendar
import json
from datetime import date, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.errors import validate_id
from pocketsmith_mcp.logger import get_logger
from pocketsmith_mcp.user_context import UserContext

logger = get_logger("tools.events")

_MAX_WINDOWS = 24


def _split_date_range(start_date_str: str, end_date_str: str) -> list[tuple[str, str]]:
    """Split a date range into calendar-month windows.

    Returns a list of (start, end) ISO-date string tuples. If the range is
    ≤31 days, a single window covering the full range is returned. Otherwise
    the range is split on calendar-month boundaries.

    Raises ValueError if the range requires more than _MAX_WINDOWS windows.
    """
    start = date.fromisoformat(start_date_str)
    end = date.fromisoformat(end_date_str)

    if (end - start).days < 31:
        return [(start_date_str, end_date_str)]

    windows: list[tuple[str, str]] = []
    current_start = start

    while current_start <= end:
        last_day = calendar.monthrange(current_start.year, current_start.month)[1]
        window_end = date(current_start.year, current_start.month, last_day)

        if window_end > end:
            window_end = end

        windows.append((current_start.isoformat(), window_end.isoformat()))

        if len(windows) > _MAX_WINDOWS:
            raise ValueError(
                f"Date range exceeds the safety limit of {_MAX_WINDOWS} monthly "
                f"windows (2 years). Please narrow the date range."
            )

        current_start = window_end + timedelta(days=1)

    return windows


def register_event_tools(mcp: FastMCP, client: PocketSmithClient, user_ctx: UserContext) -> None:
    """Register event-related MCP tools."""

    @mcp.tool()
    async def list_events(
        start_date: str,
        end_date: str,
        auto_window: bool = True,
    ) -> str:
        """
        List budget/calendar events.

        Events represent scheduled transactions for budgeting and
        forecasting, including recurring bills and income.

        NOTE: The PocketSmith API returns a maximum of approximately 30 events
        per request. By default, date ranges longer than 31 days are
        automatically split into monthly windows and results are merged and
        deduplicated. Maximum 24 windows (2-year limit).

        Args:
            start_date: Start date for events (YYYY-MM-DD)
            end_date: End date for events (YYYY-MM-DD)
            auto_window: If True (default), splits ranges >31 days into monthly
                windows and merges deduplicated results. If False, makes a
                single request (results capped at ~30 events by the API).

        Returns:
            JSON array of events
        """
        try:
            windows = (
                _split_date_range(start_date, end_date)
                if auto_window
                else [(start_date, end_date)]
            )

            all_events: list[dict[str, Any]] = []
            seen_ids: set[int] = set()

            for win_start, win_end in windows:
                params: dict[str, Any] = {
                    "start_date": win_start,
                    "end_date": win_end,
                }
                result = await client.get(
                    f"/users/{user_ctx.user_id}/events", params=params
                )
                if isinstance(result, list):
                    for event in result:
                        event_id = event.get("id")
                        if event_id is not None and event_id in seen_ids:
                            continue
                        if event_id is not None:
                            seen_ids.add(event_id)
                        all_events.append(event)

            return json.dumps(all_events, indent=2)
        except Exception as e:
            logger.error(f"list_events failed: {e}")
            raise ValueError(f"Failed to list events: {e}")

    @mcp.tool()
    async def get_event(event_id: int) -> str:
        """
        Get details of a specific event.

        Args:
            event_id: The event ID

        Returns:
            JSON object with event details including amount, date,
            repeat settings, and associated category/scenario
        """
        try:
            validate_id(event_id, "event_id")
            result = await client.get(f"/events/{event_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_event failed: {e}")
            raise ValueError(f"Failed to get event {event_id}: {e}")

    @mcp.tool()
    async def create_event(
        scenario_id: int,
        category_id: int,
        amount: float,
        date: str,
        repeat_type: str = "once",
        repeat_interval: int = 1,
        note: str | None = None,
    ) -> str:
        """
        Create a new budget event.

        Events are used for forecasting and budgeting. They can be
        one-time or recurring (daily, weekly, monthly, yearly, etc.).

        Args:
            scenario_id: The scenario ID to associate with
            category_id: The category ID for the event
            amount: Event amount (negative for expenses)
            date: Event date (YYYY-MM-DD)
            repeat_type: Repeat frequency ("once", "daily", "weekly",
                        "fortnightly", "monthly", "yearly", "each weekday")
            repeat_interval: Interval for repeating (e.g., 2 for every 2 weeks)
            note: Event note/description

        Returns:
            JSON object with created event
        """
        try:
            validate_id(scenario_id, "scenario_id")
            validate_id(category_id, "category_id")
            body: dict[str, Any] = {
                "category_id": category_id,
                "amount": amount,
                "date": date,
                "repeat_type": repeat_type,
                "repeat_interval": repeat_interval,
            }
            if note is not None:
                body["note"] = note

            result = await client.post(f"/scenarios/{scenario_id}/events", json_data=body)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"create_event failed: {e}")
            raise ValueError(f"Failed to create event: {e}")

    @mcp.tool()
    async def update_event(
        event_id: int,
        amount: float | None = None,
        date: str | None = None,
        repeat_type: str | None = None,
        repeat_interval: int | None = None,
        note: str | None = None,
    ) -> str:
        """
        Update an event.

        Args:
            event_id: The event ID to update
            amount: New amount
            date: New date (YYYY-MM-DD)
            repeat_type: New repeat frequency
            repeat_interval: New repeat interval
            note: New note

        Returns:
            JSON object with updated event
        """
        try:
            validate_id(event_id, "event_id")
            body: dict[str, Any] = {}
            if amount is not None:
                body["amount"] = amount
            if date is not None:
                body["date"] = date
            if repeat_type is not None:
                body["repeat_type"] = repeat_type
            if repeat_interval is not None:
                body["repeat_interval"] = repeat_interval
            if note is not None:
                body["note"] = note

            if not body:
                raise ValueError("At least one field must be provided for update")

            result = await client.put(f"/events/{event_id}", json_data=body)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"update_event failed: {e}")
            raise ValueError(f"Failed to update event {event_id}: {e}")

    @mcp.tool()
    async def delete_event(event_id: int) -> str:
        """
        Delete an event.

        NOTE: For recurring events, this deletes only this specific
        occurrence, not the entire series.

        Args:
            event_id: The event ID to delete

        Returns:
            Confirmation message
        """
        try:
            validate_id(event_id, "event_id")
            await client.delete(f"/events/{event_id}")
            return json.dumps({
                "deleted": True,
                "event_id": event_id,
                "message": "Event deleted"
            })
        except Exception as e:
            logger.error(f"delete_event failed: {e}")
            raise ValueError(f"Failed to delete event {event_id}: {e}")

    @mcp.tool()
    async def list_scenario_events(
        scenario_id: int,
        start_date: str,
        end_date: str,
        auto_window: bool = True,
    ) -> str:
        """
        List events for a specific scenario.

        NOTE: The PocketSmith API returns a maximum of approximately 30 events
        per request. By default, date ranges longer than 31 days are
        automatically split into monthly windows and results are merged and
        deduplicated. Maximum 24 windows (2-year limit).

        Args:
            scenario_id: The scenario ID
            start_date: Start date for events (YYYY-MM-DD)
            end_date: End date for events (YYYY-MM-DD)
            auto_window: If True (default), splits ranges >31 days into monthly
                windows and merges deduplicated results. If False, makes a
                single request (results capped at ~30 events by the API).

        Returns:
            JSON array of events within the scenario
        """
        try:
            validate_id(scenario_id, "scenario_id")

            windows = (
                _split_date_range(start_date, end_date)
                if auto_window
                else [(start_date, end_date)]
            )

            all_events: list[dict[str, Any]] = []
            seen_ids: set[int] = set()

            for win_start, win_end in windows:
                params: dict[str, Any] = {
                    "start_date": win_start,
                    "end_date": win_end,
                }
                result = await client.get(
                    f"/scenarios/{scenario_id}/events", params=params
                )
                if isinstance(result, list):
                    for event in result:
                        event_id = event.get("id")
                        if event_id is not None and event_id in seen_ids:
                            continue
                        if event_id is not None:
                            seen_ids.add(event_id)
                        all_events.append(event)

            return json.dumps(all_events, indent=2)
        except Exception as e:
            logger.error(f"list_scenario_events failed: {e}")
            raise ValueError(f"Failed to list events for scenario {scenario_id}: {e}")
