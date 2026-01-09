"""Common Pydantic models shared across entities."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """API error response."""

    error: str = Field(..., description="Error message")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response wrapper."""

    data: list[T] = Field(default_factory=list, description="List of items")
    total: int | None = Field(None, description="Total number of items")
    page: int | None = Field(None, description="Current page number")
    per_page: int | None = Field(None, description="Items per page")
    total_pages: int | None = Field(None, description="Total number of pages")


class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields."""

    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


class Currency(BaseModel):
    """Currency information."""

    id: str = Field(..., description="Currency code (e.g., 'USD', 'NZD')")
    name: str = Field(..., description="Currency name")
    symbol: str = Field(..., description="Currency symbol")
    decimal_places: int = Field(2, description="Number of decimal places")


class TimeZone(BaseModel):
    """Time zone information."""

    id: str = Field(..., description="Time zone identifier")
    name: str = Field(..., description="Time zone display name")
    formatted_offset: str = Field(..., description="Formatted UTC offset")
    offset_minutes: int = Field(..., description="Offset from UTC in minutes")


class Label(BaseModel):
    """Transaction label."""

    id: str = Field(..., description="Label identifier")
    name: str = Field(..., description="Label name")


class SavedSearch(BaseModel):
    """Saved transaction search."""

    id: int = Field(..., description="Saved search ID")
    title: str = Field(..., description="Search title")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
