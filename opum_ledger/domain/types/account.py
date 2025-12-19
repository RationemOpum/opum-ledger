from typing import Annotated, TypeAlias

from pydantic import UUID7, Field

AccountUUID: TypeAlias = Annotated[
    UUID7,
    Field(
        ...,
        description="The account unique ID",
        json_schema_extra={
            "format": "uuid",
        },
    ),
]


AccountName: TypeAlias = Annotated[
    str,
    Field(
        ...,
        min_length=1,
        max_length=256,
        description="The account name",
    ),
]

AccountPath: TypeAlias = Annotated[
    str,
    Field(
        ...,
        description="The account path",
    ),
]


AccountPaths: TypeAlias = Annotated[
    list[AccountPath],
    Field(
        default_factory=list,
        description="The list of account paths",
    ),
]
