"""PocketSmith MCP Server - Production-ready MCP server for PocketSmith API."""

__version__ = "1.0.0"
__author__ = "PocketSmith MCP"

from pocketsmith_mcp.server import create_server

__all__ = ["create_server", "__version__"]
