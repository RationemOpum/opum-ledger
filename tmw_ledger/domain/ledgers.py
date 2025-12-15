from typing import ClassVar
from uuid import uuid7

import pendulum
from beanie import UpdateResponse
from beanie.odm.operators.update.general import Set
from beanie.odm.queries.find import FindOne
from essentials.exceptions import ConflictException, ObjectNotFound
from pendulum import DateTime
from pydantic import UUID7, BaseModel, ConfigDict
from pymongo.errors import DuplicateKeyError
from pymongo.results import UpdateResult

from tmw_ledger.core.exceptions import PreconditionFailed
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
    name: LedgerName | None = None
    description: LedgerDescription | None = None


@add_service(scope="scoped")
class LedgersDAL:
    async def create_ledger(
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

    async def get_ledgers(self) -> list[Ledger]:
        ledgers = await LedgerModel.find_many(
            LedgerModel.deleted_at == None,  # noqa E711
        ).to_list()
        return [Ledger.model_validate(ledger) for ledger in ledgers]

    async def get_ledger(self, ledger_id: UUID7) -> Ledger:
        ledger = await LedgerModel.find_one(
            LedgerModel.id == ledger_id,
            LedgerModel.deleted_at == None,  # noqa E711
        )
        if ledger is None:
            raise ObjectNotFound("Ledger not found")

        return Ledger.model_validate(ledger)

    async def update_ledger(
        self,
        ledger_id: UUID7,
        data: UpdateLedger,
        updated_at: DateTime | None = None,
    ) -> Ledger:
        new_data = data.model_dump(exclude_unset=True)
        if not new_data:
            raise ValueError("No data to update")

        ledger_query: FindOne = LedgerModel.find_one(  # pyright: ignore[reportUnusedCallResult]
            LedgerModel.id == ledger_id,
            LedgerModel.deleted_at == None,  # noqa E711
        )
        ledger = await ledger_query

        if ledger is None:
            raise ObjectNotFound("Ledger not found")

        if updated_at and pendulum.instance(ledger.updated_at) > updated_at:
            raise PreconditionFailed(f"Ledger has been modified since {updated_at}")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = pendulum.now("UTC")

        if updated_at is not None:
            ledger_query = ledger_query.find_one(LedgerModel.updated_at == updated_at)

        update_result: UpdateResult = await ledger_query.update(  # pyright: ignore[reportGeneralTypeIssues]
            Set(update_data),
            response_type=UpdateResponse.UPDATE_RESULT,
        )

        if update_result.matched_count == 0:
            raise PreconditionFailed(f"Ledger has been modified since {updated_at}")

        return await self.get_ledger(ledger_id)

    async def exists(self, ledger_id: UUID7) -> bool:
        return await LedgerModel.find(LedgerModel.id == ledger_id).exists()


@add_service(scope="scoped")
class LedgersBL:
    def __init__(self, dal: LedgersDAL):
        self.dal = dal

    async def create_ledger(
        self,
        name: str,
        description: str | None = None,
    ) -> Ledger:
        new_ledger = NewLedger(
            name=name,
            description=description,
        )
        ledger = await self.dal.create_ledger(new_ledger)
        return ledger

    async def get_ledgers(self) -> list[Ledger]:
        ledgers = await self.dal.get_ledgers()
        return ledgers

    async def get_ledger(self, id_: UUID7) -> Ledger:
        return await self.dal.get_ledger(id_)

    async def exists(self, ledger_id: UUID7) -> bool:
        return await self.dal.exists(ledger_id)

    async def update_ledger(
        self,
        ledger_id: UUID7,
        data: UpdateLedger,
        updated_at: DateTime | None = None,
    ) -> Ledger:
        return await self.dal.update_ledger(
            ledger_id,
            data,
            updated_at,
        )
