"""Custom exceptions for PocketSmith MCP Server."""



class PocketSmithError(Exception):
    """Base exception for all PocketSmith MCP errors."""

    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class APIError(PocketSmithError):
    """Exception raised for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        response_body: str | None = None,
    ):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message, response_body)

    def __str__(self) -> str:
        base = f"[HTTP {self.status_code}] {self.message}"
        if self.response_body:
            return f"{base}: {self.response_body}"
        return base


class AuthError(PocketSmithError):
    """Exception raised for authentication errors (401)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class RateLimitError(PocketSmithError):
    """Exception raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ):
        self.retry_after = retry_after
        details = f"Retry after {retry_after}s" if retry_after else None
        super().__init__(message, details)


class ValidationError(PocketSmithError):
    """Exception raised for input validation errors."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        details = f"Field: {field}" if field else None
        super().__init__(message, details)


class ConfigurationError(PocketSmithError):
    """Exception raised for configuration errors."""

    pass


class CircuitBreakerOpenError(PocketSmithError):
    """Exception raised when circuit breaker is open."""

    def __init__(self, message: str = "Circuit breaker is open - service unavailable"):
        super().__init__(message)


class TimeoutError(PocketSmithError):
    """Exception raised when an operation times out."""

    def __init__(self, message: str = "Operation timed out", timeout_seconds: float | None = None):
        self.timeout_seconds = timeout_seconds
        details = f"Timeout: {timeout_seconds}s" if timeout_seconds else None
        super().__init__(message, details)
