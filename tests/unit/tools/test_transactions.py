"""Unit tests for transaction MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PaginatedResponse
from pocketsmith_mcp.tools.transactions import register_transaction_tools


@pytest.fixture
def mock_client():
    """Create a mock PocketSmith client."""
    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    client.get_paginated = AsyncMock(return_value=PaginatedResponse(data=[]))
    return client


@pytest.fixture
def mcp_with_tools(mock_client, user_ctx):
    """Create FastMCP instance with transaction tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_transaction_tools(mcp, mock_client, user_ctx)
    return mcp, mock_client


class TestListTransactions:
    """Tests for list_transactions tool."""

    @pytest.mark.asyncio
    async def test_list_transactions_basic(self, mcp_with_tools, sample_transaction):
        """Test basic transaction listing."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions")
        result = await tool.fn()
        result_data = json.loads(result)

        client.get_paginated.assert_called_once_with(
            "/users/42/transactions",
            params={"page": 1, "per_page": 1000}
        )
        assert len(result_data) == 1
        assert result_data[0]["id"] == sample_transaction["id"]

    @pytest.mark.asyncio
    async def test_list_transactions_with_date_filter(self, mcp_with_tools, sample_transaction):
        """Test transaction listing with date filter."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions")
        _result = await tool.fn(
            start_date="2024-01-01",
            end_date="2024-01-31"
        )

        client.get_paginated.assert_called_once_with(
            "/users/42/transactions",
            params={
                "page": 1,
                "per_page": 1000,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }
        )

    @pytest.mark.asyncio
    async def test_list_transactions_with_search(self, mcp_with_tools, sample_transaction):
        """Test transaction listing with search query."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions")
        await tool.fn(search="coffee")

        client.get_paginated.assert_called_once_with(
            "/users/42/transactions",
            params={"page": 1, "per_page": 1000, "search": "coffee"}
        )

    @pytest.mark.asyncio
    async def test_list_transactions_uncategorised(self, mcp_with_tools):
        """Test listing uncategorised transactions."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[])

        tool = mcp._tool_manager._tools.get("list_transactions")
        await tool.fn(uncategorised=True)

        client.get_paginated.assert_called_once_with(
            "/users/42/transactions",
            params={"page": 1, "per_page": 1000, "uncategorised": 1}
        )

    @pytest.mark.asyncio
    async def test_list_transactions_needs_review(self, mcp_with_tools):
        """Test listing transactions needing review."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[])

        tool = mcp._tool_manager._tools.get("list_transactions")
        await tool.fn(needs_review=True)

        client.get_paginated.assert_called_once_with(
            "/users/42/transactions",
            params={"page": 1, "per_page": 1000, "needs_review": 1}
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
        """Test transaction creation with labels — list is joined to comma-separated string."""
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
        assert call_args[1]["json_data"]["labels"] == "coffee,work"


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


class TestUpdateTransactionLabels:
    """Tests for labels type conversion in update_transaction."""

    @pytest.mark.asyncio
    async def test_update_transaction_labels_joined(self, mcp_with_tools, sample_transaction):
        """update_transaction should convert labels list to comma-separated string."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("update_transaction")
        await tool.fn(transaction_id=456, labels=["foo", "bar", "baz"])

        call_args = client.put.call_args
        assert call_args[1]["json_data"]["labels"] == "foo,bar,baz"

    @pytest.mark.asyncio
    async def test_update_transaction_single_label(self, mcp_with_tools, sample_transaction):
        """Single-item labels list should produce a string without trailing comma."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("update_transaction")
        await tool.fn(transaction_id=456, labels=["food"])

        call_args = client.put.call_args
        assert call_args[1]["json_data"]["labels"] == "food"


class TestCreateTransactionLabelValidation:
    """Tests for label comma validation in create_transaction."""

    @pytest.mark.asyncio
    async def test_label_with_comma_raises(self, mcp_with_tools):
        """create_transaction should reject labels containing commas."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_transaction")
        with pytest.raises(ValueError, match="contains a comma"):
            await tool.fn(
                transaction_account_id=789,
                payee="Starbucks",
                amount=-5.50,
                date="2024-01-15",
                labels=["food,drink"],
            )

    @pytest.mark.asyncio
    async def test_labels_whitespace_stripped(self, mcp_with_tools, sample_transaction):
        """create_transaction should strip leading/trailing whitespace from labels."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("create_transaction")
        await tool.fn(
            transaction_account_id=789,
            payee="Starbucks",
            amount=-5.50,
            date="2024-01-15",
            labels=[" coffee ", " work"],
        )

        call_args = client.post.call_args
        assert call_args[1]["json_data"]["labels"] == "coffee,work"

    @pytest.mark.asyncio
    async def test_labels_valid_unchanged(self, mcp_with_tools, sample_transaction):
        """create_transaction should pass valid labels through unchanged."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("create_transaction")
        await tool.fn(
            transaction_account_id=789,
            payee="Starbucks",
            amount=-5.50,
            date="2024-01-15",
            labels=["food", "work"],
        )

        call_args = client.post.call_args
        assert call_args[1]["json_data"]["labels"] == "food,work"

    @pytest.mark.asyncio
    async def test_whitespace_only_label_excluded(self, mcp_with_tools, sample_transaction):
        """create_transaction should exclude whitespace-only labels (empty after strip)."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("create_transaction")
        await tool.fn(
            transaction_account_id=789,
            payee="Starbucks",
            amount=-5.50,
            date="2024-01-15",
            labels=[" "],
        )

        call_args = client.post.call_args
        assert "labels" not in call_args[1]["json_data"]

    @pytest.mark.asyncio
    async def test_mixed_labels_whitespace_only_filtered(self, mcp_with_tools, sample_transaction):
        """create_transaction should filter whitespace-only entries from a mixed list."""
        mcp, client = mcp_with_tools
        client.post.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("create_transaction")
        await tool.fn(
            transaction_account_id=789,
            payee="Starbucks",
            amount=-5.50,
            date="2024-01-15",
            labels=["food", " ", "groceries"],
        )

        call_args = client.post.call_args
        assert call_args[1]["json_data"]["labels"] == "food,groceries"


class TestUpdateTransactionLabelValidation:
    """Tests for label comma validation in update_transaction."""

    @pytest.mark.asyncio
    async def test_label_with_comma_raises(self, mcp_with_tools):
        """update_transaction should reject labels containing commas."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("update_transaction")
        with pytest.raises(ValueError, match="contains a comma"):
            await tool.fn(transaction_id=456, labels=["food,drink"])

    @pytest.mark.asyncio
    async def test_labels_whitespace_stripped(self, mcp_with_tools, sample_transaction):
        """update_transaction should strip leading/trailing whitespace from labels."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("update_transaction")
        await tool.fn(transaction_id=456, labels=[" foo ", "bar "])

        call_args = client.put.call_args
        assert call_args[1]["json_data"]["labels"] == "foo,bar"

    @pytest.mark.asyncio
    async def test_labels_valid_unchanged(self, mcp_with_tools, sample_transaction):
        """update_transaction should pass valid labels through unchanged."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("update_transaction")
        await tool.fn(transaction_id=456, labels=["food", "work"])

        call_args = client.put.call_args
        assert call_args[1]["json_data"]["labels"] == "food,work"

    @pytest.mark.asyncio
    async def test_whitespace_only_label_excluded(self, mcp_with_tools, sample_transaction):
        """update_transaction should exclude whitespace-only labels (empty after strip)."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("update_transaction")
        await tool.fn(transaction_id=456, labels=[" "], needs_review=False)

        call_args = client.put.call_args
        assert "labels" not in call_args[1]["json_data"]

    @pytest.mark.asyncio
    async def test_mixed_labels_whitespace_only_filtered(self, mcp_with_tools, sample_transaction):
        """update_transaction should filter whitespace-only entries from a mixed list."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("update_transaction")
        await tool.fn(transaction_id=456, labels=["food", " ", "groceries"])

        call_args = client.put.call_args
        assert call_args[1]["json_data"]["labels"] == "food,groceries"


