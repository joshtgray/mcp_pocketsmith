"""Transaction model for PocketSmith API."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Transaction type (debit or credit)."""

    DEBIT = "debit"
    CREDIT = "credit"


class TransactionStatus(str, Enum):
    """Transaction status."""

    PENDING = "pending"
    POSTED = "posted"


class Transaction(BaseModel):
    """A financial transaction."""

    id: int = Field(..., description="Transaction ID")
    payee: str = Field(..., description="Payee name")
    original_payee: Optional[str] = Field(None, description="Original payee from import")
    date: str = Field(..., description="Transaction date (YYYY-MM-DD)")
    upload_source: Optional[str] = Field(None, description="Source of transaction import")

    # Amount information
    amount: float = Field(..., description="Transaction amount")
    amount_in_base_currency: Optional[float] = Field(
        None, description="Amount in base currency"
    )
    type: TransactionType = Field(..., description="Debit or credit")
    closing_balance: Optional[float] = Field(None, description="Balance after transaction")

    # Details
    cheque_number: Optional[str] = Field(None, description="Check/cheque number")
    memo: Optional[str] = Field(None, description="Transaction memo")
    note: Optional[str] = Field(None, description="User note")
    labels: List[str] = Field(default_factory=list, description="Transaction labels")

    # Status
    is_transfer: bool = Field(False, description="Is this a transfer")
    needs_review: bool = Field(False, description="Needs manual review")
    status: TransactionStatus = Field(
        TransactionStatus.POSTED, description="Transaction status"
    )

    # Related entities
    category: Optional[Dict[str, Any]] = Field(None, description="Transaction category")
    transaction_account: Optional[Dict[str, Any]] = Field(
        None, description="Transaction account"
    )

    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic model configuration."""

        extra = "allow"


class TransactionCreate(BaseModel):
    """Fields for creating a transaction."""

    payee: str = Field(..., description="Payee name")
    amount: float = Field(..., description="Transaction amount (negative for expenses)")
    date: str = Field(..., description="Transaction date (YYYY-MM-DD)")
    category_id: Optional[int] = Field(None, description="Category ID")
    note: Optional[str] = Field(None, description="User note")
    memo: Optional[str] = Field(None, description="Transaction memo")
    cheque_number: Optional[str] = Field(None, description="Check/cheque number")
    is_transfer: bool = Field(False, description="Is this a transfer")
    labels: Optional[List[str]] = Field(None, description="Transaction labels")
    needs_review: bool = Field(False, description="Needs manual review")


class TransactionUpdate(BaseModel):
    """Fields for updating a transaction."""

    payee: Optional[str] = Field(None, description="Payee name")
    amount: Optional[float] = Field(None, description="Transaction amount")
    date: Optional[str] = Field(None, description="Transaction date (YYYY-MM-DD)")
    category_id: Optional[int] = Field(None, description="Category ID")
    note: Optional[str] = Field(None, description="User note")
    memo: Optional[str] = Field(None, description="Transaction memo")
    cheque_number: Optional[str] = Field(None, description="Check/cheque number")
    is_transfer: Optional[bool] = Field(None, description="Is this a transfer")
    labels: Optional[List[str]] = Field(None, description="Transaction labels")
    needs_review: Optional[bool] = Field(None, description="Needs manual review")
