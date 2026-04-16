"""Unit tests for account MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.accounts import register_account_tools


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
    """Create FastMCP instance with account tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_account_tools(mcp, mock_client, user_ctx)
    return mcp, mock_client


class TestListAccounts:
    """Tests for list_accounts tool."""

    @pytest.mark.asyncio
    async def test_list_accounts_success(self, mcp_with_tools, sample_account):
        """Test successful account listing."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_account]

        tool = mcp._tool_manager._tools.get("list_accounts")
        result = await tool.fn()
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/42/accounts")
        assert len(result_data) == 1
        assert result_data[0]["id"] == sample_account["id"]

    @pytest.mark.asyncio
    async def test_list_accounts_error(self, mcp_with_tools):
        """Test error handling for account listing."""
        mcp, client = mcp_with_tools
        client.get.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("list_accounts")

        with pytest.raises(ValueError, match="Failed to list accounts"):
            await tool.fn()


class TestGetAccount:
    """Tests for get_account tool."""

    @pytest.mark.asyncio
    async def test_get_account_success(self, mcp_with_tools, sample_account):
        """Test successful account retrieval."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_account

        tool = mcp._tool_manager._tools.get("get_account")
        result = await tool.fn(account_id=456)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/accounts/456")
        assert result_data["id"] == sample_account["id"]
        assert result_data["title"] == sample_account["title"]


class TestUpdateAccount:
    """Tests for update_account tool."""

    @pytest.mark.asyncio
    async def test_update_account_title(self, mcp_with_tools, sample_account):
        """Test updating account title."""
        mcp, client = mcp_with_tools
        updated = {**sample_account, "title": "New Account Name"}
        client.put.return_value = updated

        tool = mcp._tool_manager._tools.get("update_account")
        result = await tool.fn(account_id=456, title="New Account Name")
        result_data = json.loads(result)

        client.put.assert_called_once_with(
            "/accounts/456",
            json_data={"title": "New Account Name"}
        )
        assert result_data["title"] == "New Account Name"

    @pytest.mark.asyncio
    async def test_update_account_no_fields(self, mcp_with_tools):
        """Test error when no fields provided for update."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("update_account")

        with pytest.raises(ValueError, match="At least one field must be provided"):
            await tool.fn(account_id=456)


class TestDeleteAccount:
    """Tests for delete_account tool."""

    @pytest.mark.asyncio
    async def test_delete_account_success(self, mcp_with_tools):
        """Test successful account deletion."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_account")
        result = await tool.fn(account_id=456)
        result_data = json.loads(result)

        client.delete.assert_called_once_with("/accounts/456")
        assert result_data["deleted"] is True
        assert result_data["account_id"] == 456


class TestAccountIdValidation:
    """Tests for ID validation on account tools."""

    @pytest.mark.asyncio
    async def test_get_account_zero_id(self, mcp_with_tools):
        """get_account should reject zero ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("get_account")
        with pytest.raises(ValueError, match="account_id must be a positive integer"):
            await tool.fn(account_id=0)

    @pytest.mark.asyncio
    async def test_get_account_negative_id(self, mcp_with_tools):
        """get_account should reject negative ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("get_account")
        with pytest.raises(ValueError, match="account_id must be a positive integer"):
            await tool.fn(account_id=-1)

    @pytest.mark.asyncio
    async def test_update_account_zero_id(self, mcp_with_tools):
        """update_account should reject zero ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("update_account")
        with pytest.raises(ValueError, match="account_id must be a positive integer"):
            await tool.fn(account_id=0, title="Test")

    @pytest.mark.asyncio
    async def test_delete_account_negative_id(self, mcp_with_tools):
        """delete_account should reject negative ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("delete_account")
        with pytest.raises(ValueError, match="account_id must be a positive integer"):
            await tool.fn(account_id=-1)


class TestCreateAccount:
    """Tests for create_account tool."""

    @pytest.mark.asyncio
    async def test_create_account_basic(self, mcp_with_tools, sample_account):
        """create_account should use user_ctx.user_id in the URL, not an explicit user_id."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_account

        tool = mcp._tool_manager._tools.get("create_account")
        result = await tool.fn(
            institution_id=10,
            title="Savings",
            currency_code="AUD",
            type="bank",
        )
        result_data = json.loads(result)

        client.post.assert_called_once_with(
            "/users/42/accounts",
            json_data={
                "institution_id": 10,
                "title": "Savings",
                "currency_code": "AUD",
                "type": "bank",
            },
        )
        assert result_data["id"] == sample_account["id"]

    @pytest.mark.asyncio
    async def test_create_account_url_uses_user_ctx(self, mcp_with_tools, sample_account):
        """Verify the URL uses the user_ctx user_id (42) not a separately passed value."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_account

        tool = mcp._tool_manager._tools.get("create_account")
        await tool.fn(
            institution_id=99,
            title="Credit Card",
            currency_code="AUD",
            type="credits",
        )

        call_args = client.post.call_args
        assert call_args[0][0] == "/users/42/accounts"


class TestUpdateAccountDisplayOrder:
    """Tests for update_account_display_order tool."""

    @pytest.mark.asyncio
    async def test_update_display_order_uses_user_ctx(self, mcp_with_tools, sample_account):
        """update_account_display_order should use user_ctx.user_id in the URL."""
        mcp, client = mcp_with_tools
        client.put.return_value = [sample_account]

        tool = mcp._tool_manager._tools.get("update_account_display_order")
        result = await tool.fn(accounts=[{"id": 1}, {"id": 2}])
        result_data = json.loads(result)

        client.put.assert_called_once_with(
            "/users/42/accounts",
            json_data={"accounts": [{"id": 1}, {"id": 2}]},
        )
        assert isinstance(result_data, list)

    @pytest.mark.asyncio
    async def test_update_display_order_url_uses_user_ctx(self, mcp_with_tools, sample_account):
        """Verify the URL contains the user_ctx user_id (42)."""
        mcp, client = mcp_with_tools
        client.put.return_value = [sample_account]

        tool = mcp._tool_manager._tools.get("update_account_display_order")
        await tool.fn(accounts=[{"id": 5}])

        call_args = client.put.call_args
        assert call_args[0][0] == "/users/42/accounts"