class TestUpdateTransactionSplits:
    """Tests for splits support in update_transaction."""

    @pytest.mark.asyncio
    async def test_update_transaction_with_splits(self, mcp_with_tools, sample_transaction):
        """Providing splits should include them in the request body."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_transaction

        splits = [
            {"amount": -3.00, "payee": "Coffee", "category_id": 10},
            {"amount": -2.50, "payee": "Tip", "category_id": 11},
        ]
        tool = mcp._tool_manager._tools.get("update_transaction")
        await tool.fn(transaction_id=456, splits=splits)

        call_args = client.put.call_args
        assert call_args[1]["json_data"]["splits"] == splits

    @pytest.mark.asyncio
    async def test_update_transaction_without_splits(self, mcp_with_tools, sample_transaction):
        """Omitting splits should not include the key in the request body."""
        mcp, client = mcp_with_tools
        client.put.return_value = sample_transaction

        tool = mcp._tool_manager._tools.get("update_transaction")
        await tool.fn(transaction_id=456, payee="New Payee")

        call_args = client.put.call_args
        assert "splits" not in call_args[1]["json_data"]


class TestListTransactionsByAccount:
    """Tests for list_transactions_by_account tool."""

    @pytest.mark.asyncio
    async def test_basic(self, mcp_with_tools, sample_transaction):
        """Test basic listing by account."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions_by_account")
        result = await tool.fn(account_id=10)
        result_data = json.loads(result)

        client.get_paginated.assert_called_once_with(
            "/accounts/10/transactions", params={"page": 1, "per_page": 1000}
        )
        assert len(result_data) == 1

    @pytest.mark.asyncio
    async def test_with_date_filter(self, mcp_with_tools, sample_transaction):
        """Test listing by account with date filter."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions_by_account")
        await tool.fn(account_id=10, start_date="2024-01-01", end_date="2024-01-31")

        client.get_paginated.assert_called_once_with(
            "/accounts/10/transactions",
            params={
                "page": 1, "per_page": 1000,
                "start_date": "2024-01-01", "end_date": "2024-01-31",
            },
        )

    @pytest.mark.asyncio
    async def test_invalid_account_id(self, mcp_with_tools):
        """list_transactions_by_account should reject zero account_id."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_transactions_by_account")
        with pytest.raises(ValueError, match="account_id must be a positive integer"):
            await tool.fn(account_id=0)


