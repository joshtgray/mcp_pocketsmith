"""Unit tests for transaction-attachment linking MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.attachments import register_attachment_tools


@pytest.fixture
def mock_client():
    """Create a mock PocketSmith client."""
    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with attachment tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_attachment_tools(mcp, mock_client)
    return mcp, mock_client


@pytest.fixture
def sample_attachment():
    """Sample attachment data."""
    return {
        "id": 700,
        "title": "Receipt",
        "file_name": "receipt.pdf",
        "content_type": "application/pdf",
        "original_url": "https://example.com/receipt.pdf",
    }


class TestListTransactionAttachments:
    """Tests for list_transaction_attachments tool."""

    @pytest.mark.asyncio
    async def test_list_transaction_attachments_success(
        self, mcp_with_tools, sample_attachment
    ):
        """Test listing attachments for a transaction."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_attachment]

        tool = mcp._tool_manager._tools.get("list_transaction_attachments")
        result = await tool.fn(transaction_id=1001)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/transactions/1001/attachments")
        assert len(result_data) == 1
        assert result_data[0]["id"] == 700

    @pytest.mark.asyncio
    async def test_list_transaction_attachments_empty(self, mcp_with_tools):
        """Test listing attachments when transaction has none."""
        mcp, client = mcp_with_tools
        client.get.return_value = []

        tool = mcp._tool_manager._tools.get("list_transaction_attachments")
        result = await tool.fn(transaction_id=999)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/transactions/999/attachments")
        assert result_data == []


class TestAssignAttachmentToTransaction:
    """Tests for assign_attachment_to_transaction tool."""

    @pytest.mark.asyncio
    async def test_assign_attachment_success(
        self, mcp_with_tools, sample_attachment
    ):
        """Test assigning an attachment to a transaction."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_attachment

        tool = mcp._tool_manager._tools.get("assign_attachment_to_transaction")
        result = await tool.fn(transaction_id=1001, attachment_id=700)
        result_data = json.loads(result)

        client.post.assert_called_once_with(
            "/transactions/1001/attachments",
            json_data={"attachment_id": 700},
        )
        assert result_data["id"] == 700


class TestUnassignAttachmentFromTransaction:
    """Tests for unassign_attachment_from_transaction tool."""

    @pytest.mark.asyncio
    async def test_unassign_attachment_success(self, mcp_with_tools):
        """Test unassigning an attachment from a transaction."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get(
            "unassign_attachment_from_transaction"
        )
        result = await tool.fn(transaction_id=1001, attachment_id=700)
        result_data = json.loads(result)

        client.delete.assert_called_once_with(
            "/transactions/1001/attachments/700"
        )
        assert result_data["unassigned"] is True
        assert result_data["transaction_id"] == 1001
        assert result_data["attachment_id"] == 700
