"""Unit tests for user MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.users import register_user_tools


@pytest.fixture
def mock_client():
    """Create a mock PocketSmith client."""
    client = MagicMock()
    client.get = AsyncMock()
    client.put = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with user tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_user_tools(mcp, mock_client)
    return mcp, mock_client


class TestGetCurrentUser:
    """Tests for get_current_user tool."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mcp_with_tools, sample_user):
        """Test successful current user retrieval."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_user

        # Get the tool function
        tool = mcp._tool_manager._tools.get("get_current_user")
        assert tool is not None

        result = await tool.fn()
        result_data = json.loads(result)

        client.get.assert_called_once_with("/me")
        assert result_data["id"] == sample_user["id"]
        assert result_data["login"] == sample_user["login"]

    @pytest.mark.asyncio
    async def test_get_current_user_error(self, mcp_with_tools):
        """Test error handling for current user retrieval."""
        mcp, client = mcp_with_tools
        client.get.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("get_current_user")

        with pytest.raises(ValueError, match="Failed to get current user"):
            await tool.fn()


class TestGetUser:
    """Tests for get_user tool."""

    @pytest.mark.asyncio
    async def test_get_user_success(self, mcp_with_tools, sample_user):
        """Test successful user retrieval by ID."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_user

        tool = mcp._tool_manager._tools.get("get_user")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/123")
        assert result_data["id"] == sample_user["id"]

    @pytest.mark.asyncio
    async def test_get_user_error(self, mcp_with_tools):
        """Test error handling for user retrieval."""
        mcp, client = mcp_with_tools
        client.get.side_effect = Exception("User not found")

        tool = mcp._tool_manager._tools.get("get_user")

        with pytest.raises(ValueError, match="Failed to get user 123"):
            await tool.fn(user_id=123)


class TestUpdateUser:
    """Tests for update_user tool."""

    @pytest.mark.asyncio
    async def test_update_user_name(self, mcp_with_tools, sample_user):
        """Test updating user name."""
        mcp, client = mcp_with_tools
        updated_user = {**sample_user, "name": "New Name"}
        client.put.return_value = updated_user

        tool = mcp._tool_manager._tools.get("update_user")
        result = await tool.fn(user_id=123, name="New Name")
        result_data = json.loads(result)

        client.put.assert_called_once_with(
            "/users/123",
            json_data={"name": "New Name"}
        )
        assert result_data["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_user_email(self, mcp_with_tools, sample_user):
        """Test updating user email."""
        mcp, client = mcp_with_tools
        updated_user = {**sample_user, "email": "new@example.com"}
        client.put.return_value = updated_user

        tool = mcp._tool_manager._tools.get("update_user")
        result = await tool.fn(user_id=123, email="new@example.com")
        result_data = json.loads(result)

        client.put.assert_called_once_with(
            "/users/123",
            json_data={"email": "new@example.com"}
        )
        assert result_data["email"] == "new@example.com"

    @pytest.mark.asyncio
    async def test_update_user_multiple_fields(self, mcp_with_tools, sample_user):
        """Test updating multiple user fields."""
        mcp, client = mcp_with_tools
        updated_user = {
            **sample_user,
            "name": "New Name",
            "time_zone": "America/New_York"
        }
        client.put.return_value = updated_user

        tool = mcp._tool_manager._tools.get("update_user")
        result = await tool.fn(
            user_id=123,
            name="New Name",
            time_zone="America/New_York"
        )
        _result_data = json.loads(result)

        client.put.assert_called_once_with(
            "/users/123",
            json_data={"name": "New Name", "time_zone": "America/New_York"}
        )

    @pytest.mark.asyncio
    async def test_update_user_no_fields(self, mcp_with_tools):
        """Test error when no fields provided for update."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("update_user")

        with pytest.raises(ValueError, match="At least one field must be provided"):
            await tool.fn(user_id=123)

    @pytest.mark.asyncio
    async def test_update_user_error(self, mcp_with_tools):
        """Test error handling for user update."""
        mcp, client = mcp_with_tools
        client.put.side_effect = Exception("Update failed")

        tool = mcp._tool_manager._tools.get("update_user")

        with pytest.raises(ValueError, match="Failed to update user 123"):
            await tool.fn(user_id=123, name="New Name")
