"""Category model for PocketSmith API."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RefundBehaviour(str, Enum):
    """How refunds are handled for a category."""

    CREDITS_ARE_REFUNDS = "credits_are_refunds"
    DEBITS_ARE_REFUNDS = "debits_are_refunds"
    NONE = "none"


class Category(BaseModel):
    """A transaction category."""

    id: int = Field(..., description="Category ID")
    title: str = Field(..., description="Category name")
    colour: Optional[str] = Field(None, description="Category color (hex)")

    # Hierarchy
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    children: List["Category"] = Field(default_factory=list, description="Child categories")

    # Settings
    is_transfer: bool = Field(False, description="Is this a transfer category")
    is_bill: bool = Field(False, description="Is this a bill category")
    roll_up: bool = Field(False, description="Roll up to parent in reports")
    refund_behaviour: RefundBehaviour = Field(
        RefundBehaviour.NONE, description="How refunds are handled"
    )

    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic model configuration."""

        extra = "allow"


# Enable forward references for nested Category
Category.model_rebuild()


class CategoryCreate(BaseModel):
    """Fields for creating a category."""

    title: str = Field(..., description="Category name")
    colour: Optional[str] = Field(None, description="Category color (hex)")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    is_transfer: bool = Field(False, description="Is this a transfer category")
    is_bill: bool = Field(False, description="Is this a bill category")
    roll_up: bool = Field(False, description="Roll up to parent in reports")
    refund_behaviour: RefundBehaviour = Field(
        RefundBehaviour.NONE, description="How refunds are handled"
    )


class CategoryUpdate(BaseModel):
    """Fields for updating a category."""

    title: Optional[str] = Field(None, description="Category name")
    colour: Optional[str] = Field(None, description="Category color (hex)")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    is_transfer: Optional[bool] = Field(None, description="Is this a transfer category")
    is_bill: Optional[bool] = Field(None, description="Is this a bill category")
    roll_up: Optional[bool] = Field(None, description="Roll up to parent in reports")
    refund_behaviour: Optional[RefundBehaviour] = Field(
        None, description="How refunds are handled"
    )


class CategoryRule(BaseModel):
    """A rule for automatically categorizing transactions."""

    id: int = Field(..., description="Rule ID")
    category_id: int = Field(..., description="Category to apply")
    payee_matches: Optional[str] = Field(None, description="Payee pattern to match")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic model configuration."""

        extra = "allow"


class CategoryRuleCreate(BaseModel):
    """Fields for creating a category rule."""

    payee_matches: str = Field(..., description="Payee pattern to match")
