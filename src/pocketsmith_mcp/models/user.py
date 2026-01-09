"""User model for PocketSmith API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """PocketSmith user account."""

    id: int = Field(..., description="User ID")
    login: str = Field(..., description="Username/login")
    name: Optional[str] = Field(None, description="Display name")
    email: str = Field(..., description="Email address")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")

    # Account settings
    beta_user: bool = Field(False, description="Whether user is a beta tester")
    time_zone: str = Field(..., description="User's time zone")
    week_start_day: int = Field(0, description="Week start day (0=Sunday, 1=Monday)")
    is_reviewing_transactions: bool = Field(
        False, description="Whether transaction review mode is enabled"
    )

    # Currency settings
    base_currency_code: str = Field(..., description="Base currency code")
    always_show_base_currency: bool = Field(
        False, description="Always show amounts in base currency"
    )
    using_multiple_currencies: bool = Field(
        False, description="Whether user has multiple currencies"
    )

    # Account limits
    available_accounts: int = Field(0, description="Number of accounts available")
    available_budgets: int = Field(0, description="Number of budgets available")

    # Forecast settings
    forecast_last_updated_at: Optional[datetime] = Field(
        None, description="Last forecast update time"
    )
    forecast_last_accessed_at: Optional[datetime] = Field(
        None, description="Last forecast access time"
    )
    forecast_start_date: Optional[str] = Field(None, description="Forecast start date")
    forecast_end_date: Optional[str] = Field(None, description="Forecast end date")
    forecast_defer_recalculate: bool = Field(
        False, description="Defer forecast recalculation"
    )
    forecast_needs_recalculate: bool = Field(
        False, description="Forecast needs recalculation"
    )

    # Activity tracking
    last_logged_in_at: Optional[datetime] = Field(None, description="Last login time")
    last_activity_at: Optional[datetime] = Field(None, description="Last activity time")
    created_at: Optional[datetime] = Field(None, description="Account creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")

    class Config:
        """Pydantic model configuration."""

        extra = "allow"  # Allow extra fields from API


class UserUpdate(BaseModel):
    """Fields that can be updated on a user."""

    name: Optional[str] = Field(None, description="Display name")
    email: Optional[str] = Field(None, description="Email address")
    time_zone: Optional[str] = Field(None, description="Time zone")
    week_start_day: Optional[int] = Field(None, description="Week start day")
    base_currency_code: Optional[str] = Field(None, description="Base currency code")
    always_show_base_currency: Optional[bool] = Field(
        None, description="Always show base currency"
    )
