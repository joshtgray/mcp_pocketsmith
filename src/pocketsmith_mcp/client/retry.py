"""Exponential backoff retry with jitter."""

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from pocketsmith_mcp.logger import get_logger

T = TypeVar("T")
logger = get_logger("retry")


async def retry_with_backoff(
    func: Callable[[], Awaitable[T]],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter_factor: float = 0.2,
    retryable_errors: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int], None] | None = None,
) -> T:
    """
    Retry an async function with exponential backoff and jitter.

    Args:
        func: Async function to retry (no arguments)
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 30.0)
        jitter_factor: Jitter factor (0.0-1.0) to randomize delay (default: 0.2)
        retryable_errors: Tuple of exception types to retry (default: all)
        on_retry: Optional callback called on each retry with (exception, attempt)

    Returns:
        Result of the function

    Raises:
        The last exception if all retries fail
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if base_delay <= 0:
        raise ValueError("base_delay must be positive")
    if max_delay <= 0:
        raise ValueError("max_delay must be positive")
    if not 0 <= jitter_factor <= 1:
        raise ValueError("jitter_factor must be between 0 and 1")

    last_error: Exception = Exception("No attempts made")

    for attempt in range(1, max_attempts + 1):
        try:
            return await func()
        except retryable_errors as e:
            last_error = e

            if attempt == max_attempts:
                logger.warning(
                    f"All {max_attempts} attempts failed. Last error: {e}"
                )
                break

            # Calculate delay with exponential backoff
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)

            # Add jitter
            jitter = delay * jitter_factor * random.random()
            total_delay = delay + jitter

            logger.info(
                f"Attempt {attempt}/{max_attempts} failed: {e}. "
                f"Retrying in {total_delay:.2f}s"
            )

            if on_retry:
                on_retry(e, attempt)

            await asyncio.sleep(total_delay)

    raise last_error


def calculate_delay(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter_factor: float = 0.2,
) -> float:
    """
    Calculate delay for a given attempt number.

    Args:
        attempt: Current attempt number (1-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter_factor: Jitter factor (0.0-1.0)

    Returns:
        Calculated delay in seconds
    """
    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
    rand_val: float = random.random()
    jitter = delay * jitter_factor * rand_val
    total_delay: float = delay + jitter
    return total_delay
