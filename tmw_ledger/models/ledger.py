from uuid import uuid7

from pydantic import UUID7, Field

from tmw_ledger.models.base import BaseAppModel


class LedgerModel(BaseAppModel):
    """Ledger model."""

    id: UUID7 = Field(default_factory=uuid7)  # pyright: ignore[reportIncompatibleVariableOverride]
    name: str = Field(..., min_length=1, max_length=256)

    class Settings:
        name: str = "ledgers"
