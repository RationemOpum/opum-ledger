from datetime import datetime
from enum import Enum
from fractions import Fraction
from typing import Annotated, TypeAlias

from pydantic import UUID7, BaseModel, ConfigDict, Field, field_validator

from opum_ledger.domain.types.account import AccountUUID
from opum_ledger.domain.types.commodity import CommodityUUID
from opum_ledger.domain.types.ledger import LedgerUUID


class TransactionState(Enum):
    CLEARED = "cleared"
    UNCLEARED = "uncleared"
    PENDING = "pending"


TransactionUUID: TypeAlias = Annotated[
    UUID7,
    Field(
        ...,
        description="The transaction unique ID",
        json_schema_extra={
            "format": "uuid",
        },
    ),
]


TransactionDescription: TypeAlias = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        max_length=1024,
        description="The transaction description",
        json_schema_extra={
            "format": "string",
        },
    ),
]


TransactionDateTime: TypeAlias = Annotated[
    datetime,
    Field(
        ...,
        description="The transaction date and time",
        json_schema_extra={
            "format": "date-time",
        },
    ),
]


TransactionCreatedAt: TypeAlias = Annotated[
    datetime,
    Field(
        ...,
        description="The transaction creation date",
        json_schema_extra={
            "format": "date-time",
        },
    ),
]

TransactionUpdatedAt: TypeAlias = Annotated[
    datetime,
    Field(
        ...,
        description="The transaction update date",
        json_schema_extra={
            "format": "date-time",
        },
    ),
]


class TransactionOrdering(Enum):
    DATE_TIME_ASC = "+date_time"
    DATE_TIME_DESC = "-date_time"


class AccountBalance(BaseModel):
    id: UUID7 = Field(
        ...,
        description="The commodity unique ID",
        alias="_id",
        json_schema_extra={
            "format": "uuid",
        },
    )
    balance: int = Field(
        ...,
        description="The account balance",
    )


class FractionPrice(BaseModel):
    numerator: int = Field(
        ...,
        description="The numerator in minimal units. For example, cents.",
    )
    denominator: int = Field(
        ...,
        description="The denominator in minimal units. For example, cents.",
    )

    @property
    def amount(self) -> Fraction:
        return Fraction(
            numerator=self.numerator,
            denominator=self.denominator,
        )


class Price(BaseModel):
    commodity_id: CommodityUUID
    price: FractionPrice = Field(
        ...,
        description="The price",
    )


class Amount(BaseModel):
    commodity_id: CommodityUUID
    amount: int = Field(
        ...,
        description="The amount in minimal units. For example, cents.",
    )


class Detail(BaseModel):
    account_id: AccountUUID
    amount: Amount = Field(
        ...,
        description="The commodity amount.",
    )
    price: Price | None = Field(
        None,
        description="The price of the amount",
    )

    @property
    def total(self) -> Amount:
        if self.price is None:
            return self.amount

        value = self.amount.amount * self.price.price.amount
        if value.denominator != 1:
            raise ValueError("Price is not a whole number")

        return Amount(
            commodity_id=self.price.commodity_id,
            amount=value.numerator,
        )


class TransactionBase(BaseModel):
    description: TransactionDescription
    date_time: TransactionDateTime
    details: list[Detail] = Field(
        ...,
        description="The transaction details",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="The transaction tags",
    )
    state: TransactionState = Field(
        TransactionState.UNCLEARED,
        description="The transaction state",
    )


class NewTransaction(TransactionBase):
    @field_validator("details", mode="after")
    @classmethod
    def check_details(cls, details: list[Detail]) -> list[Detail]:
        if not details:
            raise ValueError("Details can not be empty")

        if not sum(detail.total.amount for detail in details) == 0:
            raise ValueError("Transaction is not balanced")

        return details


class Transaction(NewTransaction):
    model_config = ConfigDict(
        from_attributes=True,
    )
    id: TransactionUUID
    ledger_id: LedgerUUID

    updated_at: TransactionUpdatedAt
    created_at: TransactionCreatedAt


class UpdateTransaction(BaseModel):
    description: TransactionDescription | None = None
    date_time: TransactionDateTime | None = None
    details: list[Detail] | None = Field(None, description="The transaction details")
    tags: list[str] | None = Field(None, description="The transaction tags")
    state: TransactionState | None = Field(
        None,
        description="The transaction state",
    )
