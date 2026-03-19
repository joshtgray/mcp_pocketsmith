"""Event management MCP tools."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.events")


def register_event_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register event-related MCP tools."""

    @mcp.tool()
    async def list_events(
        user_id: int,
        start_date: str,
        end_date: str,
        scenario_id: int | None = None,
    ) -> str:
        """
        List budget/calendar events for a user or scenario.

        Events represent scheduled transactions for budgeting and
        forecasting, including recurring bills and income.

        When scenario_id is provided, returns events scoped to that
        scenario instead of all user events.

        Args:
            user_id: The PocketSmith user ID
            start_date: Filter events on/after date (YYYY-MM-DD)
            end_date: Filter events on/before date (YYYY-MM-DD)
            scenario_id: Optional scenario ID to scope events to

        Returns:
            JSON array of events
        """
        try:
            params: dict[str, Any] = {
                "start_date": start_date,
                "end_date": end_date,
            }

            if scenario_id is not None:
                endpoint = f"/scenarios/{scenario_id}/events"
            else:
                endpoint = f"/users/{user_id}/events"

            result = await client.get_all_pages(endpoint, params=params)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_events failed: {e}")
            raise ValueError(f"Failed to list events: {e}")

    @mcp.tool()
    async def get_event(event_id: str) -> str:
        """
        Get details of a specific event.

        Args:
            event_id: The event ID (string, e.g. "42-1601942400")

        Returns:
            JSON object with event details including amount, date,
            repeat settings, and associated category/scenario
        """
        try:
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
                        "fortnightly", "monthly", "yearly", "each", "once_off")
            repeat_interval: Interval for repeating (e.g., 2 for every 2 weeks)
            note: Event note/description

        Returns:
            JSON object with created event
        """
        try:
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
        event_id: str,
        behaviour: str,
        amount: float | None = None,
        repeat_type: str | None = None,
        repeat_interval: int | None = None,
        note: str | None = None,
    ) -> str:
        """
        Update an event.

        Args:
            event_id: The event ID to update (string, e.g. "42-1601942400")
            behaviour: Whether the update applies to this event only, all future
                events in the series, or all events in the series.
                Must be one of: "one", "forward", "all"
            amount: New amount
            repeat_type: New repeat frequency
            repeat_interval: New repeat interval
            note: New note

        Returns:
            JSON object with updated event
        """
        valid_behaviours = ("one", "forward", "all")
        if behaviour not in valid_behaviours:
            raise ValueError(
                f"behaviour must be one of {valid_behaviours}, got '{behaviour}'"
            )

        try:
            body: dict[str, Any] = {"behaviour": behaviour}
            if amount is not None:
                body["amount"] = amount
            if repeat_type is not None:
                body["repeat_type"] = repeat_type
            if repeat_interval is not None:
                body["repeat_interval"] = repeat_interval
            if note is not None:
                body["note"] = note

            result = await client.put(f"/events/{event_id}", json_data=body)
            return json.dumps(result, indent=2)
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"update_event failed: {e}")
            raise ValueError(f"Failed to update event {event_id}: {e}")

    @mcp.tool()
    async def delete_event(event_id: str, behaviour: str) -> str:
        """
        Delete an event.

        Args:
            event_id: The event ID to delete (string, e.g. "42-1601942400")
            behaviour: Whether the delete applies to this event only, all future
                events in the series, or all events in the series.
                Must be one of: "one", "forward", "all"

        Returns:
            Confirmation message
        """
        valid_behaviours = ("one", "forward", "all")
        if behaviour not in valid_behaviours:
            raise ValueError(
                f"behaviour must be one of {valid_behaviours}, got '{behaviour}'"
            )

        try:
            await client.delete(
                f"/events/{event_id}",
                params={"behaviour": behaviour},
            )
            return json.dumps({
                "deleted": True,
                "event_id": event_id,
                "message": "Event deleted"
            })
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"delete_event failed: {e}")
            raise ValueError(f"Failed to delete event {event_id}: {e}")
