from pymongo import IndexModel

from tmw_ledger.domain.types.commodity import (
    CommodityCode,
    CommodityIsOnMarket,
    CommodityName,
    CommoditySubunit,
    CommoditySymbol,
    CommodityUUID,
)
from tmw_ledger.domain.types.ledger import LedgerUUID
from tmw_ledger.models.base import BaseAppModel


class CommodityModel(BaseAppModel):
    """Commodities model."""

    id: CommodityUUID  # pyright: ignore[reportIncompatibleVariableOverride,reportGeneralTypeIssues]
    name: CommodityName
    code: CommodityCode
    symbol: CommoditySymbol
    subunit: CommoditySubunit
    no_market: CommodityIsOnMarket
    ledger_id: LedgerUUID

    class Settings:
        name: str = "commodities"
        indexes: list[IndexModel] = [IndexModel(["ledger_id", "code"], unique=True)]
