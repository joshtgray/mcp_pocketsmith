"""Category rules management MCP tools."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.category_rules")


def register_category_rules_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register category-rules-related MCP tools."""

    @mcp.tool()
    async def list_category_rules(user_id: int) -> str:
        """
        List all category rules for a user.

        Category rules automatically assign categories to transactions
        based on payee matching patterns.

        Args:
            user_id: The PocketSmith user ID

        Returns:
            JSON array of category rules
        """
        try:
            result = await client.get(f"/users/{user_id}/category_rules")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_category_rules failed: {e}")
            raise ValueError(f"Failed to list category rules: {e}")

    @mcp.tool()
    async def create_category_rule(
        category_id: int,
        payee_matches: str,
        apply_to_uncategorised: bool = False,
    ) -> str:
        """
        Create a category rule to automatically categorise transactions.

        Args:
            category_id: The category ID to assign matching transactions to
            payee_matches: The keyword/s to match against transaction payees
            apply_to_uncategorised: Apply the rule to all existing
                                   uncategorised transactions

        Returns:
            JSON object with the created category rule
        """
        try:
            body: dict[str, Any] = {"payee_matches": payee_matches}
            if apply_to_uncategorised:
                body["apply_to_uncategorised"] = apply_to_uncategorised

            result = await client.post(
                f"/categories/{category_id}/category_rules", json_data=body
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"create_category_rule failed: {e}")
            raise ValueError(f"Failed to create category rule: {e}")
