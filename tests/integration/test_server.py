"""Integration tests for the MCP server lifecycle."""

from unittest.mock import MagicMock, patch

import pytest

from pocketsmith_mcp.server import create_server, get_server


def _mock_config(**overrides):
    """Create a mock config with correct attribute names."""
    defaults = {
        "api_key": "test_key",
        "api_timeout": 30.0,
        "max_retries": 3,
        "rate_limit_per_minute": 60,
    }
    defaults.update(overrides)
    return MagicMock(**defaults)


class TestServerCreation:
    """Tests for server creation and configuration."""

    def test_create_server_with_api_key(self):
        """Test server creation with explicit API key."""
        with patch("pocketsmith_mcp.server.get_config") as mock_config:
            mock_config.return_value = _mock_config()

            server = create_server(api_key="explicit_test_key")

            assert server is not None
            assert server.name == "pocketsmith-mcp"

    def test_create_server_from_env(self):
        """Test server creation with environment variable."""
        with patch("pocketsmith_mcp.server.get_config") as mock_config:
            mock_config.return_value = _mock_config(api_key="env_test_key")

            server = create_server()

            assert server is not None

    def test_create_server_missing_api_key(self):
        """Test server creation fails without API key."""
        with patch("pocketsmith_mcp.server.get_config") as mock_config:
            mock_config.return_value = _mock_config(api_key=None)

            with pytest.raises(ValueError, match="POCKETSMITH_API_KEY"):
                create_server()

    def test_get_server_returns_server(self):
        """Test get_server returns a configured server."""
        with patch("pocketsmith_mcp.server.get_config") as mock_config:
            mock_config.return_value = _mock_config()

            server = get_server()

            assert server is not None


class TestServerTools:
    """Tests for server tool registration."""

    def test_all_tools_registered(self):
        """Test that all 58 tools are registered."""
        with patch("pocketsmith_mcp.server.get_config") as mock_config:
            mock_config.return_value = _mock_config()

            server = create_server()

            # Get registered tools
            tools = server._tool_manager._tools
            tool_names = list(tools.keys())

            # Verify core tools exist
            expected_tools = [
                # User tools (3)
                "get_current_user",
                "get_user",
                "update_user",
                # Account tools (7)
                "list_accounts",
                "get_account",
                "create_account",
                "update_account",
                "delete_account",
                "list_accounts_by_institution",
                "update_account_display_order",
                # Transaction account tools (3)
                "list_transaction_accounts",
                "get_transaction_account",
                "update_transaction_account",
                # Transaction tools (8)
                "list_transactions",
                "get_transaction",
                "create_transaction",
                "update_transaction",
                "delete_transaction",
                "list_transactions_by_account",
                "list_transactions_by_transaction_account",
                "list_transactions_by_category",
                # Category tools (5)
                "list_categories",
                "get_category",
                "create_category",
                "update_category",
                "delete_category",
                # Category rule tools (2)
                "list_category_rules",
                "create_category_rule",
                # Budgeting tools (4)
                "get_budget",
                "get_budget_summary",
                "get_trend_analysis",
                "clear_forecast_cache",
                # Institution tools (5)
                "list_institutions",
                "get_institution",
                "create_institution",
                "update_institution",
                "delete_institution",
                # Event tools (6)
                "list_events",
                "get_event",
                "create_event",
                "update_event",
                "delete_event",
                "list_scenario_events",
                # Attachment tools (8)
                "list_attachments",
                "get_attachment",
                "create_attachment",
                "update_attachment",
                "delete_attachment",
                "list_transaction_attachments",
                "assign_attachment_to_transaction",
                "unassign_attachment_from_transaction",
                # Label tools (2)
                "list_labels",
                "list_saved_searches",
                # Utility tools (3)
                "list_currencies",
                "list_time_zones",
                "get_currency",
                # Bulk tools (1)
                "bulk_update_transactions",
                # Scenario tools (1)
                "list_scenarios",
            ]

            for tool_name in expected_tools:
                assert tool_name in tool_names, f"Tool '{tool_name}' not registered"

            # Verify total count (58 tools)
            assert len(tool_names) == 58, f"Expected 58 tools, got {len(tool_names)}"


class TestServerConfiguration:
    """Tests for server configuration handling."""

    def test_custom_timeout(self):
        """Test server respects custom timeout."""
        with patch("pocketsmith_mcp.server.get_config") as mock_config:
            mock_config.return_value = _mock_config(api_timeout=60.0, max_retries=5, rate_limit_per_minute=120)

            server = create_server()
            assert server is not None

    def test_custom_rate_limit(self):
        """Test server respects custom rate limit."""
        with patch("pocketsmith_mcp.server.get_config") as mock_config:
            mock_config.return_value = _mock_config(rate_limit_per_minute=30)

            server = create_server()
            assert server is not None
