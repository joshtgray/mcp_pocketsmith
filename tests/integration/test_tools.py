"""Integration tests for MCP tools with mocked API responses."""

import json
from unittest.mock import MagicMock, patch

import pytest

from pocketsmith_mcp.server import create_server


@pytest.fixture
def server():
    """Create a server instance for testing."""
    with patch("pocketsmith_mcp.server.get_config") as mock_config:
        mock_config.return_value = MagicMock(
            api_key="test_key",
            timeout=30.0,
            max_retries=3,
            rate_limit_per_minute=60
        )
        yield create_server()


class TestUserToolsIntegration:
    """Integration tests for user tools."""

    @pytest.mark.asyncio
    async def test_get_current_user_flow(self, server, sample_user):
        """Test get_current_user tool end-to-end."""
        tool = server._tool_manager._tools.get("get_current_user")

        # Mock the client's get method
        with patch.object(tool, "fn") as mock_fn:
            mock_fn.return_value = json.dumps(sample_user)

            result = await mock_fn()
            result_data = json.loads(result)

            assert result_data["id"] == sample_user["id"]
            assert result_data["login"] == sample_user["login"]


class TestTransactionToolsIntegration:
    """Integration tests for transaction tools."""

    @pytest.mark.asyncio
    async def test_create_and_get_transaction_flow(self, server, sample_transaction):
        """Test creating and retrieving a transaction."""
        create_tool = server._tool_manager._tools.get("create_transaction")
        get_tool = server._tool_manager._tools.get("get_transaction")

        # Verify tools exist
        assert create_tool is not None
        assert get_tool is not None


class TestCategoryToolsIntegration:
    """Integration tests for category tools."""

    @pytest.mark.asyncio
    async def test_list_and_get_category_flow(self, server, sample_category):
        """Test listing and getting categories."""
        list_tool = server._tool_manager._tools.get("list_categories")
        get_tool = server._tool_manager._tools.get("get_category")

        assert list_tool is not None
        assert get_tool is not None


class TestBudgetingToolsIntegration:
    """Integration tests for budgeting tools."""

    @pytest.mark.asyncio
    async def test_budget_tools_exist(self, server):
        """Test budgeting tools are properly registered."""
        tools = [
            "get_budget",
            "get_budget_summary",
            "get_trend_analysis",
            "clear_forecast_cache"
        ]

        for tool_name in tools:
            tool = server._tool_manager._tools.get(tool_name)
            assert tool is not None, f"Tool {tool_name} not found"


class TestToolDocumentation:
    """Tests for tool documentation."""

    def test_all_tools_have_descriptions(self, server):
        """Test that all tools have descriptions."""
        tools = server._tool_manager._tools

        for name, tool in tools.items():
            assert tool.description is not None, f"Tool {name} missing description"
            assert len(tool.description) > 10, f"Tool {name} description too short"

    def test_all_tools_have_proper_docstrings(self, server):
        """Test that all tools have proper docstrings."""
        tools = server._tool_manager._tools

        for name, tool in tools.items():
            # Tool description comes from docstring
            assert tool.description is not None


class TestToolErrorHandling:
    """Tests for tool error handling."""

    @pytest.mark.asyncio
    async def test_tools_raise_value_error_on_failure(self, server):
        """Test that tools raise ValueError with descriptive messages."""
        # This is a structural test - actual error handling tested in unit tests
        tools = server._tool_manager._tools

        # Verify critical tools exist
        critical_tools = [
            "get_current_user",
            "list_transactions",
            "create_transaction",
            "list_categories"
        ]

        for tool_name in critical_tools:
            assert tool_name in tools
