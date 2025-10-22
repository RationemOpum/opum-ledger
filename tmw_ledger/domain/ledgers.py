from datetime import datetime
from typing import Annotated, ClassVar, final
from uuid import uuid7

from beanie.odm.operators.update.general import Set
from essentials.exceptions import ConflictException
from pydantic import UUID7, BaseModel, ConfigDict, Field
from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from tmw_ledger.core.services import add_service
from tmw_ledger.domain.types.ledger import LedgerCreatedAt, LedgerDescription, LedgerName, LedgerUpdatedAt, LedgerUUID
from tmw_ledger.models.ledger import LedgerModel


class NewLedger(BaseModel):
    name: LedgerName
    description: LedgerDescription | None = None


class Ledger(NewLedger):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True,
    )

    id: LedgerUUID
    created_at: LedgerCreatedAt
    updated_at: LedgerUpdatedAt


class UpdateLedger(BaseModel):
    name: LedgerName | None
    description: LedgerDescription | None
    updated_at: LedgerUpdatedAt


@add_service(scope="scoped")
class LedgersDAL:
    async def create(
        self,
        new_ledger: NewLedger,
    ) -> Ledger:
        ledger = LedgerModel(
            id=uuid7(),
            name=new_ledger.name,
            description=new_ledger.description,
        )
        try:
            ledger = await ledger.create()
        except DuplicateKeyError as e:
            raise ConflictException("Duplicate ledger name already exists") from e

        return Ledger.model_validate(ledger)

    async def get_all(self) -> list[Ledger]:
        ledgers = await LedgerModel.find_many(
            LedgerModel.deleted_at == None,  # noqa E711
        ).to_list()
        return [Ledger.model_validate(ledger) for ledger in ledgers]

    async def get_by_id(self, ledger_id: UUID7) -> Ledger:
        ledger = await LedgerModel.find_one(
            LedgerModel.id == ledger_id,
            LedgerModel.deleted_at == None,  # noqa E711
        )
        return Ledger.model_validate(ledger)

    async def update(self, ledger_id: UUID7, ledger: UpdateLedger) -> Ledger:
        await LedgerModel.find_one(  # pyright: ignore[reportUnusedCallResult]
            LedgerModel.id == ledger_id,
            LedgerModel.deleted_at == None,  # noqa E711
        ).update_one(
            Set(ledger.model_dump(exclude_unset=True, exclude={"id"})),
        )
        return await self.get_by_id(ledger_id)


@add_service(scope="scoped")
class LedgersBL:
    def __init__(self, dal: LedgersDAL):
        self.dal = dal

    async def create(
        self,
        name: str,
        description: str | None = None,
    ) -> Ledger:
        new_ledger = NewLedger(
            name=name,
            description=description,
        )
        ledger = await self.dal.create(new_ledger)
        return ledger

    async def get_all(self) -> list[Ledger]:
        ledgers = await self.dal.get_all()
        return ledgers

    async def get_by_id(self, id_: UUID7) -> Ledger:
        return await self.dal.get_by_id(id_)

    async def update_by_id(self, id_: UUID7, data: UpdateLedger) -> Ledger:
        return await self.dal.update(id_, data)
