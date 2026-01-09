"""Logging configuration for PocketSmith MCP Server.

All logging goes to stderr to avoid interfering with the MCP protocol on stdout.
"""

import logging
import os
import sys


def setup_logger(
    name: str = "pocketsmith_mcp",
    level: str | None = None,
) -> logging.Logger:
    """
    Set up a logger that writes to stderr.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Defaults to DEBUG if DEBUG env var is set, else INFO

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Determine log level
    if level is None:
        debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        level = "DEBUG" if debug_mode else "INFO"

    logger.setLevel(getattr(logging, level.upper()))

    # Create stderr handler (MCP protocol uses stdout, so we must use stderr)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(getattr(logging, level.upper()))

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


# Default logger instance
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the given name.

    Args:
        name: Logger name (will be prefixed with 'pocketsmith_mcp.')

    Returns:
        Logger instance
    """
    return logging.getLogger(f"pocketsmith_mcp.{name}")
