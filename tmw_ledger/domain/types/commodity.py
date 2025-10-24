"""Types for the Commodity domain."""

from datetime import datetime
from typing import Annotated, TypeAlias
from uuid import uuid7

from pydantic import UUID7, Field

CommodityName: TypeAlias = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        max_length=256,
        description="The commodity name",
    ),
]

CommodityCode: TypeAlias = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        max_length=8,
        description="The commodity code, like UA, USD, EUR, etc.",
    ),
]

CommoditySymbol: TypeAlias = Annotated[
    str | None,
    Field(
        ...,
        min_length=1,
        max_length=8,
        description="The commodity symbol, like ₴, $, €, etc.",
    ),
]

CommoditySubunit: TypeAlias = Annotated[
    int,
    Field(
        ...,
        ge=1,
        description="The commodity subunit, like 100 for cents",
    ),
]

CommodityIsOnMarket: TypeAlias = Annotated[
    bool,
    Field(
        ...,
        description="The commodity market, like NYSE, NASDAQ, etc.",
    ),
]


CommodityUUID: TypeAlias = Annotated[
    UUID7,
    Field(
        ...,
        description="The commodity unique ID",
        json_schema_extra={
            "format": "uuid",
        },
    ),
]


CommodityUpdatedAt: TypeAlias = Annotated[
    datetime,
    Field(
        ...,
        description="The commodity update time",
        json_schema_extra={
            "format": "date-time",
        },
    ),
]

CommodityCreatedAt: TypeAlias = Annotated[
    datetime,
    Field(
        ...,
        description="The commodity creation time",
        json_schema_extra={
            "format": "date-time",
        },
    ),
]
