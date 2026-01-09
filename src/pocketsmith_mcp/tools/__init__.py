"""MCP tool registration for PocketSmith API."""

from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.tools.accounts import register_account_tools
from pocketsmith_mcp.tools.attachments import register_attachment_tools
from pocketsmith_mcp.tools.budgeting import register_budgeting_tools
from pocketsmith_mcp.tools.categories import register_category_tools
from pocketsmith_mcp.tools.events import register_event_tools
from pocketsmith_mcp.tools.institutions import register_institution_tools
from pocketsmith_mcp.tools.labels import register_label_tools
from pocketsmith_mcp.tools.transaction_accounts import register_transaction_account_tools
from pocketsmith_mcp.tools.transactions import register_transaction_tools
from pocketsmith_mcp.tools.users import register_user_tools
from pocketsmith_mcp.tools.utilities import register_utility_tools


def register_all_tools(mcp: FastMCP, client: PocketSmithClient) -> None:
    """
    Register all MCP tools with the server.

    Args:
        mcp: FastMCP server instance
        client: PocketSmith API client
    """
    register_user_tools(mcp, client)  # 3 tools
    register_account_tools(mcp, client)  # 4 tools
    register_transaction_account_tools(mcp, client)  # 3 tools
    register_transaction_tools(mcp, client)  # 5 tools
    register_category_tools(mcp, client)  # 5 tools
    register_budgeting_tools(mcp, client)  # 4 tools
    register_institution_tools(mcp, client)  # 5 tools
    register_event_tools(mcp, client)  # 5 tools
    register_attachment_tools(mcp, client)  # 5 tools
    register_label_tools(mcp, client)  # 2 tools
    register_utility_tools(mcp, client)  # 2 tools


__all__ = ["register_all_tools"]
