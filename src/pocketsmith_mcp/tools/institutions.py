"""Institution management MCP tools."""

import json

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.institutions")


def register_institution_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register institution-related MCP tools."""

    @mcp.tool()
    async def list_institutions(user_id: int) -> str:
        """
        List all financial institutions for a user.

        Institutions represent banks, credit unions, and other
        financial entities. Each institution can have multiple
        accounts associated with it.

        Args:
            user_id: The PocketSmith user ID

        Returns:
            JSON array of institutions
        """
        try:
            result = await client.get(f"/users/{user_id}/institutions")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_institutions failed: {e}")
            raise ValueError(f"Failed to list institutions: {e}")

    @mcp.tool()
    async def get_institution(institution_id: int) -> str:
        """
        Get details of a specific institution.

        Args:
            institution_id: The institution ID

        Returns:
            JSON object with institution details
        """
        try:
            result = await client.get(f"/institutions/{institution_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_institution failed: {e}")
            raise ValueError(f"Failed to get institution {institution_id}: {e}")

    @mcp.tool()
    async def create_institution(
        user_id: int,
        title: str,
        currency_code: str,
    ) -> str:
        """
        Create a new institution.

        Creates a financial institution that can be associated
        with accounts. Useful for organizing accounts by bank.

        Args:
            user_id: The PocketSmith user ID
            title: Institution name (e.g., "Chase Bank", "Kiwibank")
            currency_code: Default currency code (e.g., "USD", "NZD")

        Returns:
            JSON object with created institution
        """
        try:
            body = {
                "title": title,
                "currency_code": currency_code,
            }
            result = await client.post(f"/users/{user_id}/institutions", json_data=body)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"create_institution failed: {e}")
            raise ValueError(f"Failed to create institution: {e}")

    @mcp.tool()
    async def update_institution(
        institution_id: int,
        title: str | None = None,
        currency_code: str | None = None,
    ) -> str:
        """
        Update an institution.

        Args:
            institution_id: The institution ID to update
            title: New institution name
            currency_code: New default currency code

        Returns:
            JSON object with updated institution
        """
        try:
            body = {}
            if title is not None:
                body["title"] = title
            if currency_code is not None:
                body["currency_code"] = currency_code

            if not body:
                raise ValueError("At least one field must be provided for update")

            result = await client.put(f"/institutions/{institution_id}", json_data=body)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"update_institution failed: {e}")
            raise ValueError(f"Failed to update institution {institution_id}: {e}")

    @mcp.tool()
    async def delete_institution(institution_id: int) -> str:
        """
        Delete an institution.

        NOTE: This will remove the institution association from any
        accounts, but will NOT delete the accounts themselves.

        Args:
            institution_id: The institution ID to delete

        Returns:
            Confirmation message
        """
        try:
            await client.delete(f"/institutions/{institution_id}")
            return json.dumps({
                "deleted": True,
                "institution_id": institution_id,
                "message": "Institution deleted. Associated accounts are preserved."
            })
        except Exception as e:
            logger.error(f"delete_institution failed: {e}")
            raise ValueError(f"Failed to delete institution {institution_id}: {e}")
