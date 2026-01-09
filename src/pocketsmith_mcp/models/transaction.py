"""Transaction model for PocketSmith API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    original_payee: str | None = Field(None, description="Original payee from import")
    date: str = Field(..., description="Transaction date (YYYY-MM-DD)")
    upload_source: str | None = Field(None, description="Source of transaction import")

    # Amount information
    amount: float = Field(..., description="Transaction amount")
    amount_in_base_currency: float | None = Field(
        None, description="Amount in base currency"
    )
    type: TransactionType = Field(..., description="Debit or credit")
    closing_balance: float | None = Field(None, description="Balance after transaction")

    # Details
    cheque_number: str | None = Field(None, description="Check/cheque number")
    memo: str | None = Field(None, description="Transaction memo")
    note: str | None = Field(None, description="User note")
    labels: list[str] = Field(default_factory=list, description="Transaction labels")

    # Status
    is_transfer: bool = Field(False, description="Is this a transfer")
    needs_review: bool = Field(False, description="Needs manual review")
    status: TransactionStatus = Field(
        TransactionStatus.POSTED, description="Transaction status"
    )

    # Related entities
    category: dict[str, Any] | None = Field(None, description="Transaction category")
    transaction_account: dict[str, Any] | None = Field(
        None, description="Transaction account"
    )

    # Timestamps
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(extra="allow")


class TransactionCreate(BaseModel):
    """Fields for creating a transaction."""

    payee: str = Field(..., description="Payee name")
    amount: float = Field(..., description="Transaction amount (negative for expenses)")
    date: str = Field(..., description="Transaction date (YYYY-MM-DD)")
    category_id: int | None = Field(None, description="Category ID")
    note: str | None = Field(None, description="User note")
    memo: str | None = Field(None, description="Transaction memo")
    cheque_number: str | None = Field(None, description="Check/cheque number")
    is_transfer: bool = Field(False, description="Is this a transfer")
    labels: list[str] | None = Field(None, description="Transaction labels")
    needs_review: bool = Field(False, description="Needs manual review")


class TransactionUpdate(BaseModel):
    """Fields for updating a transaction."""

    payee: str | None = Field(None, description="Payee name")
    amount: float | None = Field(None, description="Transaction amount")
    date: str | None = Field(None, description="Transaction date (YYYY-MM-DD)")
    category_id: int | None = Field(None, description="Category ID")
    note: str | None = Field(None, description="User note")
    memo: str | None = Field(None, description="Transaction memo")
    cheque_number: str | None = Field(None, description="Check/cheque number")
    is_transfer: bool | None = Field(None, description="Is this a transfer")
    labels: list[str] | None = Field(None, description="Transaction labels")
    needs_review: bool | None = Field(None, description="Needs manual review")
