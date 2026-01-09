"""Unit tests for category MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.categories import register_category_tools


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
    """Create FastMCP instance with category tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_category_tools(mcp, mock_client)
    return mcp, mock_client


class TestListCategories:
    """Tests for list_categories tool."""

    @pytest.mark.asyncio
    async def test_list_categories_success(self, mcp_with_tools, sample_category):
        """Test successful category listing."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_category]

        tool = mcp._tool_manager._tools.get("list_categories")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/123/categories")
        assert len(result_data) == 1
        assert result_data[0]["id"] == sample_category["id"]


class TestGetCategory:
    """Tests for get_category tool."""

    @pytest.mark.asyncio
    async def test_get_category_success(self, mcp_with_tools, sample_category):
        """Test successful category retrieval."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_category

        tool = mcp._tool_manager._tools.get("get_category")
        result = await tool.fn(category_id=100)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/categories/100")
        assert result_data["id"] == sample_category["id"]
        assert result_data["title"] == sample_category["title"]


class TestCreateCategory:
    """Tests for create_category tool."""

    @pytest.mark.asyncio
    async def test_create_category_basic(self, mcp_with_tools, sample_category):
        """Test basic category creation."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_category

        tool = mcp._tool_manager._tools.get("create_category")
        result = await tool.fn(user_id=123, title="Food & Dining")
        result_data = json.loads(result)

        client.post.assert_called_once_with(
            "/users/123/categories",
            json_data={
                "title": "Food & Dining",
                "is_transfer": False,
                "is_bill": False,
                "roll_up": False
            }
        )
        assert result_data["title"] == sample_category["title"]

    @pytest.mark.asyncio
    async def test_create_category_with_parent(self, mcp_with_tools, sample_category):
        """Test category creation with parent."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_category

        tool = mcp._tool_manager._tools.get("create_category")
        await tool.fn(user_id=123, title="Coffee", parent_id=50)

        client.post.assert_called_once()
        call_args = client.post.call_args
        assert call_args[1]["json_data"]["parent_id"] == 50

    @pytest.mark.asyncio
    async def test_create_category_income(self, mcp_with_tools, sample_category):
        """Test income category creation."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_category

        tool = mcp._tool_manager._tools.get("create_category")
        await tool.fn(user_id=123, title="Salary", is_transfer=False, is_bill=False)

        client.post.assert_called_once()


class TestUpdateCategory:
    """Tests for update_category tool."""

    @pytest.mark.asyncio
    async def test_update_category_title(self, mcp_with_tools, sample_category):
        """Test updating category title."""
        mcp, client = mcp_with_tools
        updated = {**sample_category, "title": "New Category Name"}
        client.put.return_value = updated

        tool = mcp._tool_manager._tools.get("update_category")
        result = await tool.fn(category_id=100, title="New Category Name")
        _result_data = json.loads(result)

        client.put.assert_called_once_with(
            "/categories/100",
            json_data={"title": "New Category Name"}
        )

    @pytest.mark.asyncio
    async def test_update_category_no_fields(self, mcp_with_tools):
        """Test error when no fields provided for update."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("update_category")

        with pytest.raises(ValueError, match="At least one field must be provided"):
            await tool.fn(category_id=100)


class TestDeleteCategory:
    """Tests for delete_category tool."""

    @pytest.mark.asyncio
    async def test_delete_category_success(self, mcp_with_tools):
        """Test successful category deletion."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_category")
        result = await tool.fn(category_id=100)
        result_data = json.loads(result)

        client.delete.assert_called_once_with("/categories/100")
        assert result_data["deleted"] is True
        assert result_data["category_id"] == 100
