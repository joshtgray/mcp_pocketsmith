"""Unit tests for bulk transaction MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.tools.bulk_transactions import register_bulk_transaction_tools


@pytest.fixture
def mock_client():
    """Create a mock PocketSmith client."""
    client = MagicMock()
    client.put = AsyncMock()
    return client


@pytest.fixture
def mcp_with_tools(mock_client):
    """Create FastMCP instance with bulk transaction tools registered."""
    mcp = FastMCP("test-pocketsmith")
    register_bulk_transaction_tools(mcp, mock_client)
    return mcp, mock_client


class TestBulkUpdateTransactions:
    """Tests for bulk_update_transactions tool."""

    @pytest.mark.asyncio
    async def test_dry_run(self, mcp_with_tools):
        """Test dry run mode validates without applying."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[
                {"transaction_id": 1, "category_id": 10},
                {"transaction_id": 2, "note": "Updated"},
            ],
            dry_run=True,
        )
        data = json.loads(result)

        assert data["dry_run"] is True
        assert data["summary"]["total"] == 2
        assert data["summary"]["successful"] == 2
        assert data["summary"]["failed"] == 0
        assert data["results"][0]["status"] == "would_update"
        # Should NOT have called the API
        client.put.assert_not_called()

    @pytest.mark.asyncio
    async def test_apply_updates(self, mcp_with_tools):
        """Test applying updates to transactions."""
        mcp, client = mcp_with_tools
        client.put.return_value = {
            "id": 1,
            "payee": "Shop",
            "amount": -10.0,
            "date": "2024-01-15",
            "category": {"title": "Groceries"},
            "is_transfer": False,
        }

        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": 1, "category_id": 10}],
        )
        data = json.loads(result)

        assert data["dry_run"] is False
        assert data["summary"]["successful"] == 1
        client.put.assert_called_once_with(
            "/transactions/1",
            json_data={"category_id": 10},
        )

    @pytest.mark.asyncio
    async def test_skip_missing_transaction_id(self, mcp_with_tools):
        """Test that entries without transaction_id are skipped."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"category_id": 10}],
            dry_run=True,
        )
        data = json.loads(result)

        assert data["summary"]["skipped"] == 1
        assert data["results"][0]["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_skip_no_fields(self, mcp_with_tools):
        """Test that entries with no update fields are skipped."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": 1}],
            dry_run=True,
        )
        data = json.loads(result)

        assert data["summary"]["skipped"] == 1
        assert data["results"][0]["message"] == "No fields to update"

    @pytest.mark.asyncio
    async def test_empty_updates_raises(self, mcp_with_tools):
        """Test that empty updates list raises ValueError."""
        mcp, _client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("bulk_update_transactions")

        with pytest.raises(ValueError, match="updates list cannot be empty"):
            await tool.fn(updates=[])

    @pytest.mark.asyncio
    async def test_over_100_raises(self, mcp_with_tools):
        """Test that >100 updates raises ValueError."""
        mcp, _client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        updates = [{"transaction_id": i, "category_id": 1} for i in range(101)]

        with pytest.raises(ValueError, match="Maximum 100"):
            await tool.fn(updates=updates)

    @pytest.mark.asyncio
    async def test_partial_failure(self, mcp_with_tools):
        """Test that one failure doesn't stop other updates."""
        mcp, client = mcp_with_tools
        client.put.side_effect = [
            {"id": 1, "payee": "A", "amount": -5, "date": "2024-01-01",
             "category": None, "is_transfer": False},
            Exception("API Error"),
        ]

        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[
                {"transaction_id": 1, "category_id": 10},
                {"transaction_id": 2, "category_id": 20},
            ],
        )
        data = json.loads(result)

        assert data["summary"]["successful"] == 1
        assert data["summary"]["failed"] == 1

    @pytest.mark.asyncio
    async def test_bulk_update_success_includes_extended_fields(self, mcp_with_tools):
        """Success response must include note, needs_review, and labels fields."""
        mcp, client = mcp_with_tools
        client.put.return_value = {
            "id": 5,
            "payee": "Supermarket",
            "amount": -25.50,
            "date": "2024-03-10",
            "category": {"title": "Groceries"},
            "is_transfer": False,
            "note": "weekly shop",
            "needs_review": False,
            "labels": "food,essentials",
        }

        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": 5, "category_id": 12}],
        )
        data = json.loads(result)

        updated = data["results"][0]["updated"]
        assert updated["note"] == "weekly shop"
        assert updated["needs_review"] is False
        assert updated["labels"] == "food,essentials"

    @pytest.mark.asyncio
    async def test_bulk_update_success_includes_extended_fields_when_null(self, mcp_with_tools):
        """Extended fields are included even when the API returns null."""
        mcp, client = mcp_with_tools
        client.put.return_value = {
            "id": 6,
            "payee": "Shop",
            "amount": -10.0,
            "date": "2024-04-01",
            "category": None,
            "is_transfer": False,
            "note": None,
            "needs_review": None,
            "labels": None,
        }

        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": 6, "is_transfer": False}],
        )
        data = json.loads(result)

        updated = data["results"][0]["updated"]
        assert "note" in updated
        assert "needs_review" in updated
        assert "labels" in updated
        assert updated["note"] is None

    @pytest.mark.asyncio
    async def test_is_transfer_and_needs_review(self, mcp_with_tools):
        """Test updating is_transfer and needs_review fields."""
        mcp, client = mcp_with_tools

        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{
                "transaction_id": 1,
                "is_transfer": True,
                "needs_review": False,
            }],
            dry_run=True,
        )
        data = json.loads(result)

        assert data["results"][0]["planned_changes"] == {
            "is_transfer": True,
            "needs_review": False,
        }


class TestBulkIdValidation:
    """Tests for ID validation in bulk updates."""

    @pytest.mark.asyncio
    async def test_negative_transaction_id_skipped(self, mcp_with_tools):
        """Negative transaction_id should be skipped with error."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": -1, "category_id": 10}],
            dry_run=True,
        )
        data = json.loads(result)
        assert data["summary"]["skipped"] == 1
        assert "positive integer" in data["results"][0]["message"]

    @pytest.mark.asyncio
    async def test_zero_transaction_id_skipped(self, mcp_with_tools):
        """Zero transaction_id should be skipped with error."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": 0, "category_id": 10}],
            dry_run=True,
        )
        data = json.loads(result)
        assert data["summary"]["skipped"] == 1

    @pytest.mark.asyncio
    async def test_string_transaction_id_coerced(self, mcp_with_tools):
        """String transaction_id that's a valid int should be coerced."""
        mcp, client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": "42", "category_id": 10}],
            dry_run=True,
        )
        data = json.loads(result)
        assert data["summary"]["successful"] == 1
        assert data["results"][0]["transaction_id"] == 42

    @pytest.mark.asyncio
    async def test_non_numeric_transaction_id_skipped(self, mcp_with_tools):
        """Non-numeric transaction_id should be skipped."""
        mcp, _client = mcp_with_tools
        tool = mcp._tool_manager._tools.get("bulk_update_transactions")
        result = await tool.fn(
            updates=[{"transaction_id": "abc", "category_id": 10}],
            dry_run=True,
        )
        data = json.loads(result)
        assert data["summary"]["skipped"] == 1
        assert "Invalid transaction_id" in data["results"][0]["message"]
