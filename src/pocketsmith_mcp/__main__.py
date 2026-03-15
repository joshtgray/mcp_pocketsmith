"""Entry point for pocketsmith-mcp server.

This module allows running the server as:
    python -m pocketsmith_mcp
    uvx pocketsmith-mcp
    uv run pocketsmith-mcp
"""

import os
from typing import Literal, cast

from pocketsmith_mcp.server import get_server

TransportType = Literal["stdio", "sse", "streamable-http"]


def main() -> None:
    """Run the PocketSmith MCP server."""
    transport = cast(TransportType, os.getenv("MCP_TRANSPORT", "stdio"))
    server = get_server()
    server.run(transport=transport)


if __name__ == "__main__":
    main()
