"""Attachment management MCP tools."""

import json

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.logger import get_logger

logger = get_logger("tools.attachments")


def register_attachment_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """Register attachment-related MCP tools."""

    @mcp.tool()
    async def list_attachments(
        user_id: int,
        unassigned: bool = False,
    ) -> str:
        """
        List all attachments for a user.

        Attachments are files (receipts, invoices, etc.) that can be
        associated with transactions for record keeping.

        Args:
            user_id: The PocketSmith user ID
            unassigned: Only show attachments not assigned to transactions

        Returns:
            JSON array of attachments
        """
        try:
            params = {}
            if unassigned:
                params["unassigned"] = 1

            result = await client.get(f"/users/{user_id}/attachments", params=params)
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
            result = await client.get(f"/attachments/{attachment_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"get_attachment failed: {e}")
            raise ValueError(f"Failed to get attachment {attachment_id}: {e}")

    @mcp.tool()
    async def create_attachment(
        user_id: int,
        title: str,
        file_name: str,
        file_data: str,
    ) -> str:
        """
        Create a new attachment by uploading a file.

        The file must be provided as base64-encoded data.

        Args:
            user_id: The PocketSmith user ID
            title: Attachment title/description
            file_name: Original file name with extension
            file_data: Base64-encoded file content

        Returns:
            JSON object with created attachment
        """
        try:
            body = {
                "title": title,
                "file_name": file_name,
                "file_data": file_data,
            }
            result = await client.post(f"/users/{user_id}/attachments", json_data=body)
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
            await client.delete(f"/attachments/{attachment_id}")
            return json.dumps({
                "deleted": True,
                "attachment_id": attachment_id,
                "message": "Attachment deleted"
            })
        except Exception as e:
            logger.error(f"delete_attachment failed: {e}")
            raise ValueError(f"Failed to delete attachment {attachment_id}: {e}")
