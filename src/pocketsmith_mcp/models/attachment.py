"""Attachment model for PocketSmith API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AttachmentVariants(BaseModel):
    """Attachment image variants."""

    thumb_url: str | None = Field(None, description="Thumbnail URL")
    large_url: str | None = Field(None, description="Large image URL")


class ContentTypeMeta(BaseModel):
    """Content type metadata."""

    title: str | None = Field(None, description="Content type title")
    description: str | None = Field(None, description="Content type description")


class Attachment(BaseModel):
    """A file attachment."""

    id: int = Field(..., description="Attachment ID")
    title: str = Field(..., description="Attachment title")
    file_name: str = Field(..., description="Original file name")
    type: str | None = Field(None, description="Attachment type")
    content_type: str = Field(..., description="MIME content type")
    content_type_meta: ContentTypeMeta | None = Field(
        None, description="Content type metadata"
    )
    original_url: str | None = Field(None, description="Original file URL")
    variants: AttachmentVariants | None = Field(None, description="Image variants")

    # Timestamps
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(extra="allow")


class AttachmentCreate(BaseModel):
    """Fields for creating an attachment."""

    title: str = Field(..., description="Attachment title")
    file_name: str = Field(..., description="File name")
    file_data: str = Field(..., description="Base64 encoded file data")


class AttachmentUpdate(BaseModel):
    """Fields for updating an attachment."""

    title: str | None = Field(None, description="Attachment title")


class BudgetAnalysis(BaseModel):
    """Budget analysis result."""

    start_date: str = Field(..., description="Analysis start date")
    end_date: str = Field(..., description="Analysis end date")
    currency_code: str = Field(..., description="Currency code")
    total_actual_amount: float = Field(0.0, description="Total actual amount")
    total_forecast_amount: float = Field(0.0, description="Total forecast amount")
    total_over_by: float = Field(0.0, description="Total over budget")
    total_under_by: float = Field(0.0, description="Total under budget")
    category_summaries: list[Any] = Field(default_factory=list, description="Category summaries")

    model_config = ConfigDict(extra="allow")


class TrendAnalysis(BaseModel):
    """Trend analysis result."""

    start_date: str = Field(..., description="Analysis start date")
    end_date: str = Field(..., description="Analysis end date")
    currency_code: str = Field(..., description="Currency code")
    periods: list[Any] = Field(default_factory=list, description="Period data")

    model_config = ConfigDict(extra="allow")
