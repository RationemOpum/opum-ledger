# from datetime import datetime
from uuid import uuid7

from pydantic import UUID7, Field

from tmw_ledger.models.base import BaseAppModel


class CommodityModel(BaseAppModel):
    """Commodities model."""

    id: UUID7 = Field(default_factory=uuid7)  # pyright: ignore[reportIncompatibleVariableOverride]
    name: str = Field(..., min_length=1, max_length=256)
    code: str = Field(..., min_length=1, max_length=8)
    symbol: str | None = Field(..., min_length=1, max_length=8)
    subunit: int = Field(100, ge=1)
    no_market: bool = Field(True)
    ledger_id: UUID7

    class Settings:
        name: str = "commodities"
