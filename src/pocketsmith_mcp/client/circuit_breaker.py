"""Circuit breaker pattern for fault tolerance."""

import time
from enum import Enum
from threading import Lock
from typing import Any

from pocketsmith_mcp.logger import get_logger

logger = get_logger("circuit_breaker")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking all calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for external service calls.

    Implements the circuit breaker pattern to prevent cascading failures
    when an external service is unhealthy.

    States:
    - CLOSED: Normal operation, all calls pass through
    - OPEN: Service is unhealthy, all calls fail immediately
    - HALF_OPEN: Testing if service recovered, limited calls allowed
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout_seconds: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            reset_timeout_seconds: Time to wait before testing recovery
            half_open_max_calls: Number of test calls allowed in half-open state
        """
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if reset_timeout_seconds <= 0:
            raise ValueError("reset_timeout_seconds must be positive")
        if half_open_max_calls < 1:
            raise ValueError("half_open_max_calls must be at least 1")

        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = reset_timeout_seconds
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failures = 0
        self._successes = 0
        self._last_failure_time: float = 0.0
        self._half_open_calls = 0
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        """Get the current circuit state."""
        with self._lock:
            self._check_state_transition()
            return self._state

    @property
    def failures(self) -> int:
        """Get the current failure count."""
        return self._failures

    @property
    def is_closed(self) -> bool:
        """Check if the circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if the circuit is open (blocking calls)."""
        return self.state == CircuitState.OPEN

    def can_execute(self) -> bool:
        """
        Check if the circuit allows execution.

        Returns:
            True if a call can be made, False if blocked
        """
        with self._lock:
            self._check_state_transition()

            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                return False

            # HALF_OPEN: Allow limited test calls
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            self._successes += 1

            if self._state == CircuitState.HALF_OPEN:
                # Service recovered, close the circuit
                logger.info("Circuit breaker: Service recovered, closing circuit")
                self._state = CircuitState.CLOSED

            # Reset failure count on success
            self._failures = 0
            self._half_open_calls = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self._failures += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                # Test call failed, reopen circuit
                logger.warning("Circuit breaker: Test call failed, reopening circuit")
                self._state = CircuitState.OPEN
                return

            if self._failures >= self.failure_threshold:
                # Too many failures, open circuit
                logger.warning(
                    f"Circuit breaker: {self._failures} failures reached threshold, "
                    f"opening circuit for {self.reset_timeout_seconds}s"
                )
                self._state = CircuitState.OPEN

    def _check_state_transition(self) -> None:
        """Check if state should transition based on timeout."""
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self.reset_timeout_seconds:
                logger.info("Circuit breaker: Reset timeout elapsed, entering half-open state")
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0

    def reset(self) -> None:
        """Reset the circuit breaker to initial state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failures = 0
            self._successes = 0
            self._last_failure_time = 0.0
            self._half_open_calls = 0
            logger.info("Circuit breaker: Reset to closed state")

    def force_open(self) -> None:
        """Force the circuit to open state."""
        with self._lock:
            self._state = CircuitState.OPEN
            self._last_failure_time = time.monotonic()
            logger.warning("Circuit breaker: Forced to open state")

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                "state": self._state.value,
                "failures": self._failures,
                "successes": self._successes,
                "failure_threshold": self.failure_threshold,
                "reset_timeout_seconds": self.reset_timeout_seconds,
            }
