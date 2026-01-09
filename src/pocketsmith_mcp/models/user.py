"""User model for PocketSmith API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """PocketSmith user account."""

    id: int = Field(..., description="User ID")
    login: str = Field(..., description="Username/login")
    name: str | None = Field(None, description="Display name")
    email: str = Field(..., description="Email address")
    avatar_url: str | None = Field(None, description="Avatar image URL")

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
    forecast_last_updated_at: datetime | None = Field(
        None, description="Last forecast update time"
    )
    forecast_last_accessed_at: datetime | None = Field(
        None, description="Last forecast access time"
    )
    forecast_start_date: str | None = Field(None, description="Forecast start date")
    forecast_end_date: str | None = Field(None, description="Forecast end date")
    forecast_defer_recalculate: bool = Field(
        False, description="Defer forecast recalculation"
    )
    forecast_needs_recalculate: bool = Field(
        False, description="Forecast needs recalculation"
    )

    # Activity tracking
    last_logged_in_at: datetime | None = Field(None, description="Last login time")
    last_activity_at: datetime | None = Field(None, description="Last activity time")
    created_at: datetime | None = Field(None, description="Account creation time")
    updated_at: datetime | None = Field(None, description="Last update time")

    model_config = ConfigDict(extra="allow")


class UserUpdate(BaseModel):
    """Fields that can be updated on a user."""

    name: str | None = Field(None, description="Display name")
    email: str | None = Field(None, description="Email address")
    time_zone: str | None = Field(None, description="Time zone")
    week_start_day: int | None = Field(None, description="Week start day")
    base_currency_code: str | None = Field(None, description="Base currency code")
    always_show_base_currency: bool | None = Field(
        None, description="Always show base currency"
    )