class TestListTransactionsByTransactionAccount:
    """Tests for list_transactions_by_transaction_account tool."""

    @pytest.mark.asyncio
    async def test_basic(self, mcp_with_tools, sample_transaction):
        """Test basic listing by transaction account."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions_by_transaction_account")
        result = await tool.fn(transaction_account_id=20)
        result_data = json.loads(result)

        client.get_paginated.assert_called_once_with(
            "/transaction_accounts/20/transactions", params={"page": 1, "per_page": 1000}
        )
        assert len(result_data) == 1

    @pytest.mark.asyncio
    async def test_with_search(self, mcp_with_tools, sample_transaction):
        """Test listing by transaction account with search filter."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions_by_transaction_account")
        await tool.fn(transaction_account_id=20, search="coffee")

        client.get_paginated.assert_called_once_with(
            "/transaction_accounts/20/transactions",
            params={"page": 1, "per_page": 1000, "search": "coffee"},
        )

    @pytest.mark.asyncio
    async def test_invalid_id(self, mcp_with_tools):
        """list_transactions_by_transaction_account should reject zero ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_transactions_by_transaction_account")
        with pytest.raises(ValueError, match="transaction_account_id must be a positive integer"):
            await tool.fn(transaction_account_id=0)


class TestListTransactionsByCategory:
    """Tests for list_transactions_by_category tool."""

    @pytest.mark.asyncio
    async def test_basic(self, mcp_with_tools, sample_transaction):
        """Test basic listing by category."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions_by_category")
        result = await tool.fn(category_id=5)
        result_data = json.loads(result)

        client.get_paginated.assert_called_once_with(
            "/categories/5/transactions", params={"page": 1, "per_page": 1000}
        )
        assert len(result_data) == 1

    @pytest.mark.asyncio
    async def test_with_uncategorised_flag(self, mcp_with_tools):
        """Test listing by category with uncategorised flag."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[])

        tool = mcp._tool_manager._tools.get("list_transactions_by_category")
        await tool.fn(category_id=5, uncategorised=True)

        client.get_paginated.assert_called_once_with(
            "/categories/5/transactions",
            params={"page": 1, "per_page": 1000, "uncategorised": 1},
        )

    @pytest.mark.asyncio
    async def test_invalid_category_id(self, mcp_with_tools):
        """list_transactions_by_category should reject zero category_id."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_transactions_by_category")
        with pytest.raises(ValueError, match="category_id must be a positive integer"):
            await tool.fn(category_id=0)


