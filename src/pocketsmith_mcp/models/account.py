"""Account and TransactionAccount models for PocketSmith API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AccountType(str, Enum):
    """Types of accounts supported by PocketSmith."""

    BANK = "bank"
    CREDITS = "credits"
    CASH = "cash"
    LOANS = "loans"
    MORTGAGE = "mortgage"
    STOCKS = "stocks"
    VEHICLE = "vehicle"
    PROPERTY = "property"
    INSURANCE = "insurance"
    OTHER_ASSET = "other_asset"
    OTHER_LIABILITY = "other_liability"


class TransactionAccount(BaseModel):
    """A transaction account within a PocketSmith account."""

    id: int = Field(..., description="Transaction account ID")
    name: str = Field(..., description="Account name")
    number: str | None = Field(None, description="Account number")

    # Balance information
    current_balance: float = Field(0.0, description="Current balance")
    current_balance_date: str | None = Field(None, description="Balance date")
    current_balance_in_base_currency: float = Field(
        0.0, description="Current balance in base currency"
    )
    current_balance_exchange_rate: float | None = Field(
        None, description="Exchange rate used"
    )
    safe_balance: float | None = Field(None, description="Safe balance")
    safe_balance_in_base_currency: float | None = Field(
        None, description="Safe balance in base currency"
    )

    # Starting balance
    starting_balance: float | None = Field(None, description="Starting balance")
    starting_balance_date: str | None = Field(None, description="Starting balance date")

    # Metadata
    currency_code: str = Field(..., description="Currency code")
    type: AccountType | None = Field(None, description="Account type")
    is_net_worth: bool = Field(True, description="Include in net worth")

    # Related entities
    institution: dict[str, Any] | None = Field(None, description="Associated institution")

    # Timestamps
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(extra="allow")


class Scenario(BaseModel):
    """A financial scenario for forecasting."""

    id: int = Field(..., description="Scenario ID")
    title: str = Field(..., description="Scenario title")
    description: str | None = Field(None, description="Scenario description")

    # Interest settings
    interest_rate: float | None = Field(None, description="Interest rate")
    interest_rate_repeat_id: int | None = Field(None, description="Interest repeat ID")
    type: str | None = Field(None, description="Scenario type")

    # Value constraints
    minimum_value: float | None = Field(None, description="Minimum value")
    maximum_value: float | None = Field(None, description="Maximum value")
    achieve_date: str | None = Field(None, description="Target achieve date")

    # Balance information
    starting_balance: float | None = Field(None, description="Starting balance")
    starting_balance_date: str | None = Field(None, description="Starting balance date")
    closing_balance: float | None = Field(None, description="Closing balance")
    closing_balance_date: str | None = Field(None, description="Closing balance date")
    current_balance: float | None = Field(None, description="Current balance")
    current_balance_date: str | None = Field(None, description="Current balance date")
    current_balance_in_base_currency: float | None = Field(
        None, description="Current balance in base currency"
    )
    current_balance_exchange_rate: float | None = Field(
        None, description="Exchange rate"
    )
    safe_balance: float | None = Field(None, description="Safe balance")
    safe_balance_in_base_currency: float | None = Field(
        None, description="Safe balance in base currency"
    )

    # Timestamps
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(extra="allow")


class Account(BaseModel):
    """A PocketSmith account (container for transaction accounts)."""

    id: int = Field(..., description="Account ID")
    title: str | None = Field(None, description="Account title")
    currency_code: str = Field(..., description="Currency code")
    type: AccountType | None = Field(None, description="Account type")

    # Balance information
    current_balance: float = Field(0.0, description="Current balance")
    current_balance_date: str | None = Field(None, description="Balance date")
    current_balance_in_base_currency: float = Field(
        0.0, description="Current balance in base currency"
    )
    current_balance_exchange_rate: float | None = Field(
        None, description="Exchange rate used"
    )
    safe_balance: float | None = Field(None, description="Safe balance")
    safe_balance_in_base_currency: float | None = Field(
        None, description="Safe balance in base currency"
    )

    # Settings
    is_net_worth: bool = Field(True, description="Include in net worth")

    # Related entities
    primary_transaction_account: TransactionAccount | None = Field(
        None, description="Primary transaction account"
    )
    primary_scenario: Scenario | None = Field(None, description="Primary scenario")
    transaction_accounts: list[TransactionAccount] = Field(
        default_factory=list, description="Transaction accounts"
    )
    scenarios: list[Scenario] = Field(default_factory=list, description="Scenarios")
    institution: dict[str, Any] | None = Field(None, description="Associated institution")

    # Timestamps
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(extra="allow")


class AccountCreate(BaseModel):
    """Fields for creating an account."""

    title: str = Field(..., description="Account title")
    currency_code: str = Field(..., description="Currency code")
    type: AccountType = Field(..., description="Account type")
    institution_id: int | None = Field(None, description="Institution ID")
    is_net_worth: bool = Field(True, description="Include in net worth")


class AccountUpdate(BaseModel):
    """Fields for updating an account."""

    title: str | None = Field(None, description="Account title")
    currency_code: str | None = Field(None, description="Currency code")
    type: AccountType | None = Field(None, description="Account type")
    is_net_worth: bool | None = Field(None, description="Include in net worth")


class TransactionAccountUpdate(BaseModel):
    """Fields for updating a transaction account."""

    name: str | None = Field(None, description="Account name")
    number: str | None = Field(None, description="Account number")
    starting_balance: float | None = Field(None, description="Starting balance")
    starting_balance_date: str | None = Field(None, description="Starting balance date")
    is_net_worth: bool | None = Field(None, description="Include in net worth")
