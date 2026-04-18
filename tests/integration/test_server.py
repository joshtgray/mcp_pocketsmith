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
        """Test that all 44 tools are registered."""
        with patch("pocketsmith_mcp.server.get_config") as mock_config:
            mock_config.return_value = _mock_config()

            server = create_server()

            # Get registered tools
            tools = server._tool_manager._tools
            tool_names = list(tools.keys())

            # Verify core tools exist
            expected_tools = [
                # User tools
                "get_current_user",
                "get_user",
                "update_user",
                # Account tools
                "list_accounts",
                "get_account",
                "update_account",
                "delete_account",
                # Transaction account tools
                "list_transaction_accounts",
                "get_transaction_account",
                "update_transaction_account",
                # Transaction tools
                "list_transactions",
                "get_transaction",
                "create_transaction",
                "update_transaction",
                "delete_transaction",
                # Category tools
                "list_categories",
                "get_category",
                "create_category",
                "update_category",
                "delete_category",
                # Budgeting tools
                "get_budget",
                "get_budget_summary",
                "get_trend_analysis",
                "clear_forecast_cache",
                # Institution tools
                "list_institutions",
                "get_institution",
                "create_institution",
                "update_institution",
                "delete_institution",
                # Event tools
                "list_events",
                "get_event",
                "create_event",
                "update_event",
                "delete_event",
                # Attachment tools
                "list_attachments",
                "get_attachment",
                "create_attachment",
                "update_attachment",
                "delete_attachment",
                # Label tools
                "list_labels",
                "list_saved_searches",
                # Utility tools
                "list_currencies",
                "list_time_zones",
                # Bulk tools
                "bulk_update_transactions",
                # Scenario tools
                "list_scenarios",
            ]

            for tool_name in expected_tools:
                assert tool_name in tool_names, f"Tool '{tool_name}' not registered"

            # Verify total count (45 tools)
            assert len(tool_names) == 45, f"Expected 45 tools, got {len(tool_names)}"


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
