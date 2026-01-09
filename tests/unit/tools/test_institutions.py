"""Unit tests for institution MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.institutions import register_institution_tools


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
    """Create FastMCP instance with institution tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_institution_tools(mcp, mock_client)
    return mcp, mock_client


@pytest.fixture
def sample_institution():
    """Sample institution data."""
    return {
        "id": 500,
        "title": "Chase Bank",
        "currency_code": "USD",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }


class TestListInstitutions:
    """Tests for list_institutions tool."""

    @pytest.mark.asyncio
    async def test_list_institutions_success(self, mcp_with_tools, sample_institution):
        """Test successful institution listing."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_institution]

        tool = mcp._tool_manager._tools.get("list_institutions")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/123/institutions")
        assert len(result_data) == 1
        assert result_data[0]["title"] == "Chase Bank"


class TestGetInstitution:
    """Tests for get_institution tool."""

    @pytest.mark.asyncio
    async def test_get_institution_success(self, mcp_with_tools, sample_institution):
        """Test successful institution retrieval."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_institution

        tool = mcp._tool_manager._tools.get("get_institution")
        result = await tool.fn(institution_id=500)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/institutions/500")
        assert result_data["id"] == 500


class TestCreateInstitution:
    """Tests for create_institution tool."""

    @pytest.mark.asyncio
    async def test_create_institution_success(self, mcp_with_tools, sample_institution):
        """Test successful institution creation."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_institution

        tool = mcp._tool_manager._tools.get("create_institution")
        result = await tool.fn(
            user_id=123,
            title="Chase Bank",
            currency_code="USD"
        )
        result_data = json.loads(result)

        client.post.assert_called_once_with(
            "/users/123/institutions",
            json_data={"title": "Chase Bank", "currency_code": "USD"}
        )
        assert result_data["title"] == "Chase Bank"


class TestUpdateInstitution:
    """Tests for update_institution tool."""

    @pytest.mark.asyncio
    async def test_update_institution_title(self, mcp_with_tools, sample_institution):
        """Test updating institution title."""
        mcp, client = mcp_with_tools
        updated = {**sample_institution, "title": "Chase Bank USA"}
        client.put.return_value = updated

        tool = mcp._tool_manager._tools.get("update_institution")
        _result = await tool.fn(institution_id=500, title="Chase Bank USA")

        client.put.assert_called_once_with(
            "/institutions/500",
            json_data={"title": "Chase Bank USA"}
        )

    @pytest.mark.asyncio
    async def test_update_institution_no_fields(self, mcp_with_tools):
        """Test error when no fields provided."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("update_institution")

        with pytest.raises(ValueError, match="At least one field must be provided"):
            await tool.fn(institution_id=500)


class TestDeleteInstitution:
    """Tests for delete_institution tool."""

    @pytest.mark.asyncio
    async def test_delete_institution_success(self, mcp_with_tools):
        """Test successful institution deletion."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_institution")
        result = await tool.fn(institution_id=500)
        result_data = json.loads(result)

        client.delete.assert_called_once_with("/institutions/500")
        assert result_data["deleted"] is True
