"""Unit tests for transaction account MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.transaction_accounts import register_transaction_account_tools


@pytest.fixture
def mock_client():
    """Create a mock PocketSmith client."""
    client = MagicMock()
    client.get = AsyncMock()
    client.put = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with transaction account tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_transaction_account_tools(mcp, mock_client)
    return mcp, mock_client


@pytest.fixture
def sample_transaction_account():
    """Sample transaction account data."""
    return {
        "id": 800,
        "name": "Main Checking",
        "number": "****1234",
        "type": "bank",
        "currency_code": "USD",
        "starting_balance": 1000.00,
        "current_balance": 5000.00
    }


class TestListTransactionAccounts:
    """Tests for list_transaction_accounts tool."""

    @pytest.mark.asyncio
    async def test_list_transaction_accounts_success(
        self, mcp_with_tools, sample_transaction_account
    ):
        """Test successful transaction account listing."""
        mcp, client = mcp_with_tools
        # list_transaction_accounts fetches accounts and extracts transaction_accounts
        accounts_response = [{
            "id": 1,
            "title": "Savings",
            "transaction_accounts": [sample_transaction_account]
        }]
        client.get.return_value = accounts_response

        tool = mcp._tool_manager._tools.get("list_transaction_accounts")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/users/123/accounts")
        assert len(result_data) == 1
        assert result_data[0]["name"] == "Main Checking"

    @pytest.mark.asyncio
    async def test_list_transaction_accounts_error(self, mcp_with_tools):
        """Test error handling."""
        mcp, client = mcp_with_tools
        client.get.side_effect = Exception("API Error")

        tool = mcp._tool_manager._tools.get("list_transaction_accounts")

        with pytest.raises(ValueError, match="Failed to list transaction accounts"):
            await tool.fn(user_id=123)


class TestGetTransactionAccount:
    """Tests for get_transaction_account tool."""

    @pytest.mark.asyncio
    async def test_get_transaction_account_success(
        self, mcp_with_tools, sample_transaction_account
    ):
        """Test successful transaction account retrieval."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_transaction_account

        tool = mcp._tool_manager._tools.get("get_transaction_account")
        result = await tool.fn(transaction_account_id=800)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/transaction_accounts/800")
        assert result_data["id"] == 800


class TestUpdateTransactionAccount:
    """Tests for update_transaction_account tool."""

    @pytest.mark.asyncio
    async def test_update_transaction_account_name(
        self, mcp_with_tools, sample_transaction_account
    ):
        """Test updating transaction account name."""
        mcp, client = mcp_with_tools
        updated = {**sample_transaction_account, "name": "Primary Checking"}
        client.put.return_value = updated

        tool = mcp._tool_manager._tools.get("update_transaction_account")
        _result = await tool.fn(transaction_account_id=800, name="Primary Checking")

        client.put.assert_called_once_with(
            "/transaction_accounts/800",
            json_data={"name": "Primary Checking"}
        )

    @pytest.mark.asyncio
    async def test_update_transaction_account_starting_balance(
        self, mcp_with_tools, sample_transaction_account
    ):
        """Test updating starting balance."""
        mcp, client = mcp_with_tools
        updated = {**sample_transaction_account, "starting_balance": 2000.00}
        client.put.return_value = updated

        tool = mcp._tool_manager._tools.get("update_transaction_account")
        await tool.fn(transaction_account_id=800, starting_balance=2000.00)

        client.put.assert_called_once_with(
            "/transaction_accounts/800",
            json_data={"starting_balance": 2000.00}
        )

    @pytest.mark.asyncio
    async def test_update_transaction_account_no_fields(self, mcp_with_tools):
        """Test error when no fields provided."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("update_transaction_account")

        with pytest.raises(ValueError, match="At least one field must be provided"):
            await tool.fn(transaction_account_id=800)
