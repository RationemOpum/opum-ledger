"""Types for the Commodity domain."""

from datetime import datetime
from typing import Annotated
from uuid import uuid7

from pydantic import UUID7, Field

type CommodityName = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        max_length=256,
        description="The commodity name",
    ),
]

type CommodityCode = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        max_length=8,
        description="The commodity code, like UA, USD, EUR, etc.",
    ),
]

type CommoditySymbol = Annotated[
    str | None,
    Field(
        ...,
        min_length=1,
        max_length=8,
        description="The commodity symbol, like ₴, $, €, etc.",
    ),
]

type CommoditySubunit = Annotated[
    int,
    Field(
        ...,
        ge=1,
        description="The commodity subunit, like 100 for cents",
    ),
]

type CommodityIsOnMarket = Annotated[
    bool,
    Field(
        ...,
        description="The commodity market, like NYSE, NASDAQ, etc.",
    ),
]


type CommodityUUID = Annotated[
    UUID7,
    Field(
        ...,
        description="The commodity unique ID",
        json_schema_extra={
            "format": "uuid",
        },
    ),
]


type CommodityUpdatedAt = Annotated[
    datetime,
    Field(
        ...,
        description="The commodity update time",
        json_schema_extra={
            "format": "date-time",
        },
    ),
]

type CommodityCreatedAt = Annotated[
    datetime,
    Field(
        ...,
        description="The commodity creation time",
        json_schema_extra={
            "format": "date-time",
        },
    ),
]
