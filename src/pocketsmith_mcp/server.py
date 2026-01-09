"""FastMCP server creation and configuration for PocketSmith."""


from mcp.server.fastmcp import FastMCP

from pocketsmith_mcp.client.api_client import PocketSmithClient
from pocketsmith_mcp.config import get_config
from pocketsmith_mcp.logger import get_logger
from pocketsmith_mcp.tools import register_all_tools

logger = get_logger("server")


def create_server(api_key: str | None = None) -> FastMCP:
    """
    Create and configure the PocketSmith MCP server.

    Args:
        api_key: Optional API key override. If not provided,
                 loads from POCKETSMITH_API_KEY environment variable.

    Returns:
        Configured FastMCP server instance with all tools registered.

    Raises:
        ValueError: If no API key is provided or found in environment.
    """
    # Load configuration
    config = get_config()

    # Use provided API key or fall back to config
    key = api_key or config.api_key
    if not key:
        raise ValueError(
            "POCKETSMITH_API_KEY environment variable required. "
            "Set it in your environment or .env file."
        )

    logger.info("Creating PocketSmith MCP server")

    # Create FastMCP server
    mcp = FastMCP("pocketsmith-mcp")

    # Initialize API client with configuration
    client = PocketSmithClient(
        api_key=key,
        timeout=config.api_timeout,
        max_retries=config.max_retries,
        rate_limit_per_minute=config.rate_limit_per_minute,
    )

    # Register all tools
    register_all_tools(mcp, client)

    logger.info("PocketSmith MCP server created successfully")

    return mcp


def get_server() -> FastMCP:
    """
    Get or create the PocketSmith MCP server singleton.

    This is the main entry point for running the server.

    Returns:
        Configured FastMCP server instance.
    """
    return create_server()
