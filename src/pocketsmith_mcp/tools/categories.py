"""Category management MCP tools."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.categories")


def register_category_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register category-related MCP tools."""

    @mcp.tool()
    async def list_categories(user_id: int) -> str:
        """
        List all categories for a user.

        Categories are organized in a hierarchy. Each category may have
        a parent and children. Categories can be marked as transfer,
        bill, or roll-up categories.

        Args:
            user_id: The PocketSmith user ID

        Returns:
            JSON array of categories in hierarchical structure
        """
        try:
            result = await client.get(f"/users/{user_id}/categories")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_categories failed: {e}")
            raise ValueError(f"Failed to list categories: {e}")

    @mcp.tool()
    async def get_category(category_id: int) -> str:
        """
        Get details of a specific category.

        Args:
            category_id: The category ID

        Returns:
            JSON object with category details including parent, children,
            color, and settings
        """
        try:
            result = await client.get(f"/categories/{category_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_category failed: {e}")
            raise ValueError(f"Failed to get category {category_id}: {e}")

    @mcp.tool()
    async def create_category(
        user_id: int,
        title: str,
        colour: str | None = None,
        parent_id: int | None = None,
        is_transfer: bool = False,
        is_bill: bool = False,
        roll_up: bool = False,
        refund_behaviour: str | None = None,
    ) -> str:
        """
        Create a new category.

        Args:
            user_id: The PocketSmith user ID
            title: Category name
            colour: Category color (hex, e.g., "#4CAF50")
            parent_id: Parent category ID for hierarchy
            is_transfer: Mark as transfer category
            is_bill: Mark as bill category
            roll_up: Roll up totals to parent in reports
            refund_behaviour: How refunds are handled
                             ("credits_are_refunds", "debits_are_refunds", "none")

        Returns:
            JSON object with created category
        """
        try:
            body: dict[str, Any] = {
                "title": title,
                "is_transfer": is_transfer,
                "is_bill": is_bill,
                "roll_up": roll_up,
            }
            if colour is not None:
                body["colour"] = colour
            if parent_id is not None:
                body["parent_id"] = parent_id
            if refund_behaviour is not None:
                body["refund_behaviour"] = refund_behaviour

            result = await client.post(f"/users/{user_id}/categories", json_data=body)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"create_category failed: {e}")
            raise ValueError(f"Failed to create category: {e}")

    @mcp.tool()
    async def update_category(
        category_id: int,
        title: str | None = None,
        colour: str | None = None,
        parent_id: int | None = None,
        is_transfer: bool | None = None,
        is_bill: bool | None = None,
        roll_up: bool | None = None,
        refund_behaviour: str | None = None,
    ) -> str:
        """
        Update a category.

        Args:
            category_id: The category ID to update
            title: New category name
            colour: New color (hex)
            parent_id: New parent category ID
            is_transfer: Update transfer status
            is_bill: Update bill status
            roll_up: Update roll-up setting
            refund_behaviour: Update refund handling

        Returns:
            JSON object with updated category
        """
        try:
            body: dict[str, Any] = {}
            if title is not None:
                body["title"] = title
            if colour is not None:
                body["colour"] = colour
            if parent_id is not None:
                body["parent_id"] = parent_id
            if is_transfer is not None:
                body["is_transfer"] = is_transfer
            if is_bill is not None:
                body["is_bill"] = is_bill
            if roll_up is not None:
                body["roll_up"] = roll_up
            if refund_behaviour is not None:
                body["refund_behaviour"] = refund_behaviour

            if not body:
                raise ValueError("At least one field must be provided for update")

            result = await client.put(f"/categories/{category_id}", json_data=body)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"update_category failed: {e}")
            raise ValueError(f"Failed to update category {category_id}: {e}")

    @mcp.tool()
    async def delete_category(category_id: int) -> str:
        """
        Delete a category.

        WARNING: Deleting a category will NOT delete transactions in that
        category, but they will become uncategorised. Child categories
        will be moved to the parent of the deleted category.

        Args:
            category_id: The category ID to delete

        Returns:
            Confirmation message
        """
        try:
            await client.delete(f"/categories/{category_id}")
            return json.dumps({
                "deleted": True,
                "category_id": category_id,
                "message": "Category deleted. Transactions are now uncategorised."
            })
        except Exception as e:
            logger.error(f"delete_category failed: {e}")
            raise ValueError(f"Failed to delete category {category_id}: {e}")
