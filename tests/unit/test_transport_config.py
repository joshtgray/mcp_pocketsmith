"""Tests for HTTP/SSE transport configuration."""

import os
from unittest.mock import ANY, MagicMock, patch

import pytest

from pocketsmith_mcp.config import Config, reset_config


class TestTransportConfig:
    """Test transport-related configuration fields."""

    def setup_method(self) -> None:
        reset_config()

    def test_config_defaults_transport_stdio(self) -> None:
        """Default transport should be stdio for backward compatibility."""
        config = Config.from_env()
        assert config.transport == "stdio"

    def test_config_defaults_host(self) -> None:
        """Default host should be 127.0.0.1."""
        config = Config.from_env()
        assert config.host == "127.0.0.1"

    def test_config_defaults_port(self) -> None:
        """Default port should be 8000."""
        config = Config.from_env()
        assert config.port == 8000

    def test_config_transport_from_env(self) -> None:
        """Transport should be configurable via MCP_TRANSPORT env var."""
        with patch.dict(os.environ, {"MCP_TRANSPORT": "sse"}):
            reset_config()
            config = Config.from_env()
            assert config.transport == "sse"

    def test_config_host_from_env(self) -> None:
        """Host should be configurable via MCP_HOST env var."""
        with patch.dict(os.environ, {"MCP_HOST": "0.0.0.0"}):
            reset_config()
            config = Config.from_env()
            assert config.host == "0.0.0.0"

    def test_config_port_from_env(self) -> None:
        """Port should be configurable via MCP_PORT env var."""
        with patch.dict(os.environ, {"MCP_PORT": "3401"}):
            reset_config()
            config = Config.from_env()
            assert config.port == 3401

    def test_config_invalid_transport_rejected(self) -> None:
        """Invalid transport values should raise ConfigurationError."""
        with patch.dict(os.environ, {"MCP_TRANSPORT": "websocket"}):
            reset_config()
            config = Config.from_env()
            with pytest.raises(Exception):
                config.validate()

    def test_config_invalid_port_rejected(self) -> None:
        """Non-positive port should raise ConfigurationError."""
        with patch.dict(os.environ, {"MCP_PORT": "0"}):
            reset_config()
            config = Config.from_env()
            with pytest.raises(Exception):
                config.validate()


class TestServerCreation:
    """Test that create_server passes transport config to FastMCP."""

    def setup_method(self) -> None:
        reset_config()

    def test_create_server_returns_fastmcp(self) -> None:
        """create_server() should still return a FastMCP instance."""
        from mcp.server.fastmcp import FastMCP

        from pocketsmith_mcp.server import create_server

        server = create_server()
        assert isinstance(server, FastMCP)

    @patch("pocketsmith_mcp.server.FastMCP")
    @patch("pocketsmith_mcp.server.PocketSmithClient")
    def test_create_server_passes_host_port(
        self, mock_client: MagicMock, mock_fastmcp: MagicMock
    ) -> None:
        """create_server should pass host and port from config to FastMCP."""
        with patch.dict(os.environ, {"MCP_HOST": "0.0.0.0", "MCP_PORT": "3401"}):
            reset_config()
            from pocketsmith_mcp.server import create_server

            create_server()
            mock_fastmcp.assert_called_once_with(
                "pocketsmith-mcp",
                lifespan=ANY,
                host="0.0.0.0",
                port=3401,
            )


class TestMainEntryPoint:
    """Test that __main__.py passes transport to server.run()."""

    def setup_method(self) -> None:
        reset_config()

    @patch("pocketsmith_mcp.__main__.get_server")
    def test_main_passes_transport_to_run(self, mock_get_server: MagicMock) -> None:
        """main() should pass MCP_TRANSPORT value to server.run()."""
        mock_server = mock_get_server.return_value
        with patch.dict(os.environ, {"MCP_TRANSPORT": "sse"}):
            reset_config()
            from pocketsmith_mcp.__main__ import main

            main()
            mock_server.run.assert_called_once_with(transport="sse")

    @patch("pocketsmith_mcp.__main__.get_server")
    def test_main_defaults_to_stdio(self, mock_get_server: MagicMock) -> None:
        """main() should default to stdio transport."""
        mock_server = mock_get_server.return_value
        with patch.dict(os.environ, {}, clear=False):
            # Ensure MCP_TRANSPORT is not set
            os.environ.pop("MCP_TRANSPORT", None)
            reset_config()
            from pocketsmith_mcp.__main__ import main

            main()
            mock_server.run.assert_called_once_with(transport="stdio")
