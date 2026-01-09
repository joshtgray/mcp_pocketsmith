"""Unit tests for rate limiter."""

import asyncio
import time

import pytest

from pocketsmith_mcp.client.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests for the RateLimiter class."""

    def test_init_valid_params(self):
        """Test initialization with valid parameters."""
        limiter = RateLimiter(tokens_per_interval=10, interval_seconds=60)
        assert limiter.tokens_per_interval == 10
        assert limiter.interval_seconds == 60
        assert limiter.tokens == 10.0
        assert limiter.max_tokens == 10.0

    def test_init_custom_initial_tokens(self):
        """Test initialization with custom initial tokens."""
        limiter = RateLimiter(tokens_per_interval=10, interval_seconds=60, initial_tokens=5)
        assert limiter.tokens == 5.0

    def test_init_invalid_tokens_per_interval(self):
        """Test initialization fails with invalid tokens_per_interval."""
        with pytest.raises(ValueError, match="tokens_per_interval must be positive"):
            RateLimiter(tokens_per_interval=0, interval_seconds=60)

        with pytest.raises(ValueError, match="tokens_per_interval must be positive"):
            RateLimiter(tokens_per_interval=-1, interval_seconds=60)

    def test_init_invalid_interval_seconds(self):
        """Test initialization fails with invalid interval_seconds."""
        with pytest.raises(ValueError, match="interval_seconds must be positive"):
            RateLimiter(tokens_per_interval=10, interval_seconds=0)

        with pytest.raises(ValueError, match="interval_seconds must be positive"):
            RateLimiter(tokens_per_interval=10, interval_seconds=-1)

    @pytest.mark.asyncio
    async def test_acquire_success(self):
        """Test successful token acquisition."""
        limiter = RateLimiter(tokens_per_interval=10, interval_seconds=60)

        await limiter.acquire()
        assert limiter.tokens == pytest.approx(9.0, abs=0.1)

        await limiter.acquire()
        assert limiter.tokens == pytest.approx(8.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens at once."""
        limiter = RateLimiter(tokens_per_interval=10, interval_seconds=60)

        await limiter.acquire(tokens=5)
        assert limiter.tokens == 5.0

    @pytest.mark.asyncio
    async def test_acquire_exceeds_max(self):
        """Test acquiring more tokens than max fails."""
        limiter = RateLimiter(tokens_per_interval=10, interval_seconds=60)

        with pytest.raises(ValueError, match="Cannot acquire 11 tokens"):
            await limiter.acquire(tokens=11)

    def test_try_acquire_success(self):
        """Test try_acquire returns True when tokens available."""
        limiter = RateLimiter(tokens_per_interval=10, interval_seconds=60)

        assert limiter.try_acquire() is True
        assert limiter.tokens == 9.0

    def test_try_acquire_failure(self):
        """Test try_acquire returns False when no tokens available."""
        limiter = RateLimiter(tokens_per_interval=1, interval_seconds=60, initial_tokens=0)

        assert limiter.try_acquire() is False

    def test_available_tokens(self):
        """Test available_tokens property."""
        limiter = RateLimiter(tokens_per_interval=10, interval_seconds=60)

        assert limiter.available_tokens == pytest.approx(10.0, abs=0.1)

        limiter.try_acquire()
        assert limiter.available_tokens == pytest.approx(9.0, abs=0.1)

    def test_reset(self):
        """Test reset restores full capacity."""
        limiter = RateLimiter(tokens_per_interval=10, interval_seconds=60)

        # Use some tokens
        limiter.try_acquire()
        limiter.try_acquire()
        assert limiter.tokens == pytest.approx(8.0, abs=0.1)

        # Reset
        limiter.reset()
        assert limiter.tokens == pytest.approx(10.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test tokens refill over time."""
        limiter = RateLimiter(
            tokens_per_interval=10,
            interval_seconds=1,  # 10 tokens per second
            initial_tokens=0,
        )

        # Wait a bit for tokens to refill
        await asyncio.sleep(0.5)

        # Should have approximately 5 tokens after 0.5 seconds
        available = limiter.available_tokens
        assert 4 <= available <= 6  # Allow some timing variance

    @pytest.mark.asyncio
    async def test_acquire_waits_when_empty(self):
        """Test acquire waits when tokens are depleted."""
        limiter = RateLimiter(
            tokens_per_interval=10,
            interval_seconds=1,  # Fast refill for testing
            initial_tokens=0,
        )

        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # Should have waited for token to refill
        assert elapsed >= 0.05  # At least some wait time
