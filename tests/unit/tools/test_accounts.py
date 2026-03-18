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
def mcp_with_tools(mock_client):
    """Create FastMCP instance with account tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_account_tools(mcp, mock_client)
    return mcp, mock_client


class TestListAccounts:
    """Tests for list_accounts tool."""

    @pytest.mark.asyncio
    async def test_list_accounts_success(self, mcp_with_tools, sample_account):
        """Test successful account listing."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_account]

        tool = mcp._tool_manager._tools.get("list_accounts")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/123/accounts")
        assert len(result_data) == 1
        assert result_data[0]["id"] == sample_account["id"]

    @pytest.mark.asyncio
    async def test_list_accounts_error(self, mcp_with_tools):
        """Test error handling for account listing."""
        mcp, client = mcp_with_tools
        client.get.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("list_accounts")

        with pytest.raises(ValueError, match="Failed to list accounts"):
            await tool.fn(user_id=123)


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


class TestCreateAccount:
    """Tests for create_account tool."""

    @pytest.mark.asyncio
    async def test_create_account_success(self, mcp_with_tools, sample_account):
        """Test successful account creation with all required params."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_account

        tool = mcp._tool_manager._tools.get("create_account")
        result = await tool.fn(
            user_id=123,
            institution_id=500,
            title="Main Checking",
            currency_code="NZD",
            type="bank",
        )
        result_data = json.loads(result)

        client.post.assert_called_once_with(
            "/users/123/accounts",
            json_data={
                "institution_id": 500,
                "title": "Main Checking",
                "currency_code": "NZD",
                "type": "bank",
            },
        )
        assert result_data["id"] == sample_account["id"]
        assert result_data["title"] == "Main Checking"

    @pytest.mark.asyncio
    async def test_create_account_required_params(self, mcp_with_tools):
        """Test that all four required params are sent in the body."""
        mcp, client = mcp_with_tools
        created = {
            "id": 99,
            "title": "Savings",
            "currency_code": "USD",
            "type": "bank",
            "is_net_worth": True,
            "current_balance": 0,
            "current_balance_date": "2026-03-18",
            "current_balance_in_base_currency": 0,
            "safe_balance": None,
            "created_at": "2026-03-18T00:00:00Z",
            "updated_at": "2026-03-18T00:00:00Z",
            "transaction_accounts": [],
            "scenarios": [],
        }
        client.post.return_value = created

        tool = mcp._tool_manager._tools.get("create_account")
        result = await tool.fn(
            user_id=1,
            institution_id=42,
            title="Savings",
            currency_code="USD",
            type="bank",
        )
        result_data = json.loads(result)

        call_args = client.post.call_args
        body = call_args.kwargs.get("json_data") or call_args[1].get("json_data")
        assert body["institution_id"] == 42
        assert body["title"] == "Savings"
        assert body["currency_code"] == "USD"
        assert body["type"] == "bank"
        assert result_data["id"] == 99

    @pytest.mark.asyncio
    async def test_create_account_all_types(self, mcp_with_tools, sample_account):
        """Test creating account with each valid account type."""
        mcp, client = mcp_with_tools
        valid_types = [
            "bank", "credits", "cash", "loans", "mortgage",
            "stocks", "vehicle", "property", "insurance",
            "other_asset", "other_liability",
        ]

        tool = mcp._tool_manager._tools.get("create_account")

        for acct_type in valid_types:
            client.post.reset_mock()
            client.post.return_value = {**sample_account, "type": acct_type}

            result = await tool.fn(
                user_id=1,
                institution_id=42,
                title="Test",
                currency_code="NZD",
                type=acct_type,
            )
            result_data = json.loads(result)
            assert result_data["type"] == acct_type

    @pytest.mark.asyncio
    async def test_create_account_error(self, mcp_with_tools):
        """Test error handling for account creation."""
        mcp, client = mcp_with_tools
        client.post.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("create_account")

        with pytest.raises(ValueError, match="Failed to create account"):
            await tool.fn(
                user_id=123,
                institution_id=500,
                title="Test",
                currency_code="NZD",
                type="bank",
            )
