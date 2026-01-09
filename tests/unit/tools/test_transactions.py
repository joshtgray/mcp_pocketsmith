"""Unit tests for transaction MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.transactions import register_transaction_tools


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
    """Create FastMCP instance with transaction tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_transaction_tools(mcp, mock_client)
    return mcp, mock_client


class TestListTransactions:
    """Tests for list_transactions tool."""

    @pytest.mark.asyncio
    async def test_list_transactions_basic(self, mcp_with_tools, sample_transaction):
        """Test basic transaction listing."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_transaction]

        tool = mcp._tool_manager._tools.get("list_transactions")
        result = await tool.fn(user_id=123)
        result_data = json.loads(result)

        client.get.assert_called_once_with(
            "/users/123/transactions",
            params={"page": 1}
        )
        assert len(result_data) == 1
        assert result_data[0]["id"] == sample_transaction["id"]

    @pytest.mark.asyncio
    async def test_list_transactions_with_date_filter(self, mcp_with_tools, sample_transaction):
        """Test transaction listing with date filter."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_transaction]

        tool = mcp._tool_manager._tools.get("list_transactions")
        _result = await tool.fn(
            user_id=123,
            start_date="2024-01-01",
            end_date="2024-01-31"
        )

        client.get.assert_called_once_with(
            "/users/123/transactions",
            params={
                "page": 1,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }
        )

    @pytest.mark.asyncio
    async def test_list_transactions_with_search(self, mcp_with_tools, sample_transaction):
        """Test transaction listing with search query."""
        mcp, client = mcp_with_tools
        client.get.return_value = [sample_transaction]

        tool = mcp._tool_manager._tools.get("list_transactions")
        await tool.fn(user_id=123, search="coffee")

        client.get.assert_called_once_with(
            "/users/123/transactions",
            params={"page": 1, "search": "coffee"}
        )

    @pytest.mark.asyncio
    async def test_list_transactions_uncategorised(self, mcp_with_tools):
        """Test listing uncategorised transactions."""
        mcp, client = mcp_with_tools
        client.get.return_value = []

        tool = mcp._tool_manager._tools.get("list_transactions")
        await tool.fn(user_id=123, uncategorised=True)

        client.get.assert_called_once_with(
            "/users/123/transactions",
            params={"page": 1, "uncategorised": 1}
        )

    @pytest.mark.asyncio
    async def test_list_transactions_needs_review(self, mcp_with_tools):
        """Test listing transactions needing review."""
        mcp, client = mcp_with_tools
        client.get.return_value = []

        tool = mcp._tool_manager._tools.get("list_transactions")
        await tool.fn(user_id=123, needs_review=True)

        client.get.assert_called_once_with(
            "/users/123/transactions",
            params={"page": 1, "needs_review": 1}
        )


class TestGetTransaction:
    """Tests for get_transaction tool."""

    @pytest.mark.asyncio
    async def test_get_transaction_success(self, mcp_with_tools, sample_transaction):
        """Test successful transaction retrieval."""
        mcp, client = mcp_with_tools
        client.get.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("get_transaction")
        result = await tool.fn(transaction_id=456)
        result_data = json.loads(result)

        client.get.assert_called_once_with("/transactions/456")
        assert result_data["id"] == sample_transaction["id"]
        assert result_data["payee"] == sample_transaction["payee"]


class TestCreateTransaction:
    """Tests for create_transaction tool."""

    @pytest.mark.asyncio
    async def test_create_transaction_basic(self, mcp_with_tools, sample_transaction):
        """Test basic transaction creation."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("create_transaction")
        result = await tool.fn(
            transaction_account_id=789,
            payee="Starbucks",
            amount=-5.50,
            date="2024-01-15"
        )
        _result_data = json.loads(result)

        client.post.assert_called_once_with(
            "/transaction_accounts/789/transactions",
            json_data={
                "payee": "Starbucks",
                "amount": -5.50,
                "date": "2024-01-15",
                "is_transfer": False,
                "needs_review": False
            }
        )

    @pytest.mark.asyncio
    async def test_create_transaction_with_category(self, mcp_with_tools, sample_transaction):
        """Test transaction creation with category."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("create_transaction")
        await tool.fn(
            transaction_account_id=789,
            payee="Starbucks",
            amount=-5.50,
            date="2024-01-15",
            category_id=100
        )

        client.post.assert_called_once()
        call_args = client.post.call_args
        assert call_args[1]["json_data"]["category_id"] == 100

    @pytest.mark.asyncio
    async def test_create_transaction_with_labels(self, mcp_with_tools, sample_transaction):
        """Test transaction creation with labels."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("create_transaction")
        await tool.fn(
            transaction_account_id=789,
            payee="Starbucks",
            amount=-5.50,
            date="2024-01-15",
            labels=["coffee", "work"]
        )

        client.post.assert_called_once()
        call_args = client.post.call_args
        assert call_args[1]["json_data"]["labels"] == ["coffee", "work"]


class TestUpdateTransaction:
    """Tests for update_transaction tool."""

    @pytest.mark.asyncio
    async def test_update_transaction_payee(self, mcp_with_tools, sample_transaction):
        """Test updating transaction payee."""
        mcp, client = mcp_with_tools
        updated = {**sample_transaction, "payee": "New Payee"}
        client.put.return_value = updated

        tool = mcp._tool_manager._tools.get("update_transaction")
        result = await tool.fn(transaction_id=456, payee="New Payee")
        result_data = json.loads(result)

        client.put.assert_called_once_with(
            "/transactions/456",
            json_data={"payee": "New Payee"}
        )
        assert result_data["payee"] == "New Payee"

    @pytest.mark.asyncio
    async def test_update_transaction_category(self, mcp_with_tools, sample_transaction):
        """Test updating transaction category."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("update_transaction")
        await tool.fn(transaction_id=456, category_id=200)

        client.put.assert_called_once_with(
            "/transactions/456",
            json_data={"category_id": 200}
        )


class TestDeleteTransaction:
    """Tests for delete_transaction tool."""

    @pytest.mark.asyncio
    async def test_delete_transaction_success(self, mcp_with_tools):
        """Test successful transaction deletion."""
        mcp, client = mcp_with_tools
        client.delete.return_value = None

        tool = mcp._tool_manager._tools.get("delete_transaction")
        result = await tool.fn(transaction_id=456)
        result_data = json.loads(result)

        client.delete.assert_called_once_with("/transactions/456")
        assert result_data["deleted"] is True
        assert result_data["transaction_id"] == 456
