"""Event management MCP tools."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.errors import validate_id
from pocketsmith_mcp.logger import get_logger
from pocketsmith_mcp.user_context import UserContext

logger = get_logger("tools.events")


def register_event_tools(mcp: FastMCP, client: PocketSmithClient, user_ctx: UserContext) -> None:
    """Register event-related MCP tools."""

    @mcp.tool()
    async def list_events(
        start_date: str,
        end_date: str,
    ) -> str:
        """
        List budget/calendar events.

        Events represent scheduled transactions for budgeting and
        forecasting, including recurring bills and income.

        Args:
            start_date: Start date for events (YYYY-MM-DD)
            end_date: End date for events (YYYY-MM-DD)

        Returns:
            JSON array of events
        """
        try:
            params: dict[str, Any] = {
                "start_date": start_date,
                "end_date": end_date,
            }

            result = await client.get(f"/users/{user_ctx.user_id}/events", params=params)
            return json.dumps(result, indent=2)
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
    ) -> str:
        """
        List events for a specific scenario.

        Args:
            scenario_id: The scenario ID
            start_date: Start date for events (YYYY-MM-DD)
            end_date: End date for events (YYYY-MM-DD)

        Returns:
            JSON array of events within the scenario
        """
        try:
            validate_id(scenario_id, "scenario_id")
            params: dict[str, Any] = {
                "start_date": start_date,
                "end_date": end_date,
            }
            result = await client.get(f"/scenarios/{scenario_id}/events", params=params)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_scenario_events failed: {e}")
            raise ValueError(f"Failed to list events for scenario {scenario_id}: {e}")
