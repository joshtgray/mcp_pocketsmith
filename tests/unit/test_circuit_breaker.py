"""Unit tests for circuit breaker."""

import time

import pytest

from pocketsmith_mcp.client.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""

    def test_init_valid_params(self):
        """Test initialization with valid parameters."""
        cb = CircuitBreaker(
            failure_threshold=5,
            reset_timeout_seconds=60,
            half_open_max_calls=1,
        )
        assert cb.failure_threshold == 5
        assert cb.reset_timeout_seconds == 60
        assert cb.half_open_max_calls == 1
        assert cb.state == CircuitState.CLOSED

    def test_init_invalid_failure_threshold(self):
        """Test initialization fails with invalid failure_threshold."""
        with pytest.raises(ValueError, match="failure_threshold must be at least 1"):
            CircuitBreaker(failure_threshold=0)

    def test_init_invalid_reset_timeout(self):
        """Test initialization fails with invalid reset_timeout_seconds."""
        with pytest.raises(ValueError, match="reset_timeout_seconds must be positive"):
            CircuitBreaker(reset_timeout_seconds=0)

    def test_init_invalid_half_open_max_calls(self):
        """Test initialization fails with invalid half_open_max_calls."""
        with pytest.raises(ValueError, match="half_open_max_calls must be at least 1"):
            CircuitBreaker(half_open_max_calls=0)

    def test_initial_state_is_closed(self):
        """Test circuit starts in closed state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed is True
        assert cb.is_open is False

    def test_can_execute_when_closed(self):
        """Test can_execute returns True when circuit is closed."""
        cb = CircuitBreaker()
        assert cb.can_execute() is True

    def test_record_success_resets_failures(self):
        """Test record_success resets failure count."""
        cb = CircuitBreaker(failure_threshold=5)

        # Record some failures
        cb.record_failure()
        cb.record_failure()
        assert cb.failures == 2

        # Record success
        cb.record_success()
        assert cb.failures == 0

    def test_circuit_opens_after_threshold(self):
        """Test circuit opens after failure threshold is reached."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()  # Third failure - should open
        assert cb.state == CircuitState.OPEN
        assert cb.is_open is True

    def test_can_execute_when_open(self):
        """Test can_execute returns False when circuit is open."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()

        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

    def test_circuit_transitions_to_half_open(self):
        """Test circuit transitions to half-open after timeout."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout_seconds=0.1)

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for reset timeout
        time.sleep(0.15)

        # Checking state should transition to half-open
        assert cb.state == CircuitState.HALF_OPEN

    def test_can_execute_in_half_open(self):
        """Test can_execute allows limited calls in half-open state."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout_seconds=0.1, half_open_max_calls=2)

        cb.record_failure()
        time.sleep(0.15)

        # First call should be allowed
        assert cb.can_execute() is True
        # Second call should be allowed
        assert cb.can_execute() is True
        # Third call should be blocked
        assert cb.can_execute() is False

    def test_success_in_half_open_closes_circuit(self):
        """Test success in half-open state closes the circuit."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout_seconds=0.1)

        cb.record_failure()
        time.sleep(0.15)

        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_failure_in_half_open_reopens_circuit(self):
        """Test failure in half-open state reopens the circuit."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout_seconds=0.1)

        cb.record_failure()
        time.sleep(0.15)

        assert cb.state == CircuitState.HALF_OPEN

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_reset(self):
        """Test reset returns circuit to initial state."""
        cb = CircuitBreaker(failure_threshold=1)

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failures == 0

    def test_force_open(self):
        """Test force_open opens the circuit immediately."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

        cb.force_open()
        assert cb.state == CircuitState.OPEN

    def test_get_stats(self):
        """Test get_stats returns correct statistics."""
        cb = CircuitBreaker(failure_threshold=5, reset_timeout_seconds=60)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()

        stats = cb.get_stats()

        assert stats["state"] == "closed"
        assert stats["failures"] == 0  # Reset by success
        assert stats["successes"] == 1
        assert stats["failure_threshold"] == 5
        assert stats["reset_timeout_seconds"] == 60
