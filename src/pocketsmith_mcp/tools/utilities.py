"""Utility MCP tools for currencies and time zones."""

import json

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.utilities")


def register_utility_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register utility MCP tools."""

    @mcp.tool()
    async def list_currencies() -> str:
        """
        List all supported currencies.

        Returns all currency codes supported by PocketSmith,
        including their names, symbols, and decimal places.

        Returns:
            JSON array of currencies with id, name, symbol,
            and decimal_places fields
        """
        try:
            result = await client.get("/currencies")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_currencies failed: {e}")
            raise ValueError(f"Failed to list currencies: {e}")

    @mcp.tool()
    async def list_time_zones() -> str:
        """
        List all supported time zones.

        Returns all time zones supported by PocketSmith,
        including their names and UTC offsets.

        Returns:
            JSON array of time zones with id, name,
            formatted_offset, and offset_minutes fields
        """
        try:
            result = await client.get("/time_zones")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_time_zones failed: {e}")
            raise ValueError(f"Failed to list time zones: {e}")
