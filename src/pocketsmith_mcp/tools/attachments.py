"""Attachment management MCP tools."""

import base64
import json

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.errors import validate_id
from pocketsmith_mcp.logger import get_logger
from pocketsmith_mcp.user_context import UserContext

logger = get_logger("tools.attachments")


def register_attachment_tools(mcp: FastMCP, client: PocketSmithClient, user_ctx: UserContext) -> None:
    """Register attachment-related MCP tools."""

    def _validate_file_upload(file_name: str, file_data: str) -> None:
        """Validate file upload inputs."""
        if "/" in file_name or "\\" in file_name:
            raise ValueError("file_name contains path separator characters")
        if len(file_name) > 255:
            raise ValueError("file_name exceeds 255 characters")
        try:
            decoded = base64.b64decode(file_data, validate=True)
        except Exception:
            raise ValueError("file_data is not valid base64")
        max_bytes = 10 * 1024 * 1024  # 10MB
        if len(decoded) > max_bytes:
            raise ValueError("Decoded file exceeds maximum size of 10MB")

    @mcp.tool()
    async def list_attachments(
        unassigned: bool = False,
    ) -> str:
        """
        List all attachments.

        Attachments are files (receipts, invoices, etc.) that can be
        associated with transactions for record keeping.

        Args:
            unassigned: Only show attachments not assigned to transactions

        Returns:
            JSON array of attachments
        """
        try:
            params = {}
            if unassigned:
                params["unassigned"] = 1

            result = await client.get(f"/users/{user_ctx.user_id}/attachments", params=params)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_attachments failed: {e}")
            raise ValueError(f"Failed to list attachments: {e}")

    @mcp.tool()
    async def get_attachment(attachment_id: int) -> str:
        """
        Get details of a specific attachment.

        Args:
            attachment_id: The attachment ID

        Returns:
            JSON object with attachment details including URLs
            for original and variant images
        """
        try:
            validate_id(attachment_id, "attachment_id")
            result = await client.get(f"/attachments/{attachment_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_attachment failed: {e}")
            raise ValueError(f"Failed to get attachment {attachment_id}: {e}")

    @mcp.tool()
    async def create_attachment(
        title: str | None = None,
        file_name: str | None = None,
        file_data: str | None = None,
    ) -> str:
        """
        Create a new attachment by uploading a file.

        The file must be provided as base64-encoded data.

        Args:
            title: Attachment title/description
            file_name: Original file name with extension
            file_data: Base64-encoded file content

        Returns:
            JSON object with created attachment
        """
        try:
            if file_name is not None and file_data is not None:
                _validate_file_upload(file_name, file_data)
            body = {}
            if title is not None:
                body["title"] = title
            if file_name is not None:
                body["file_name"] = file_name
            if file_data is not None:
                body["file_data"] = file_data
            result = await client.post(f"/users/{user_ctx.user_id}/attachments", json_data=body)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"create_attachment failed: {e}")
            raise ValueError(f"Failed to create attachment: {e}")

    @mcp.tool()
    async def update_attachment(
        attachment_id: int,
        title: str | None = None,
    ) -> str:
        """
        Update an attachment's metadata.

        Args:
            attachment_id: The attachment ID to update
            title: New title/description

        Returns:
            JSON object with updated attachment
        """
        try:
            validate_id(attachment_id, "attachment_id")
            body = {}
            if title is not None:
                body["title"] = title

            if not body:
                raise ValueError("At least one field must be provided for update")

            result = await client.put(f"/attachments/{attachment_id}", json_data=body)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"update_attachment failed: {e}")
            raise ValueError(f"Failed to update attachment {attachment_id}: {e}")

    @mcp.tool()
    async def delete_attachment(attachment_id: int) -> str:
        """
        Delete an attachment.

        This will remove the attachment file and any associations
        with transactions.

        Args:
            attachment_id: The attachment ID to delete

        Returns:
            Confirmation message
        """
        try:
            validate_id(attachment_id, "attachment_id")
            await client.delete(f"/attachments/{attachment_id}")
            return json.dumps({
                "deleted": True,
                "attachment_id": attachment_id,
                "message": "Attachment deleted"
            })
        except Exception as e:
            logger.error(f"delete_attachment failed: {e}")
            raise ValueError(f"Failed to delete attachment {attachment_id}: {e}")

    @mcp.tool()
    async def list_transaction_attachments(transaction_id: int) -> str:
        """
        List all attachments for a transaction.

        Args:
            transaction_id: The transaction ID

        Returns:
            JSON array of attachments belonging to the transaction
        """
        try:
            validate_id(transaction_id, "transaction_id")
            result = await client.get(f"/transactions/{transaction_id}/attachments")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"list_transaction_attachments failed: {e}")
            raise ValueError(
                f"Failed to list attachments for transaction {transaction_id}: {e}"
            )

    @mcp.tool()
    async def assign_attachment_to_transaction(
        transaction_id: int,
        attachment_id: int,
    ) -> str:
        """
        Assign an existing attachment to a transaction.

        Args:
            transaction_id: The transaction ID
            attachment_id: The attachment ID to assign

        Returns:
            JSON object with the assigned attachment
        """
        try:
            validate_id(transaction_id, "transaction_id")
            validate_id(attachment_id, "attachment_id")
            result = await client.post(
                f"/transactions/{transaction_id}/attachments",
                json_data={"attachment_id": attachment_id},
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"assign_attachment_to_transaction failed: {e}")
            raise ValueError(
                f"Failed to assign attachment {attachment_id} to transaction "
                f"{transaction_id}: {e}"
            )

    @mcp.tool()
    async def unassign_attachment_from_transaction(
        transaction_id: int,
        attachment_id: int,
    ) -> str:
        """
        Unassign an attachment from a transaction.

        This does not delete the attachment, it only removes its
        association from the transaction.

        Args:
            transaction_id: The transaction ID
            attachment_id: The attachment ID to unassign

        Returns:
            Confirmation message
        """
        try:
            validate_id(transaction_id, "transaction_id")
            validate_id(attachment_id, "attachment_id")
            await client.delete(
                f"/transactions/{transaction_id}/attachments/{attachment_id}"
            )
            return json.dumps({
                "unassigned": True,
                "transaction_id": transaction_id,
                "attachment_id": attachment_id,
                "message": "Attachment unassigned from transaction",
            })
        except Exception as e:
            logger.error(f"unassign_attachment_from_transaction failed: {e}")
            raise ValueError(
                f"Failed to unassign attachment {attachment_id} from transaction "
                f"{transaction_id}: {e}"
            )
