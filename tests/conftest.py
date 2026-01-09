"""Pytest configuration and fixtures."""

import os
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

# Set test environment variables before importing modules
os.environ["POCKETSMITH_API_KEY"] = "test_api_key_12345"
os.environ["DEBUG"] = "true"


@pytest.fixture
def api_key() -> str:
    """Provide a test API key."""
    return "test_api_key_12345"


@pytest.fixture
def mock_httpx_client() -> Generator[AsyncMock, None, None]:
    """Provide a mocked httpx AsyncClient."""
    with patch("httpx.AsyncClient") as mock:
        client_instance = AsyncMock()
        mock.return_value = client_instance
        yield client_instance


@pytest.fixture
def sample_user() -> dict[str, Any]:
    """Provide a sample user response."""
    return {
        "id": 1,
        "login": "testuser",
        "name": "Test User",
        "email": "test@example.com",
        "avatar_url": "https://example.com/avatar.png",
        "beta_user": False,
        "time_zone": "Pacific/Auckland",
        "week_start_day": 1,
        "is_reviewing_transactions": False,
        "base_currency_code": "NZD",
        "always_show_base_currency": False,
        "using_multiple_currencies": False,
        "available_accounts": 10,
        "available_budgets": 5,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_account() -> dict[str, Any]:
    """Provide a sample account response."""
    return {
        "id": 1,
        "title": "Main Checking",
        "currency_code": "NZD",
        "type": "bank",
        "is_net_worth": True,
        "current_balance": 1500.00,
        "current_balance_date": "2024-01-15",
        "current_balance_in_base_currency": 1500.00,
        "safe_balance": 1200.00,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "transaction_accounts": [],
        "scenarios": [],
    }


@pytest.fixture
def sample_transaction() -> dict[str, Any]:
    """Provide a sample transaction response."""
    return {
        "id": 1001,
        "payee": "Grocery Store",
        "original_payee": "GROCERY STORE #123",
        "date": "2024-01-15",
        "amount": -50.00,
        "amount_in_base_currency": -50.00,
        "type": "debit",
        "is_transfer": False,
        "needs_review": False,
        "status": "posted",
        "memo": "Weekly groceries",
        "note": "",
        "labels": ["food", "essentials"],
        "category": {
            "id": 10,
            "title": "Groceries",
        },
        "transaction_account": {
            "id": 1,
            "name": "Main Checking",
        },
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z",
    }


@pytest.fixture
def sample_category() -> dict[str, Any]:
    """Provide a sample category response."""
    return {
        "id": 10,
        "title": "Groceries",
        "colour": "#4CAF50",
        "parent_id": 5,
        "is_transfer": False,
        "is_bill": False,
        "roll_up": False,
        "refund_behaviour": "none",
        "children": [],
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_institution() -> dict[str, Any]:
    """Provide a sample institution response."""
    return {
        "id": 1,
        "title": "Test Bank",
        "currency_code": "NZD",
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_budget_summary() -> dict[str, Any]:
    """Provide a sample budget summary response."""
    return {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "currency_code": "NZD",
        "total_actual_amount": -2500.00,
        "total_forecast_amount": -3000.00,
        "total_over_by": 0.00,
        "total_under_by": 500.00,
        "category_summaries": [],
    }


@pytest.fixture
def sample_event() -> dict[str, Any]:
    """Provide a sample event response."""
    return {
        "id": 100,
        "amount": -100.00,
        "amount_in_base_currency": -100.00,
        "currency_code": "NZD",
        "date": "2024-02-01",
        "repeat_type": "monthly",
        "repeat_interval": 1,
        "note": "Monthly subscription",
        "colour": "#2196F3",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_attachment() -> dict[str, Any]:
    """Provide a sample attachment response."""
    return {
        "id": 50,
        "title": "Receipt",
        "file_name": "receipt.pdf",
        "type": "document",
        "content_type": "application/pdf",
        "original_url": "https://example.com/receipt.pdf",
        "created_at": "2024-01-15T00:00:00Z",
        "updated_at": "2024-01-15T00:00:00Z",
    }


@pytest.fixture
def sample_currencies() -> list:
    """Provide sample currencies response."""
    return [
        {"id": "NZD", "name": "New Zealand Dollar", "symbol": "$", "decimal_places": 2},
        {"id": "USD", "name": "US Dollar", "symbol": "$", "decimal_places": 2},
        {"id": "EUR", "name": "Euro", "symbol": "\u20ac", "decimal_places": 2},
    ]


@pytest.fixture
def sample_time_zones() -> list:
    """Provide sample time zones response."""
    return [
        {
            "id": "Pacific/Auckland",
            "name": "Auckland",
            "formatted_offset": "+13:00",
            "offset_minutes": 780,
        },
        {
            "id": "America/New_York",
            "name": "New York",
            "formatted_offset": "-05:00",
            "offset_minutes": -300,
        },
    ]
