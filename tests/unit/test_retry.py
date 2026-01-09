"""Unit tests for retry logic."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pocketsmith_mcp.client.retry import calculate_delay, retry_with_backoff


class TestRetryWithBackoff:
    """Tests for the retry_with_backoff function."""

    @pytest.mark.asyncio
    async def test_success_first_attempt(self):
        """Test function succeeds on first attempt."""
        mock_func = AsyncMock(return_value="success")

        result = await retry_with_backoff(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """Test function succeeds after one retry."""
        mock_func = AsyncMock(side_effect=[ValueError("fail"), "success"])

        result = await retry_with_backoff(
            mock_func,
            max_attempts=3,
            base_delay=0.01,  # Fast for testing
        )

        assert result == "success"
        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_all_attempts_fail(self):
        """Test function raises last error when all attempts fail."""
        mock_func = AsyncMock(side_effect=ValueError("always fails"))

        with pytest.raises(ValueError, match="always fails"):
            await retry_with_backoff(
                mock_func,
                max_attempts=3,
                base_delay=0.01,
            )

        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_non_retryable_error(self):
        """Test non-retryable errors are raised immediately."""
        mock_func = AsyncMock(side_effect=KeyError("not retryable"))

        with pytest.raises(KeyError):
            await retry_with_backoff(
                mock_func,
                max_attempts=3,
                base_delay=0.01,
                retryable_errors=(ValueError,),  # Only retry ValueError
            )

        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_on_retry_callback(self):
        """Test on_retry callback is called on each retry."""
        mock_func = AsyncMock(side_effect=[ValueError("fail1"), ValueError("fail2"), "success"])
        on_retry = MagicMock()

        result = await retry_with_backoff(
            mock_func,
            max_attempts=3,
            base_delay=0.01,
            on_retry=on_retry,
        )

        assert result == "success"
        assert on_retry.call_count == 2

    @pytest.mark.asyncio
    async def test_invalid_max_attempts(self):
        """Test invalid max_attempts raises ValueError."""
        with pytest.raises(ValueError, match="max_attempts must be at least 1"):
            await retry_with_backoff(AsyncMock(), max_attempts=0)

    @pytest.mark.asyncio
    async def test_invalid_base_delay(self):
        """Test invalid base_delay raises ValueError."""
        with pytest.raises(ValueError, match="base_delay must be positive"):
            await retry_with_backoff(AsyncMock(), base_delay=0)

        with pytest.raises(ValueError, match="base_delay must be positive"):
            await retry_with_backoff(AsyncMock(), base_delay=-1)

    @pytest.mark.asyncio
    async def test_invalid_max_delay(self):
        """Test invalid max_delay raises ValueError."""
        with pytest.raises(ValueError, match="max_delay must be positive"):
            await retry_with_backoff(AsyncMock(), max_delay=0)

    @pytest.mark.asyncio
    async def test_invalid_jitter_factor(self):
        """Test invalid jitter_factor raises ValueError."""
        with pytest.raises(ValueError, match="jitter_factor must be between 0 and 1"):
            await retry_with_backoff(AsyncMock(), jitter_factor=-0.1)

        with pytest.raises(ValueError, match="jitter_factor must be between 0 and 1"):
            await retry_with_backoff(AsyncMock(), jitter_factor=1.5)


class TestCalculateDelay:
    """Tests for the calculate_delay function."""

    def test_first_attempt(self):
        """Test delay calculation for first attempt."""
        delay = calculate_delay(attempt=1, base_delay=1.0, max_delay=30.0, jitter_factor=0)
        assert delay == 1.0

    def test_second_attempt(self):
        """Test delay calculation for second attempt (doubles)."""
        delay = calculate_delay(attempt=2, base_delay=1.0, max_delay=30.0, jitter_factor=0)
        assert delay == 2.0

    def test_third_attempt(self):
        """Test delay calculation for third attempt (quadruples)."""
        delay = calculate_delay(attempt=3, base_delay=1.0, max_delay=30.0, jitter_factor=0)
        assert delay == 4.0

    def test_max_delay_cap(self):
        """Test delay is capped at max_delay."""
        delay = calculate_delay(attempt=10, base_delay=1.0, max_delay=30.0, jitter_factor=0)
        assert delay == 30.0

    def test_jitter_adds_randomness(self):
        """Test jitter adds randomness to delay."""
        delays = [
            calculate_delay(attempt=1, base_delay=1.0, max_delay=30.0, jitter_factor=0.2)
            for _ in range(10)
        ]

        # With jitter, delays should vary
        assert len(set(delays)) > 1

        # All delays should be within expected range (1.0 to 1.2)
        for delay in delays:
            assert 1.0 <= delay <= 1.2
