"""Transaction management MCP tools."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.transactions")


def register_transaction_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register transaction-related MCP tools."""

    @mcp.tool()
    async def list_transactions(
        user_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
        updated_since: str | None = None,
        category_id: int | None = None,
        search: str | None = None,
        uncategorised: bool = False,
        needs_review: bool = False,
        transaction_type: str | None = None,
        page: int = 1,
    ) -> str:
        """
        List transactions for a user with optional filtering.

        Args:
            user_id: PocketSmith user ID
            start_date: Filter transactions on/after date (YYYY-MM-DD)
            end_date: Filter transactions on/before date (YYYY-MM-DD)
            updated_since: Filter by last update time (ISO 8601)
            category_id: Filter by category ID
            search: Search transactions by payee/memo
            uncategorised: Only show uncategorised transactions
            needs_review: Only show transactions needing review
            transaction_type: Filter by type ("debit" or "credit")
            page: Page number for pagination (default: 1)

        Returns:
            JSON array of transactions
        """
        try:
            params: dict[str, Any] = {"page": page}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date
            if updated_since:
                params["updated_since"] = updated_since
            if category_id:
                params["category_id"] = category_id
            if search:
                params["search"] = search
            if uncategorised:
                params["uncategorised"] = 1
            if needs_review:
                params["needs_review"] = 1
            if transaction_type:
                params["type"] = transaction_type

            result = await client.get(f"/users/{user_id}/transactions", params=params)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_transactions failed: {e}")
            raise ValueError(f"Failed to list transactions: {e}")

    @mcp.tool()
    async def get_transaction(transaction_id: int) -> str:
        """
        Get details of a specific transaction.

        Args:
            transaction_id: The transaction ID

        Returns:
            JSON object with transaction details including payee, amount,
            category, labels, and account information
        """
        try:
            result = await client.get(f"/transactions/{transaction_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_transaction failed: {e}")
            raise ValueError(f"Failed to get transaction {transaction_id}: {e}")

    @mcp.tool()
    async def create_transaction(
        transaction_account_id: int,
        payee: str,
        amount: float,
        date: str,
        category_id: int | None = None,
        note: str | None = None,
        memo: str | None = None,
        cheque_number: str | None = None,
        is_transfer: bool = False,
        labels: list[str] | None = None,
        needs_review: bool = False,
    ) -> str:
        """
        Create a new transaction.

        Args:
            transaction_account_id: The transaction account to add to
            payee: Name of the payee
            amount: Transaction amount (negative for expenses, positive for income)
            date: Transaction date (YYYY-MM-DD)
            category_id: Category ID to assign
            note: User note
            memo: Transaction memo (usually from bank)
            cheque_number: Check/cheque number if applicable
            is_transfer: Whether this is a transfer between accounts
            labels: List of labels to apply
            needs_review: Mark for manual review

        Returns:
            JSON object with created transaction
        """
        try:
            body = {
                "payee": payee,
                "amount": amount,
                "date": date,
                "is_transfer": is_transfer,
                "needs_review": needs_review,
            }
            if category_id is not None:
                body["category_id"] = category_id
            if note is not None:
                body["note"] = note
            if memo is not None:
                body["memo"] = memo
            if cheque_number is not None:
                body["cheque_number"] = cheque_number
            if labels is not None:
                body["labels"] = labels

            result = await client.post(
                f"/transaction_accounts/{transaction_account_id}/transactions",
                json_data=body,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"create_transaction failed: {e}")
            raise ValueError(f"Failed to create transaction: {e}")

    @mcp.tool()
    async def update_transaction(
        transaction_id: int,
        payee: str | None = None,
        amount: float | None = None,
        date: str | None = None,
        category_id: int | None = None,
        note: str | None = None,
        memo: str | None = None,
        cheque_number: str | None = None,
        is_transfer: bool | None = None,
        labels: list[str] | None = None,
        needs_review: bool | None = None,
    ) -> str:
        """
        Update an existing transaction.

        Args:
            transaction_id: The transaction ID to update
            payee: New payee name
            amount: New amount
            date: New date (YYYY-MM-DD)
            category_id: New category ID
            note: New user note
            memo: New memo
            cheque_number: New cheque number
            is_transfer: Update transfer status
            labels: New labels (replaces existing)
            needs_review: Update review status

        Returns:
            JSON object with updated transaction
        """
        try:
            body: dict[str, Any] = {}
            if payee is not None:
                body["payee"] = payee
            if amount is not None:
                body["amount"] = amount
            if date is not None:
                body["date"] = date
            if category_id is not None:
                body["category_id"] = category_id
            if note is not None:
                body["note"] = note
            if memo is not None:
                body["memo"] = memo
            if cheque_number is not None:
                body["cheque_number"] = cheque_number
            if is_transfer is not None:
                body["is_transfer"] = is_transfer
            if labels is not None:
                body["labels"] = labels
            if needs_review is not None:
                body["needs_review"] = needs_review

            if not body:
                raise ValueError("At least one field must be provided for update")

            result = await client.put(f"/transactions/{transaction_id}", json_data=body)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"update_transaction failed: {e}")
            raise ValueError(f"Failed to update transaction {transaction_id}: {e}")

    @mcp.tool()
    async def delete_transaction(transaction_id: int) -> str:
        """
        Delete a transaction.

        WARNING: This will permanently delete the transaction.
        This action cannot be undone.

        Args:
            transaction_id: The transaction ID to delete

        Returns:
            Confirmation message
        """
        try:
            await client.delete(f"/transactions/{transaction_id}")
            return json.dumps({
                "deleted": True,
                "transaction_id": transaction_id,
                "message": "Transaction permanently deleted"
            })
        except Exception as e:
            logger.error(f"delete_transaction failed: {e}")
            raise ValueError(f"Failed to delete transaction {transaction_id}: {e}")
