from pydantic import Field

from tmw_ledger.domain.types.ledger import LedgerUUID
from tmw_ledger.domain.types.transaction import (
    Detail,
    TransactionDateTime,
    TransactionDescription,
    TransactionState,
    TransactionUUID,
)
from tmw_ledger.models.base import BaseAppModel


class TransactionModel(BaseAppModel):
    id: TransactionUUID  #  pyright: ignore[reportGeneralTypeIssues,reportIncompatibleVariableOverride]
    date_time: TransactionDateTime
    description: TransactionDescription
    details: list[Detail] = Field(default_factory=list)
    # TODO: make tags as a list of UUID4
    tags: list[str] = Field(default_factory=list)
    state: TransactionState = Field(TransactionState.UNCLEARED)
    ledger_id: LedgerUUID

    class Settings:
        name = "transactions"
