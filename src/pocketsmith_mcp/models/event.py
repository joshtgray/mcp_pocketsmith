"""Event model for PocketSmith API."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RepeatType(str, Enum):
    """Event repeat frequency."""

    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    EACH = "each"
    ONCE_OFF = "once_off"


class Event(BaseModel):
    """A calendar event (budget event, recurring transaction, etc.)."""

    id: int = Field(..., description="Event ID")

    # Amount information
    amount: float = Field(..., description="Event amount")
    amount_in_base_currency: Optional[float] = Field(
        None, description="Amount in base currency"
    )
    currency_code: str = Field(..., description="Currency code")

    # Schedule
    date: str = Field(..., description="Event date (YYYY-MM-DD)")
    repeat_type: RepeatType = Field(RepeatType.ONCE, description="Repeat frequency")
    repeat_interval: int = Field(1, description="Repeat interval")

    # Series information
    series_id: Optional[int] = Field(None, description="Series ID for recurring events")
    series_start_id: Optional[int] = Field(None, description="First event in series")
    infinite_series: bool = Field(False, description="Is this an infinite series")

    # Details
    note: Optional[str] = Field(None, description="Event note")
    colour: Optional[str] = Field(None, description="Event color (hex)")

    # Related entities
    category: Optional[Dict[str, Any]] = Field(None, description="Event category")
    scenario: Optional[Dict[str, Any]] = Field(None, description="Associated scenario")

    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic model configuration."""

        extra = "allow"


class EventCreate(BaseModel):
    """Fields for creating an event."""

    category_id: int = Field(..., description="Category ID")
    amount: float = Field(..., description="Event amount")
    date: str = Field(..., description="Event date (YYYY-MM-DD)")
    repeat_type: RepeatType = Field(RepeatType.ONCE, description="Repeat frequency")
    repeat_interval: int = Field(1, description="Repeat interval")
    note: Optional[str] = Field(None, description="Event note")
    colour: Optional[str] = Field(None, description="Event color (hex)")


class EventUpdate(BaseModel):
    """Fields for updating an event."""

    category_id: Optional[int] = Field(None, description="Category ID")
    amount: Optional[float] = Field(None, description="Event amount")
    date: Optional[str] = Field(None, description="Event date (YYYY-MM-DD)")
    repeat_type: Optional[RepeatType] = Field(None, description="Repeat frequency")
    repeat_interval: Optional[int] = Field(None, description="Repeat interval")
    note: Optional[str] = Field(None, description="Event note")
    colour: Optional[str] = Field(None, description="Event color (hex)")
