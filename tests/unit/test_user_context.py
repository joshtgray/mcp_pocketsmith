"""Unit tests for UserContext."""

import pytest

from pocketsmith_mcp.user_context import UserContext


class TestUserContext:
    """Tests for UserContext holder."""

    def test_set_and_get(self):
        """Test setting and getting user_id."""
        ctx = UserContext()
        ctx.user_id = 42
        assert ctx.user_id == 42

    def test_initial_value(self):
        """Test that initial value of 0 raises."""
        ctx = UserContext()
        with pytest.raises(RuntimeError, match="user_id has not been resolved"):
            _ = ctx.user_id

    def test_constructor_with_value(self):
        """Test constructing with a user_id."""
        ctx = UserContext(user_id=99)
        assert ctx.user_id == 99
