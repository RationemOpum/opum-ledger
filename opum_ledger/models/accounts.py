from pymongo import IndexModel

from opum_ledger.core.utils import split_path
from opum_ledger.domain.types.account import AccountName, AccountPath, AccountPaths, AccountUUID
from opum_ledger.domain.types.ledger import LedgerUUID
from opum_ledger.models.base import BaseAppModel


class AccountModel(BaseAppModel):
    id: AccountUUID  # pyright: ignore[reportIncompatibleVariableOverride,reportGeneralTypeIssues]
    name: AccountName
    path: AccountPath
    paths: AccountPaths
    ledger_id: LedgerUUID

    class Settings:
        name = "accounts"
        indexes: list[IndexModel] = [IndexModel(["ledger_id", "path", "name"], unique=True)]

    @classmethod
    def parse_path(cls, path: AccountPath) -> list[AccountPath]:
        return split_path(path)
