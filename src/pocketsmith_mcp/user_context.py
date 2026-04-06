"""User context holder for auto-resolved user ID."""


class UserContext:
    """Mutable holder for the authenticated user's ID.

    Created during server setup and populated by the lifespan handler
    before any tool calls are served. Tools read ``user_id`` at call
    time via closure.
    """

    def __init__(self, user_id: int = 0) -> None:
        self._user_id = user_id

    @property
    def user_id(self) -> int:
        if self._user_id == 0:
            raise RuntimeError(
                "user_id has not been resolved yet. "
                "The server lifespan must run before tools are called."
            )
        return self._user_id

    @user_id.setter
    def user_id(self, value: int) -> None:
        if self._user_id != 0:
            raise RuntimeError(
                "user_id has already been set and cannot be changed."
            )
        if not isinstance(value, int) or value <= 0:
            raise ValueError(
                f"user_id must be a positive integer, got {value}"
            )
        self._user_id = value
