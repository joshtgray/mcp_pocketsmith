"""Account and TransactionAccount models for PocketSmith API."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
    number: Optional[str] = Field(None, description="Account number")

    # Balance information
    current_balance: float = Field(0.0, description="Current balance")
    current_balance_date: Optional[str] = Field(None, description="Balance date")
    current_balance_in_base_currency: float = Field(
        0.0, description="Current balance in base currency"
    )
    current_balance_exchange_rate: Optional[float] = Field(
        None, description="Exchange rate used"
    )
    safe_balance: Optional[float] = Field(None, description="Safe balance")
    safe_balance_in_base_currency: Optional[float] = Field(
        None, description="Safe balance in base currency"
    )

    # Starting balance
    starting_balance: Optional[float] = Field(None, description="Starting balance")
    starting_balance_date: Optional[str] = Field(None, description="Starting balance date")

    # Metadata
    currency_code: str = Field(..., description="Currency code")
    type: Optional[AccountType] = Field(None, description="Account type")
    is_net_worth: bool = Field(True, description="Include in net worth")

    # Related entities
    institution: Optional[Dict[str, Any]] = Field(None, description="Associated institution")

    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic model configuration."""

        extra = "allow"


class Scenario(BaseModel):
    """A financial scenario for forecasting."""

    id: int = Field(..., description="Scenario ID")
    title: str = Field(..., description="Scenario title")
    description: Optional[str] = Field(None, description="Scenario description")

    # Interest settings
    interest_rate: Optional[float] = Field(None, description="Interest rate")
    interest_rate_repeat_id: Optional[int] = Field(None, description="Interest repeat ID")
    type: Optional[str] = Field(None, description="Scenario type")

    # Value constraints
    minimum_value: Optional[float] = Field(None, description="Minimum value")
    maximum_value: Optional[float] = Field(None, description="Maximum value")
    achieve_date: Optional[str] = Field(None, description="Target achieve date")

    # Balance information
    starting_balance: Optional[float] = Field(None, description="Starting balance")
    starting_balance_date: Optional[str] = Field(None, description="Starting balance date")
    closing_balance: Optional[float] = Field(None, description="Closing balance")
    closing_balance_date: Optional[str] = Field(None, description="Closing balance date")
    current_balance: Optional[float] = Field(None, description="Current balance")
    current_balance_date: Optional[str] = Field(None, description="Current balance date")
    current_balance_in_base_currency: Optional[float] = Field(
        None, description="Current balance in base currency"
    )
    current_balance_exchange_rate: Optional[float] = Field(
        None, description="Exchange rate"
    )
    safe_balance: Optional[float] = Field(None, description="Safe balance")
    safe_balance_in_base_currency: Optional[float] = Field(
        None, description="Safe balance in base currency"
    )

    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic model configuration."""

        extra = "allow"


class Account(BaseModel):
    """A PocketSmith account (container for transaction accounts)."""

    id: int = Field(..., description="Account ID")
    title: Optional[str] = Field(None, description="Account title")
    currency_code: str = Field(..., description="Currency code")
    type: Optional[AccountType] = Field(None, description="Account type")

    # Balance information
    current_balance: float = Field(0.0, description="Current balance")
    current_balance_date: Optional[str] = Field(None, description="Balance date")
    current_balance_in_base_currency: float = Field(
        0.0, description="Current balance in base currency"
    )
    current_balance_exchange_rate: Optional[float] = Field(
        None, description="Exchange rate used"
    )
    safe_balance: Optional[float] = Field(None, description="Safe balance")
    safe_balance_in_base_currency: Optional[float] = Field(
        None, description="Safe balance in base currency"
    )

    # Settings
    is_net_worth: bool = Field(True, description="Include in net worth")

    # Related entities
    primary_transaction_account: Optional[TransactionAccount] = Field(
        None, description="Primary transaction account"
    )
    primary_scenario: Optional[Scenario] = Field(None, description="Primary scenario")
    transaction_accounts: List[TransactionAccount] = Field(
        default_factory=list, description="Transaction accounts"
    )
    scenarios: List[Scenario] = Field(default_factory=list, description="Scenarios")
    institution: Optional[Dict[str, Any]] = Field(None, description="Associated institution")

    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic model configuration."""

        extra = "allow"


class AccountCreate(BaseModel):
    """Fields for creating an account."""

    title: str = Field(..., description="Account title")
    currency_code: str = Field(..., description="Currency code")
    type: AccountType = Field(..., description="Account type")
    institution_id: Optional[int] = Field(None, description="Institution ID")
    is_net_worth: bool = Field(True, description="Include in net worth")


class AccountUpdate(BaseModel):
    """Fields for updating an account."""

    title: Optional[str] = Field(None, description="Account title")
    currency_code: Optional[str] = Field(None, description="Currency code")
    type: Optional[AccountType] = Field(None, description="Account type")
    is_net_worth: Optional[bool] = Field(None, description="Include in net worth")


class TransactionAccountUpdate(BaseModel):
    """Fields for updating a transaction account."""

    name: Optional[str] = Field(None, description="Account name")
    number: Optional[str] = Field(None, description="Account number")
    starting_balance: Optional[float] = Field(None, description="Starting balance")
    starting_balance_date: Optional[str] = Field(None, description="Starting balance date")
    is_net_worth: Optional[bool] = Field(None, description="Include in net worth")
