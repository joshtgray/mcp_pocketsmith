"""Label and saved search management MCP tools."""

import json

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger
from pocketsmith_mcp.user_context import UserContext

logger = get_logger("tools.labels")


def register_label_tools(mcp: FastMCP, client: PocketSmithClient, user_ctx: UserContext) -> None:
    """Register label and saved search related MCP tools."""

    @mcp.tool()
    async def list_labels() -> str:
        """
        List all labels.

        Labels are tags that can be applied to transactions for
        additional organization beyond categories.

        Returns:
            JSON array of labels
        """
        try:
            result = await client.get(f"/users/{user_ctx.user_id}/labels")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_labels failed: {e}")
            raise ValueError(f"Failed to list labels: {e}")

    @mcp.tool()
    async def list_saved_searches() -> str:
        """
        List all saved transaction searches.

        Saved searches are pre-configured filters that can be
        quickly applied to find specific transactions.

        Returns:
            JSON array of saved searches
        """
        try:
            result = await client.get(f"/users/{user_ctx.user_id}/saved_searches")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_saved_searches failed: {e}")
            raise ValueError(f"Failed to list saved searches: {e}")
