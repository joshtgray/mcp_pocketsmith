"""Account management MCP tools."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.accounts")


def register_account_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register account-related MCP tools."""

    @mcp.tool()
    async def list_accounts(user_id: int) -> str:
        """
        List all accounts for a user.

        Returns all financial accounts including bank accounts, credit cards,
        loans, investments, and other asset/liability accounts.

        Args:
            user_id: The PocketSmith user ID

        Returns:
            JSON array of accounts with their balances and settings
        """
        try:
            result = await client.get(f"/users/{user_id}/accounts")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_accounts failed: {e}")
            raise ValueError(f"Failed to list accounts: {e}")

    @mcp.tool()
    async def get_account(account_id: int) -> str:
        """
        Get details of a specific account.

        Args:
            account_id: The account ID

        Returns:
            JSON object with account details including balance, type,
            currency, and associated transaction accounts
        """
        try:
            result = await client.get(f"/accounts/{account_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_account failed: {e}")
            raise ValueError(f"Failed to get account {account_id}: {e}")

    @mcp.tool()
    async def update_account(
        account_id: int,
        title: str | None = None,
        currency_code: str | None = None,
        type: str | None = None,
        is_net_worth: bool | None = None,
    ) -> str:
        """
        Update an account's settings.

        Args:
            account_id: The account ID
            title: Account title/name
            currency_code: Currency code (e.g., "USD", "NZD")
            type: Account type (bank, credits, cash, loans, mortgage, stocks,
                  vehicle, property, insurance, other_asset, other_liability)
            is_net_worth: Whether to include in net worth calculations

        Returns:
            JSON object with updated account details
        """
        try:
            body: dict[str, Any] = {}
            if title is not None:
                body["title"] = title
            if currency_code is not None:
                body["currency_code"] = currency_code
            if type is not None:
                body["type"] = type
            if is_net_worth is not None:
                body["is_net_worth"] = is_net_worth

            if not body:
                raise ValueError("At least one field must be provided for update")

            result = await client.put(f"/accounts/{account_id}", json_data=body)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"update_account failed: {e}")
            raise ValueError(f"Failed to update account {account_id}: {e}")

    @mcp.tool()
    async def delete_account(account_id: int) -> str:
        """
        Delete an account.

        WARNING: This will permanently delete the account and all its
        transaction accounts and transactions. This action cannot be undone.

        Args:
            account_id: The account ID to delete

        Returns:
            Confirmation message
        """
        try:
            await client.delete(f"/accounts/{account_id}")
            return json.dumps({
                "deleted": True,
                "account_id": account_id,
                "message": "Account permanently deleted"
            })
        except Exception as e:
            logger.error(f"delete_account failed: {e}")
            raise ValueError(f"Failed to delete account {account_id}: {e}")