class TestTransactionIdValidation:
    """Tests for ID validation on transaction tools."""

    @pytest.mark.asyncio
    async def test_get_transaction_zero_id(self, mcp_with_tools):
        """get_transaction should reject zero ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("get_transaction")
        with pytest.raises(ValueError, match="transaction_id must be a positive integer"):
            await tool.fn(transaction_id=0)

    @pytest.mark.asyncio
    async def test_create_transaction_zero_account_id(self, mcp_with_tools):
        """create_transaction should reject zero transaction_account_id."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("create_transaction")
        with pytest.raises(ValueError, match="transaction_account_id must be a positive integer"):
            await tool.fn(transaction_account_id=0, payee="Test", amount=-5, date="2024-01-01")

    @pytest.mark.asyncio
    async def test_update_transaction_negative_id(self, mcp_with_tools):
        """update_transaction should reject negative ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("update_transaction")
        with pytest.raises(ValueError, match="transaction_id must be a positive integer"):
            await tool.fn(transaction_id=-1, payee="Test")

    @pytest.mark.asyncio
    async def test_delete_transaction_zero_id(self, mcp_with_tools):
        """delete_transaction should reject zero ID."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("delete_transaction")
        with pytest.raises(ValueError, match="transaction_id must be a positive integer"):
            await tool.fn(transaction_id=0)


