"""Unit tests for attachment MCP tools."""

import base64
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
def mcp_with_tools(mock_client, user_ctx):
    """Create FastMCP instance with attachment tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_attachment_tools(mcp, mock_client, user_ctx)
    return mcp, mock_client


@pytest.fixture
def sample_attachment():
    """Sample attachment data."""
    return {
        "id": 700,
        "title": "Receipt",
        "file_name": "receipt.pdf",
        "content_type": "application/pdf",
        "original_url": "https://example.com/receipt.pdf"
    }


class TestListAttachments:
    """Tests for list_attachments tool."""

    @pytest.mark.asyncio
    async def test_list_attachments_basic(self, mcp_with_tools, sample_attachment):
        """Test basic attachment listing."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_attachment]

        tool = mcp._tool_manager._tools.get("list_attachments")
        result = await tool.fn()
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/42/attachments", params={})
        assert len(result_data) == 1

    @pytest.mark.asyncio
    async def test_list_attachments_unassigned(self, mcp_with_tools):
        """Test listing unassigned attachments."""
        mcp, client = mcp_with_tools
        client.get.return_value = []

        tool = mcp._tool_manager._tools.get("list_attachments")
        await tool.fn(unassigned=True)

        client.get.assert_called_once_with(
            "/users/42/attachments",
            params={"unassigned": 1}
        )


class TestGetAttachment:
    """Tests for get_attachment tool."""

    @pytest.mark.asyncio
    async def test_get_attachment_success(self, mcp_with_tools, sample_attachment):
        """Test successful attachment retrieval."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_attachment

        tool = mcp._tool_manager._tools.get("get_attachment")
        result = await tool.fn(attachment_id=700)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/attachments/700")
        assert result_data["id"] == 700


class TestCreateAttachment:
    """Tests for create_attachment tool."""

    @pytest.mark.asyncio
    async def test_create_attachment_success(self, mcp_with_tools, sample_attachment):
        """Test successful attachment creation."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_attachment

        valid_b64 = base64.b64encode(b"receipt content").decode()
        tool = mcp._tool_manager._tools.get("create_attachment")
        _result = await tool.fn(
            title="Receipt",
            file_name="receipt.pdf",
            file_data=valid_b64
        )

        client.post.assert_called_once_with(
            "/users/42/attachments",
            json_data={
                "title": "Receipt",
                "file_name": "receipt.pdf",
                "file_data": valid_b64
            }
        )


class TestUpdateAttachment:
    """Tests for update_attachment tool."""

    @pytest.mark.asyncio
    async def test_update_attachment_title(self, mcp_with_tools, sample_attachment):
        """Test updating attachment title."""
        mcp, client = mcp_with_tools
        updated = {**sample_attachment, "title": "Updated Receipt"}
        client.put.return_value = updated

        tool = mcp._tool_manager._tools.get("update_attachment")
        await tool.fn(attachment_id=700, title="Updated Receipt")

        client.put.assert_called_once_with(
            "/attachments/700",
            json_data={"title": "Updated Receipt"}
        )

    @pytest.mark.asyncio
    async def test_update_attachment_no_fields(self, mcp_with_tools):
        """Test error when no fields provided."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("update_attachment")

        with pytest.raises(ValueError, match="At least one field must be provided"):
            await tool.fn(attachment_id=700)


class TestDeleteAttachment:
    """Tests for delete_attachment tool."""

    @pytest.mark.asyncio
    async def test_delete_attachment_success(self, mcp_with_tools):
        """Test successful attachment deletion."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_attachment")
        result = await tool.fn(attachment_id=700)
        result_data = json.loads(result)

        client.delete.assert_called_once_with("/attachments/700")
        assert result_data["deleted"] is True


class TestAttachmentValidation:
    """Tests for input validation on attachment tools."""

    @pytest.mark.asyncio
    async def test_get_attachment_zero_id(self, mcp_with_tools):
        """get_attachment should reject zero ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("get_attachment")
        with pytest.raises(ValueError, match="attachment_id must be a positive integer"):
            await tool.fn(attachment_id=0)

    @pytest.mark.asyncio
    async def test_delete_attachment_negative_id(self, mcp_with_tools):
        """delete_attachment should reject negative ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("delete_attachment")
        with pytest.raises(ValueError, match="attachment_id must be a positive integer"):
            await tool.fn(attachment_id=-1)

    @pytest.mark.asyncio
    async def test_create_attachment_path_traversal_slash(self, mcp_with_tools):
        """create_attachment should reject filenames with path separators."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_attachment")
        valid_b64 = base64.b64encode(b"test content").decode()
        with pytest.raises(ValueError, match="file_name contains path separator"):
            await tool.fn(title="Test", file_name="../etc/passwd", file_data=valid_b64)

    @pytest.mark.asyncio
    async def test_create_attachment_path_traversal_backslash(self, mcp_with_tools):
        """create_attachment should reject filenames with backslash."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_attachment")
        valid_b64 = base64.b64encode(b"test content").decode()
        with pytest.raises(ValueError, match="file_name contains path separator"):
            await tool.fn(title="Test", file_name="..\\etc\\passwd", file_data=valid_b64)

    @pytest.mark.asyncio
    async def test_create_attachment_invalid_base64(self, mcp_with_tools):
        """create_attachment should reject invalid base64 data."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_attachment")
        with pytest.raises(ValueError, match="file_data is not valid base64"):
            await tool.fn(title="Test", file_name="test.pdf", file_data="not!valid!base64!!!")

    @pytest.mark.asyncio
    async def test_create_attachment_oversized(self, mcp_with_tools):
        """create_attachment should reject files over 10MB."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_attachment")
        big_data = base64.b64encode(b"x" * (11 * 1024 * 1024)).decode()
        with pytest.raises(ValueError, match="exceeds maximum.*10MB"):
            await tool.fn(title="Test", file_name="big.bin", file_data=big_data)

    @pytest.mark.asyncio
    async def test_create_attachment_valid(self, mcp_with_tools, sample_attachment):
        """create_attachment should accept valid inputs."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_attachment
        valid_b64 = base64.b64encode(b"test PDF content").decode()

        tool = mcp._tool_manager._tools.get("create_attachment")
        result = await tool.fn(title="Receipt", file_name="receipt.pdf", file_data=valid_b64)

        data = json.loads(result)
        assert data["id"] == 700
        client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_attachment_filename_too_long(self, mcp_with_tools):
        """create_attachment should reject filenames over 255 chars."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_attachment")
        valid_b64 = base64.b64encode(b"test").decode()
        with pytest.raises(ValueError, match="file_name exceeds 255 characters"):
            await tool.fn(title="Test", file_name="a" * 256, file_data=valid_b64)
