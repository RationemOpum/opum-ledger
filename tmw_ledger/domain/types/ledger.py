"""Types for the Ledger domain."""

from datetime import datetime
from typing import Annotated, TypeAlias

from pydantic import UUID7, Field

LedgerUUID: TypeAlias = Annotated[
    UUID7,
    Field(
        ...,
        description="The ledger unique ID",
        json_schema_extra={
            "format": "uuid",
        },
    ),
]


LedgerName: TypeAlias = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        max_length=256,
        description="The ledger name",
        json_schema_extra={
            "format": "string",
        },
    ),
]

LedgerDescription: TypeAlias = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        max_length=1024,
        description="The ledger description",
        json_schema_extra={
            "format": "string",
        },
    ),
]

LedgerCreatedAt: TypeAlias = Annotated[
    datetime,
    Field(
        ...,
        description="The ledger creation date",
        json_schema_extra={
            "format": "date-time",
        },
    ),
]

LedgerUpdatedAt: TypeAlias = Annotated[
    datetime,
    Field(
        ...,
        description="The ledger update date",
        json_schema_extra={
            "format": "date-time",
        },
    ),
]
