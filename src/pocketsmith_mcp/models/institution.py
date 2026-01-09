"""Institution model for PocketSmith API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Institution(BaseModel):
    """Financial institution (bank, credit card company, etc.)."""

    id: int = Field(..., description="Institution ID")
    title: str = Field(..., description="Institution name")
    currency_code: str = Field(..., description="Default currency code")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic model configuration."""

        extra = "allow"


class InstitutionCreate(BaseModel):
    """Fields for creating an institution."""

    title: str = Field(..., description="Institution name")
    currency_code: str = Field(..., description="Default currency code")


class InstitutionUpdate(BaseModel):
    """Fields for updating an institution."""

    title: Optional[str] = Field(None, description="Institution name")
    currency_code: Optional[str] = Field(None, description="Default currency code")