class TestListTransactionsPerPage:
    """Tests for per_page parameter on all transaction list tools."""

    @pytest.mark.asyncio
    async def test_list_transactions_custom_per_page(self, mcp_with_tools, sample_transaction):
        """list_transactions should pass custom per_page value."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions")
        await tool.fn(per_page=100)

        client.get_paginated.assert_called_once_with(
            "/users/42/transactions",
            params={"page": 1, "per_page": 100},
        )

    @pytest.mark.asyncio
    async def test_list_transactions_per_page_too_low(self, mcp_with_tools):
        """list_transactions should reject per_page below 10."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_transactions")
        with pytest.raises(ValueError, match="per_page must be between 10 and 1000"):
            await tool.fn(per_page=5)

    @pytest.mark.asyncio
    async def test_list_transactions_per_page_too_high(self, mcp_with_tools):
        """list_transactions should reject per_page above 1000."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_transactions")
        with pytest.raises(ValueError, match="per_page must be between 10 and 1000"):
            await tool.fn(per_page=1001)

    @pytest.mark.asyncio
    async def test_list_by_account_custom_per_page(self, mcp_with_tools, sample_transaction):
        """list_transactions_by_account should pass custom per_page value."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions_by_account")
        await tool.fn(account_id=10, per_page=50)

        client.get_paginated.assert_called_once_with(
            "/accounts/10/transactions",
            params={"page": 1, "per_page": 50},
        )

    @pytest.mark.asyncio
    async def test_list_by_account_per_page_too_low(self, mcp_with_tools):
        """list_transactions_by_account should reject per_page below 10."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_transactions_by_account")
        with pytest.raises(ValueError, match="per_page must be between 10 and 1000"):
            await tool.fn(account_id=10, per_page=9)

    @pytest.mark.asyncio
    async def test_list_by_account_per_page_too_high(self, mcp_with_tools):
        """list_transactions_by_account should reject per_page above 1000."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_transactions_by_account")
        with pytest.raises(ValueError, match="per_page must be between 10 and 1000"):
            await tool.fn(account_id=10, per_page=1001)

    @pytest.mark.asyncio
    async def test_list_by_transaction_account_custom_per_page(
        self, mcp_with_tools, sample_transaction
    ):
        """list_transactions_by_transaction_account should pass custom per_page value."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions_by_transaction_account")
        await tool.fn(transaction_account_id=20, per_page=200)

        client.get_paginated.assert_called_once_with(
            "/transaction_accounts/20/transactions",
            params={"page": 1, "per_page": 200},
        )

    @pytest.mark.asyncio
    async def test_list_by_transaction_account_per_page_too_low(self, mcp_with_tools):
        """list_transactions_by_transaction_account should reject per_page below 10."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_transactions_by_transaction_account")
        with pytest.raises(ValueError, match="per_page must be between 10 and 1000"):
            await tool.fn(transaction_account_id=20, per_page=5)

    @pytest.mark.asyncio
    async def test_list_by_transaction_account_per_page_too_high(self, mcp_with_tools):
        """list_transactions_by_transaction_account should reject per_page above 1000."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_transactions_by_transaction_account")
        with pytest.raises(ValueError, match="per_page must be between 10 and 1000"):
            await tool.fn(transaction_account_id=20, per_page=1001)

    @pytest.mark.asyncio
    async def test_list_by_category_custom_per_page(self, mcp_with_tools, sample_transaction):
        """list_transactions_by_category should pass custom per_page value."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(data=[sample_transaction])

        tool = mcp._tool_manager._tools.get("list_transactions_by_category")
        await tool.fn(category_id=5, per_page=500)

        client.get_paginated.assert_called_once_with(
            "/categories/5/transactions",
            params={"page": 1, "per_page": 500},
        )

    @pytest.mark.asyncio
    async def test_list_by_category_per_page_too_low(self, mcp_with_tools):
        """list_transactions_by_category should reject per_page below 10."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_transactions_by_category")
        with pytest.raises(ValueError, match="per_page must be between 10 and 1000"):
            await tool.fn(category_id=5, per_page=9)

    @pytest.mark.asyncio
    async def test_list_by_category_per_page_too_high(self, mcp_with_tools):
        """list_transactions_by_category should reject per_page above 1000."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("list_transactions_by_category")
        with pytest.raises(ValueError, match="per_page must be between 10 and 1000"):
            await tool.fn(category_id=5, per_page=1001)


