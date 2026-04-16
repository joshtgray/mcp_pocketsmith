"""Unit tests for error helpers."""

import pytest

from pocketsmith_mcp.errors import (
    APIError,
    ValidationError,
    validate_behaviour,
    validate_event_id,
    validate_id,
)


class TestValidateId:
    """Tests for validate_id helper."""

    def test_valid_positive_int(self):
        """Valid positive int should not raise."""
        validate_id(1, "account_id")
        validate_id(999999, "account_id")

    def test_zero_raises(self):
        """Zero should raise ValidationError."""
        with pytest.raises(ValidationError, match="account_id must be a positive integer"):
            validate_id(0, "account_id")

    def test_negative_raises(self):
        """Negative int should raise ValidationError."""
        with pytest.raises(ValidationError, match="transaction_id must be a positive integer"):
            validate_id(-1, "transaction_id")

    def test_field_name_in_message(self):
        """Error message should include the field name."""
        with pytest.raises(ValidationError, match="my_field"):
            validate_id(-5, "my_field")


class TestAPIErrorTruncation:
    """Tests for APIError response body truncation in str()."""

    def test_short_body_not_truncated(self):
        """Short response bodies appear in full."""
        err = APIError("Server error", status_code=500, response_body="short error")
        assert str(err) == "[HTTP 500] Server error: short error"

    def test_long_body_truncated(self):
        """Response bodies over 200 chars are truncated in str()."""
        long_body = "x" * 300
        err = APIError("Server error", status_code=500, response_body=long_body)
        result = str(err)
        assert len(result) < 300
        assert result.endswith("... (truncated)")

    def test_full_body_still_on_attribute(self):
        """Full response body remains accessible on the attribute."""
        long_body = "x" * 300
        err = APIError("Server error", status_code=500, response_body=long_body)
        assert err.response_body == long_body
        assert len(err.response_body) == 300

    def test_none_body(self):
        """None response body should not cause errors."""
        err = APIError("Server error", status_code=500, response_body=None)
        assert str(err) == "[HTTP 500] Server error"


class TestValidateEventId:
    """Tests for validate_event_id helper."""

    def test_valid_plain_integer_string(self):
        """Plain integer string should return the value unchanged."""
        assert validate_event_id("422457484", "event_id") == "422457484"

    def test_valid_composite_id(self):
        """Composite series_id-timestamp string should return the value unchanged."""
        assert validate_event_id("26074572-1614556800", "event_id") == "26074572-1614556800"

    def test_rejects_empty_string(self):
        """Empty string should raise ValidationError."""
        with pytest.raises(ValidationError, match="event_id"):
            validate_event_id("", "event_id")

    def test_rejects_whitespace_only(self):
        """Whitespace-only string should raise ValidationError."""
        with pytest.raises(ValidationError, match="event_id"):
            validate_event_id("   ", "event_id")

    def test_rejects_non_numeric_parts(self):
        """Non-numeric parts should raise ValidationError."""
        with pytest.raises(ValidationError, match="event_id"):
            validate_event_id("abc-def", "event_id")

    def test_rejects_single_non_numeric(self):
        """Single non-numeric part should raise ValidationError."""
        with pytest.raises(ValidationError, match="event_id"):
            validate_event_id("abc", "event_id")

    def test_rejects_too_many_parts(self):
        """Three-part composite ID should raise ValidationError."""
        with pytest.raises(ValidationError, match="event_id"):
            validate_event_id("1-2-3", "event_id")

    def test_field_name_in_message(self):
        """Error message should include the field name."""
        with pytest.raises(ValidationError, match="my_event"):
            validate_event_id("bad-value", "my_event")

    def test_whitespace_padded_returns_stripped(self):
        """Whitespace-padded ID should return trimmed value."""
        assert validate_event_id(" 600 ", "event_id") == "600"

    def test_whitespace_padded_composite_returns_stripped(self):
        """Whitespace-padded composite ID should return trimmed value."""
        assert validate_event_id(" 26074572-1614556800 ", "event_id") == "26074572-1614556800"


class TestValidateBehaviour:
    """Tests for validate_behaviour helper."""

    def test_valid_one(self):
        """'one' should return the value unchanged."""
        assert validate_behaviour("one", "behaviour") == "one"

    def test_valid_all(self):
        """'all' should return the value unchanged."""
        assert validate_behaviour("all", "behaviour") == "all"

    def test_valid_forward(self):
        """'forward' should return the value unchanged."""
        assert validate_behaviour("forward", "behaviour") == "forward"

    def test_rejects_invalid_value(self):
        """Invalid value should raise ValidationError."""
        with pytest.raises(ValidationError, match="behaviour"):
            validate_behaviour("invalid", "behaviour")

    def test_case_sensitive(self):
        """Validation is case-sensitive; 'One' should raise ValidationError."""
        with pytest.raises(ValidationError, match="behaviour"):
            validate_behaviour("One", "behaviour")

    def test_rejects_empty_string(self):
        """Empty string should raise ValidationError."""
        with pytest.raises(ValidationError, match="behaviour"):
            validate_behaviour("", "behaviour")

    def test_field_name_in_message(self):
        """Error message should include the field name."""
        with pytest.raises(ValidationError, match="my_behaviour"):
            validate_behaviour("bad", "my_behaviour")
