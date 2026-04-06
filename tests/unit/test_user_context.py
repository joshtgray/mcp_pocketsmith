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

    def test_set_once_only(self):
        """Setting user_id twice should raise RuntimeError."""
        ctx = UserContext()
        ctx.user_id = 42
        with pytest.raises(RuntimeError, match="user_id has already been set"):
            ctx.user_id = 99

    def test_reject_zero_setter(self):
        """Setting user_id to zero should raise ValueError."""
        ctx = UserContext()
        with pytest.raises(ValueError, match="user_id must be a positive integer"):
            ctx.user_id = 0

    def test_reject_negative_setter(self):
        """Setting user_id to negative should raise ValueError."""
        ctx = UserContext()
        with pytest.raises(ValueError, match="user_id must be a positive integer"):
            ctx.user_id = -5

    def test_constructor_with_zero_leaves_unset(self):
        """Constructor with 0 (default) leaves user_id unresolved."""
        ctx = UserContext(user_id=0)
        with pytest.raises(RuntimeError, match="user_id has not been resolved"):
            _ = ctx.user_id
        # But setting it once should still work
        ctx.user_id = 42
        assert ctx.user_id == 42
