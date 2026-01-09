"""Transaction account management MCP tools."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.transaction_accounts")


def register_transaction_account_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register transaction account-related MCP tools."""

    @mcp.tool()
    async def list_transaction_accounts(user_id: int) -> str:
        """
        List all transaction accounts for a user.

        Transaction accounts are the actual bank accounts/feeds within
        a parent account. Each transaction account holds the transaction
        history and current balance.

        Args:
            user_id: The PocketSmith user ID

        Returns:
            JSON array of transaction accounts
        """
        try:
            # Get all accounts and extract transaction accounts
            accounts_result = await client.get(f"/users/{user_id}/accounts")
            transaction_accounts: list[dict[str, Any]] = []

            # accounts_result is a list of account dictionaries
            if isinstance(accounts_result, list):
                for account in accounts_result:
                    if isinstance(account, dict) and "transaction_accounts" in account:
                        for ta in account["transaction_accounts"]:
                            if isinstance(ta, dict):
                                ta["parent_account_id"] = account.get("id")
                                ta["parent_account_title"] = account.get("title")
                                transaction_accounts.append(ta)

            return json.dumps(transaction_accounts, indent=2)
        except Exception as e:
            logger.error(f"list_transaction_accounts failed: {e}")
            raise ValueError(f"Failed to list transaction accounts: {e}")

    @mcp.tool()
    async def get_transaction_account(transaction_account_id: int) -> str:
        """
        Get details of a specific transaction account.

        Args:
            transaction_account_id: The transaction account ID

        Returns:
            JSON object with transaction account details including balance,
            currency, and institution information
        """
        try:
            result = await client.get(f"/transaction_accounts/{transaction_account_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_transaction_account failed: {e}")
            raise ValueError(f"Failed to get transaction account {transaction_account_id}: {e}")

    @mcp.tool()
    async def update_transaction_account(
        transaction_account_id: int,
        name: str | None = None,
        number: str | None = None,
        starting_balance: float | None = None,
        starting_balance_date: str | None = None,
        is_net_worth: bool | None = None,
    ) -> str:
        """
        Update a transaction account's settings.

        Args:
            transaction_account_id: The transaction account ID
            name: Account name
            number: Account number (for reference only)
            starting_balance: Starting balance amount
            starting_balance_date: Starting balance date (YYYY-MM-DD)
            is_net_worth: Whether to include in net worth calculations

        Returns:
            JSON object with updated transaction account details
        """
        try:
            body: dict[str, Any] = {}
            if name is not None:
                body["name"] = name
            if number is not None:
                body["number"] = number
            if starting_balance is not None:
                body["starting_balance"] = starting_balance
            if starting_balance_date is not None:
                body["starting_balance_date"] = starting_balance_date
            if is_net_worth is not None:
                body["is_net_worth"] = is_net_worth

            if not body:
                raise ValueError("At least one field must be provided for update")

            result = await client.put(
                f"/transaction_accounts/{transaction_account_id}",
                json_data=body
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"update_transaction_account failed: {e}")
            raise ValueError(f"Failed to update transaction account {transaction_account_id}: {e}")
