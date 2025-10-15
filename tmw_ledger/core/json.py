"""Configuration for JSON serialization via orjson."""

import base64
from decimal import Decimal
from typing import Any

import orjson
from blacksheep.settings.json import json_settings
from pendulum import Date, DateTime, Time
from pydantic import BaseModel


def default(obj: Any) -> dict[str, Any] | str | bytes:  # pyright: ignore[reportExplicitAny, reportAny]
    """Set default serialize function for JSON serialization via orjson.

    Args:
        obj: The object to serialize.

    Returns:
        The serialized object.

    """
    if isinstance(obj, BaseModel) and hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, BaseModel) and hasattr(obj, "dict"):
        return obj.dict()  # pyright: ignore[reportDeprecated]
    if isinstance(obj, Time):
        return obj.strftime("%H:%M:%S")
    if isinstance(obj, DateTime):
        return obj.isoformat()
    if isinstance(obj, Date):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, bytes):
        return base64.urlsafe_b64encode(obj)
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, Exception):
        return str(obj)

    raise TypeError


def dumps(obj: Any) -> str:  # pyright: ignore[reportExplicitAny, reportAny]
    """Reload dumps."""
    return orjson.dumps(obj, default=default).decode("utf8")


def pretty_dumps(obj: Any) -> str:  # pyright: ignore[reportExplicitAny, reportAny]
    """Reload pretty dumps."""
    return orjson.dumps(obj, default=default, option=orjson.OPT_INDENT_2).decode("utf8")


def loads(obj: str) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
    """Reload loads."""
    return orjson.loads(obj)  # pyright: ignore[reportAny]


def use_orjson() -> None:
    """Enable orjson for JSON serialization."""
    json_settings.use(  # pyright: ignore[reportUnknownMemberType]
        loads=loads,
        dumps=dumps,
        pretty_dumps=pretty_dumps,
    )