class TestTransactionPaginationMetadata:
    """Tests for truncation warnings and pagination metadata in transaction list tools."""

    @pytest.mark.asyncio
    async def test_list_transactions_includes_pagination_metadata_when_has_next(
        self, mcp_with_tools, sample_transaction
    ):
        """list_transactions wraps response with _pagination when has_next=True."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(
            data=[sample_transaction] * 1000,
            total=2000,
            per_page=1000,
            page=1,
            has_next=True,
        )

        tool = mcp._tool_manager._tools.get("list_transactions")
        result = await tool.fn()
        result_data = json.loads(result)

        assert "data" in result_data
        assert "_pagination" in result_data
        assert result_data["_pagination"]["total"] == 2000
        assert result_data["_pagination"]["has_more"] is True
        assert result_data["_pagination"]["per_page"] == 1000
        assert result_data["_pagination"]["page"] == 1
        assert len(result_data["data"]) == 1000

    @pytest.mark.asyncio
    async def test_list_transactions_plain_array_when_total_known_and_fits_on_one_page(
        self, mcp_with_tools, sample_transaction
    ):
        """list_transactions returns plain array when total is known and fits within per_page."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(
            data=[sample_transaction] * 500,
            total=500,
            per_page=1000,
            page=1,
            has_next=False,
        )

        tool = mcp._tool_manager._tools.get("list_transactions")
        result = await tool.fn()
        result_data = json.loads(result)

        assert isinstance(result_data, list)
        assert len(result_data) == 500

    @pytest.mark.asyncio
    async def test_list_transactions_truncation_warning_when_full_page(
        self, mcp_with_tools, sample_transaction
    ):
        """list_transactions adds _warning when exactly per_page results and no total header."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(
            data=[sample_transaction] * 1000,
            total=None,
            per_page=None,
            page=1,
            has_next=False,
        )

        tool = mcp._tool_manager._tools.get("list_transactions")
        result = await tool.fn()
        result_data = json.loads(result)

        assert "data" in result_data
        assert "_pagination" in result_data
        assert result_data["_pagination"]["has_more"] is None
        assert "_warning" in result_data["_pagination"]

    @pytest.mark.asyncio
    async def test_list_transactions_plain_array_when_partial_page(
        self, mcp_with_tools, sample_transaction
    ):
        """list_transactions returns plain array when fewer than per_page results."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(
            data=[sample_transaction, sample_transaction],
            total=None,
            per_page=None,
            page=1,
            has_next=False,
        )

        tool = mcp._tool_manager._tools.get("list_transactions")
        result = await tool.fn()
        result_data = json.loads(result)

        assert isinstance(result_data, list)
        assert len(result_data) == 2

    @pytest.mark.asyncio
    async def test_list_transactions_by_account_pagination_metadata(
        self, mcp_with_tools, sample_transaction
    ):
        """list_transactions_by_account includes _pagination when has_next=True."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(
            data=[sample_transaction] * 1000,
            total=3000,
            per_page=1000,
            page=1,
            has_next=True,
        )

        tool = mcp._tool_manager._tools.get("list_transactions_by_account")
        result = await tool.fn(account_id=10)
        result_data = json.loads(result)

        assert "data" in result_data
        assert result_data["_pagination"]["total"] == 3000
        assert result_data["_pagination"]["has_more"] is True

    @pytest.mark.asyncio
    async def test_list_transactions_by_transaction_account_truncation_warning(
        self, mcp_with_tools, sample_transaction
    ):
        """list_transactions_by_transaction_account adds _warning when exactly per_page results."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(
            data=[sample_transaction] * 1000,
            total=None,
            per_page=None,
            page=1,
            has_next=False,
        )

        tool = mcp._tool_manager._tools.get("list_transactions_by_transaction_account")
        result = await tool.fn(transaction_account_id=20)
        result_data = json.loads(result)

        assert "_pagination" in result_data
        assert "_warning" in result_data["_pagination"]

    @pytest.mark.asyncio
    async def test_list_transactions_by_category_plain_array_when_partial(
        self, mcp_with_tools, sample_transaction
    ):
        """list_transactions_by_category returns plain array when results < per_page."""
        mcp, client = mcp_with_tools
        client.get_paginated.return_value = PaginatedResponse(
            data=[sample_transaction] * 5,
            total=None,
            per_page=None,
            page=1,
            has_next=False,
        )

        tool = mcp._tool_manager._tools.get("list_transactions_by_category")
        result = await tool.fn(category_id=5)
        result_data = json.loads(result)

        assert isinstance(result_data, list)
        assert len(result_data) == 5
