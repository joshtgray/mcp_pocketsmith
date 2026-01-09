"""Configuration management for PocketSmith MCP Server."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from pocketsmith_mcp.errors import ConfigurationError


@dataclass
class Config:
    """Server configuration loaded from environment variables."""

    # Required
    api_key: str

    # Optional with defaults
    debug: bool = False
    api_timeout: float = 30.0
    max_retries: int = 3
    rate_limit_per_minute: int = 60

    # API settings
    base_url: str = "https://api.pocketsmith.com/v2"

    @classmethod
    def from_env(cls, env_file: str | None = None) -> "Config":
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional path to .env file

        Returns:
            Config instance

        Raises:
            ConfigurationError: If required configuration is missing
        """
        # Load .env file if it exists
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Get API key (required)
        api_key = os.getenv("POCKETSMITH_API_KEY")
        if not api_key:
            raise ConfigurationError(
                "POCKETSMITH_API_KEY environment variable is required. "
                "Get your API key from https://my.pocketsmith.com/settings/security"
            )

        # Validate API key format (basic check)
        if len(api_key) < 10:
            raise ConfigurationError(
                "POCKETSMITH_API_KEY appears to be invalid (too short)"
            )

        return cls(
            api_key=api_key,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            api_timeout=float(os.getenv("API_TIMEOUT", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
        )

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ConfigurationError: If any configuration is invalid
        """
        if self.api_timeout <= 0:
            raise ConfigurationError("API_TIMEOUT must be positive")

        if self.max_retries < 0:
            raise ConfigurationError("MAX_RETRIES must be non-negative")

        if self.rate_limit_per_minute <= 0:
            raise ConfigurationError("RATE_LIMIT_PER_MINUTE must be positive")


# Global config instance (lazy loaded)
_config: Config | None = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance

    Raises:
        ConfigurationError: If configuration is invalid
    """
    global _config
    if _config is None:
        _config = Config.from_env()
        _config.validate()
    return _config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None
