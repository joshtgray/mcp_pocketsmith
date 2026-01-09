"""User management MCP tools."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.users")


def register_user_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register user-related MCP tools."""

    @mcp.tool()
    async def get_current_user() -> str:
        """
        Get the currently authenticated user's details.

        Returns the user associated with the API key being used, including
        their ID, email, name, timezone, currency settings, and account limits.

        Returns:
            JSON object with user details
        """
        try:
            result = await client.get("/me")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_current_user failed: {e}")
            raise ValueError(f"Failed to get current user: {e}")

    @mcp.tool()
    async def get_user(user_id: int) -> str:
        """
        Get a user's details by ID.

        Args:
            user_id: The PocketSmith user ID

        Returns:
            JSON object with user details including timezone, currency settings,
            and account information
        """
        try:
            result = await client.get(f"/users/{user_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_user failed: {e}")
            raise ValueError(f"Failed to get user {user_id}: {e}")

    @mcp.tool()
    async def update_user(
        user_id: int,
        name: str | None = None,
        email: str | None = None,
        time_zone: str | None = None,
        week_start_day: int | None = None,
        base_currency_code: str | None = None,
        always_show_base_currency: bool | None = None,
    ) -> str:
        """
        Update a user's settings.

        Args:
            user_id: The PocketSmith user ID
            name: Display name
            email: Email address
            time_zone: Time zone (e.g., "Pacific/Auckland")
            week_start_day: Week start day (0=Sunday, 1=Monday, etc.)
            base_currency_code: Base currency code (e.g., "USD", "NZD")
            always_show_base_currency: Whether to always show amounts in base currency

        Returns:
            JSON object with updated user details
        """
        try:
            body: dict[str, Any] = {}
            if name is not None:
                body["name"] = name
            if email is not None:
                body["email"] = email
            if time_zone is not None:
                body["time_zone"] = time_zone
            if week_start_day is not None:
                body["week_start_day"] = week_start_day
            if base_currency_code is not None:
                body["base_currency_code"] = base_currency_code
            if always_show_base_currency is not None:
                body["always_show_base_currency"] = always_show_base_currency

            if not body:
                raise ValueError("At least one field must be provided for update")

            result = await client.put(f"/users/{user_id}", json_data=body)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"update_user failed: {e}")
            raise ValueError(f"Failed to update user {user_id}: {e}")
