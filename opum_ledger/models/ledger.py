from pymongo import IndexModel

from opum_ledger.domain.types.ledger import LedgerDescription, LedgerName, LedgerUUID
from opum_ledger.models.base import BaseAppModel


class LedgerModel(BaseAppModel):
    """Ledger model."""

    id: LedgerUUID  # pyright: ignore[reportGeneralTypeIssues,reportIncompatibleVariableOverride]
    name: LedgerName
    description: LedgerDescription | None = None

    class Settings:
        name: str = "ledgers"
        indexes: list[IndexModel] = [IndexModel(["name"], unique=True)]
