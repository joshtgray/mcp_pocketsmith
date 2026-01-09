"""Entry point for pocketsmith-mcp server.

This module allows running the server as:
    python -m pocketsmith_mcp
    uvx pocketsmith-mcp
    uv run pocketsmith-mcp
"""

from pocketsmith_mcp.server import get_server


def main() -> None:
    """Run the PocketSmith MCP server."""
    server = get_server()
    server.run()


if __name__ == "__main__":
    main()
