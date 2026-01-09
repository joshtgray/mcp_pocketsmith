"""Token bucket rate limiter for API calls."""

import asyncio
import time


class RateLimiter:
    """
    Token bucket rate limiter with async support.

    Implements a token bucket algorithm that allows a certain number of
    requests per time interval. Tokens are refilled continuously based
    on elapsed time.
    """

    def __init__(
        self,
        tokens_per_interval: int,
        interval_seconds: float,
        initial_tokens: int | None = None,
    ):
        """
        Initialize the rate limiter.

        Args:
            tokens_per_interval: Number of tokens to add per interval
            interval_seconds: Length of the interval in seconds
            initial_tokens: Initial number of tokens (defaults to tokens_per_interval)
        """
        if tokens_per_interval <= 0:
            raise ValueError("tokens_per_interval must be positive")
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")

        self.tokens_per_interval = tokens_per_interval
        self.interval_seconds = interval_seconds
        self.tokens = float(initial_tokens if initial_tokens is not None else tokens_per_interval)
        self.max_tokens = float(tokens_per_interval)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Raises:
            ValueError: If tokens requested exceeds max_tokens
        """
        if tokens > self.max_tokens:
            raise ValueError(f"Cannot acquire {tokens} tokens (max: {self.max_tokens})")

        async with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return

            # Calculate wait time until we have enough tokens
            tokens_needed = tokens - self.tokens
            wait_time = (tokens_needed / self.tokens_per_interval) * self.interval_seconds

            await asyncio.sleep(wait_time)
            self._refill()
            self.tokens -= tokens

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without waiting.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True if tokens were acquired, False otherwise
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill

        # Calculate tokens to add based on elapsed time
        tokens_to_add = (elapsed / self.interval_seconds) * self.tokens_per_interval
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now

    @property
    def available_tokens(self) -> float:
        """Get the current number of available tokens."""
        self._refill()
        return self.tokens

    def reset(self) -> None:
        """Reset the rate limiter to full capacity."""
        self.tokens = self.max_tokens
        self.last_refill = time.monotonic()
