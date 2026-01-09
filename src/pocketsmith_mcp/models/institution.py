"""Institution model for PocketSmith API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Institution(BaseModel):
    """Financial institution (bank, credit card company, etc.)."""

    id: int = Field(..., description="Institution ID")
    title: str = Field(..., description="Institution name")
    currency_code: str = Field(..., description="Default currency code")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(extra="allow")


class InstitutionCreate(BaseModel):
    """Fields for creating an institution."""

    title: str = Field(..., description="Institution name")
    currency_code: str = Field(..., description="Default currency code")


class InstitutionUpdate(BaseModel):
    """Fields for updating an institution."""

    title: str | None = Field(None, description="Institution name")
    currency_code: str | None = Field(None, description="Default currency code")
