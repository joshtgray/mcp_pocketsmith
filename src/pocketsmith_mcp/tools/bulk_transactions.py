"""Bulk transaction update MCP tools."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.bulk_transactions")


def register_bulk_transaction_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register bulk transaction MCP tools."""

    @mcp.tool()
    async def bulk_update_transactions(
        updates: list[dict[str, Any]],
        dry_run: bool = False,
    ) -> str:
        """
        Update multiple transactions at once.

        Each entry in `updates` must have a `transaction_id` (int) and may have:
          - `category_id` (int): new category to assign
          - `note` (str): note to add or update
          - `is_transfer` (bool): mark as transfer to prevent double-counting
          - `needs_review` (bool): set review flag

        Up to 100 transactions can be updated in a single call.

        When dry_run is True, the updates are validated but not applied.

        Args:
            updates: List of update dicts, each containing transaction_id plus
                     optional category_id, note, is_transfer, needs_review
            dry_run: If True, validate only — do not apply changes

        Returns:
            JSON object with per-transaction results and a summary
        """
        if not updates:
            raise ValueError("updates list cannot be empty")
        if len(updates) > 100:
            raise ValueError("Maximum 100 updates per call")

        results: list[dict[str, Any]] = []
        successful = 0
        failed = 0
        skipped = 0
        errors = []

        for update in updates:
            raw_id = update.get("transaction_id")
            if not raw_id and raw_id != 0:
                skipped += 1
                results.append({
                    "transaction_id": None,
                    "status": "skipped",
                    "message": "Missing transaction_id",
                })
                continue

            try:
                transaction_id = int(raw_id)
            except (ValueError, TypeError):
                skipped += 1
                results.append({
                    "transaction_id": raw_id,
                    "status": "skipped",
                    "message": f"Invalid transaction_id: must be a numeric value, got {raw_id!r}",
                })
                continue

            if transaction_id <= 0:
                skipped += 1
                results.append({
                    "transaction_id": transaction_id,
                    "status": "skipped",
                    "message": f"transaction_id must be a positive integer, got {transaction_id}",
                })
                continue

            try:
                body: dict[str, Any] = {}
                if "category_id" in update and update["category_id"] is not None:
                    body["category_id"] = int(update["category_id"])
                if "note" in update and update["note"] is not None:
                    body["note"] = str(update["note"])
                if "is_transfer" in update and update["is_transfer"] is not None:
                    body["is_transfer"] = bool(update["is_transfer"])
                if "needs_review" in update and update["needs_review"] is not None:
                    body["needs_review"] = bool(update["needs_review"])

                if not body:
                    skipped += 1
                    results.append({
                        "transaction_id": transaction_id,
                        "status": "skipped",
                        "message": "No fields to update",
                    })
                    continue

                if dry_run:
                    successful += 1
                    results.append({
                        "transaction_id": transaction_id,
                        "status": "would_update",
                        "planned_changes": body,
                    })
                else:
                    updated = await client.put(
                        f"/transactions/{transaction_id}",
                        json_data=body,
                    )
                    if not isinstance(updated, dict):
                        raise ValueError(
                            f"Unexpected API response type for transaction {transaction_id}"
                        )
                    successful += 1
                    results.append({
                        "transaction_id": transaction_id,
                        "status": "success",
                        "updated": {
                            "id": updated.get("id"),
                            "payee": updated.get("payee"),
                            "amount": updated.get("amount"),
                            "date": updated.get("date"),
                            "category": (
                                updated.get("category", {}).get("title")
                                if updated.get("category")
                                else None
                            ),
                            "is_transfer": updated.get("is_transfer"),
                            "note": updated.get("note"),
                            "needs_review": updated.get("needs_review"),
                            "labels": updated.get("labels"),
                        },
                    })

            except Exception as e:
                failed += 1
                error_msg = f"Transaction {transaction_id}: {e}"
                errors.append(error_msg)
                logger.error(f"bulk_update_transactions failed for {transaction_id}: {e}")
                results.append({
                    "transaction_id": transaction_id,
                    "status": "error",
                    "message": str(e),
                })

        return json.dumps({
            "dry_run": dry_run,
            "summary": {
                "total": len(updates),
                "successful": successful,
                "failed": failed,
                "skipped": skipped,
                "errors": errors,
            },
            "results": results,
        }, indent=2)
