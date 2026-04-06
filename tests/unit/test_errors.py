"""Unit tests for error helpers."""

import pytest

from pocketsmith_mcp.errors import APIError, ValidationError, validate_id


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
