from datetime import datetime
from typing import ClassVar, final
from uuid import uuid7

import pendulum
from beanie.odm.operators.update.general import Set
from essentials.exceptions import ConflictException, ObjectNotFound
from pydantic import UUID7, BaseModel, ConfigDict, TypeAdapter
from pymongo.errors import DuplicateKeyError

from tmw_ledger.core.services import add_service
from tmw_ledger.domain.types.commodity import (
    CommodityCode,
    CommodityCreatedAt,
    CommodityIsOnMarket,
    CommodityName,
    CommoditySubunit,
    CommoditySymbol,
    CommodityUpdatedAt,
    CommodityUUID,
)
from tmw_ledger.domain.types.ledger import LedgerUUID
from tmw_ledger.models.commodities import CommodityModel


class CommodityBase(BaseModel):
    name: CommodityName
    code: CommodityCode
    symbol: CommoditySymbol
    subunit: CommoditySubunit = 100
    no_market: CommodityIsOnMarket = False


class NewCommodity(CommodityBase):
    ledger_id: LedgerUUID


class Commodity(NewCommodity):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        from_attributes=True,
    )

    id: CommodityUUID
    created_at: CommodityCreatedAt
    updated_at: CommodityUpdatedAt


class UpdateCommodity(BaseModel):
    name: CommodityName | None
    code: CommodityCode | None
    symbol: CommoditySymbol | None
    subunit: CommoditySubunit | None
    no_market: CommodityIsOnMarket | None

    updated_at: CommodityUpdatedAt


@add_service(scope="scoped")
class CommoditiesDAL:
    async def create(
        self,
        new_commodity: NewCommodity,
    ) -> Commodity:
        commodity = CommodityModel(
            id=uuid7(),
            name=new_commodity.name,
            code=new_commodity.code,
            symbol=new_commodity.symbol,
            subunit=new_commodity.subunit,
            ledger_id=new_commodity.ledger_id,
            no_market=new_commodity.no_market,
        )

        try:
            commodity = await commodity.create()
        except DuplicateKeyError as e:
            raise ConflictException("Duplicate commodity with the same code for the ledger already exists") from e

        return Commodity.model_validate(commodity)

    async def get_by_id(self, commodity_id: CommodityUUID) -> Commodity:
        commodity = await CommodityModel.find_one(
            CommodityModel.id == commodity_id,
            CommodityModel.deleted_at == None,  # noqa E711
        )
        if not commodity:
            raise ObjectNotFound

        return Commodity.model_validate(commodity)

    async def get_ledger_commodity_by_id(
        self,
        ledger_id: LedgerUUID,
        commodity_id: CommodityUUID,
    ) -> Commodity:
        commodity = await CommodityModel.find_one(
            CommodityModel.id == commodity_id,
            CommodityModel.ledger_id == ledger_id,
            CommodityModel.deleted_at == None,  # noqa E711
        )
        if not commodity:
            raise ObjectNotFound

        return Commodity.model_validate(commodity)

    async def get_ledger_commodities(self, ledger_id: LedgerUUID) -> list[Commodity]:
        commodities = await CommodityModel.find(
            CommodityModel.ledger_id == ledger_id,
            CommodityModel.deleted_at == None,  # noqa E711
        ).to_list()
        return TypeAdapter(list[Commodity]).validate_python(commodities)

    async def update_by_id(
        self,
        commodity_id: CommodityUUID,
        update_commodity: UpdateCommodity,
    ) -> Commodity:
        new_data = update_commodity.model_dump(exclude_unset=True, exclude={"id", "updated_at"})
        if not new_data:
            raise ValueError("No data to update")

        try:
            commodity = await CommodityModel.find_one(
                CommodityModel.id == commodity_id,
                CommodityModel.deleted_at == None,  # noqa E711
                CommodityModel.updated_at == update_commodity.updated_at,
            ).update_one(
                Set(new_data),
            )
        except DuplicateKeyError as e:
            raise ConflictException("Duplicate commodity with the same code for the ledger already exists") from e

        if commodity is None:
            raise ObjectNotFound

        return await self.get_by_id(commodity_id)

    async def update_ledger_commodity(
        self,
        ledger_id: LedgerUUID,
        commodity_id: CommodityUUID,
        update_commodity: UpdateCommodity,
    ) -> Commodity:
        new_data = update_commodity.model_dump(exclude_unset=True, exclude={"id", "updated_at"})
        if not new_data:
            raise ValueError("No data to update")

        try:
            commodity = await CommodityModel.find_one(
                CommodityModel.id == commodity_id,
                CommodityModel.ledger_id == ledger_id,
                CommodityModel.deleted_at == None,  # noqa E711
                CommodityModel.updated_at == update_commodity.updated_at,
            ).update_one(
                Set(update_commodity.dict(exclude_unset=True)),
            )
        except DuplicateKeyError as e:
            raise ConflictException("Duplicate commodity with the same code for the ledger already exists") from e

        if commodity is None:
            raise ObjectNotFound

        return await self.get_by_id(commodity_id)

    async def delete_ledger_commodity_by_id(
        self,
        ledger_id: LedgerUUID,
        commodity_id: CommodityUUID,
    ):
        commodity = await CommodityModel.find_one(
            CommodityModel.id == commodity_id,
            CommodityModel.ledger_id == ledger_id,
            CommodityModel.deleted_at == None,  # noqa E711
        ).update_one(
            Set({"deleted_at": pendulum.now()}),
        )
        if not commodity:
            raise ObjectNotFound


@add_service(scope="scoped")
class CommoditiesBL:
    def __init__(self, dal: CommoditiesDAL):
        self.dal = dal

    async def create(
        self,
        commodity_name: str,
        commodity_code: str,
        commodity_symbol: str | None,
        commodity_subunit: int,
        ledger_id: UUID7,
    ) -> Commodity:
        new_commodity = NewCommodity(
            name=commodity_name,
            code=commodity_code,
            symbol=commodity_symbol,
            subunit=commodity_subunit,
            ledger_id=ledger_id,
        )
        return await self.dal.create(new_commodity)

    async def update_by_id(
        self,
        commodity_id: UUID7,
        commodity_updated_at: datetime,
        commodity_name: str | None,
        commodity_code: str | None,
        commodity_symbol: str | None,
        commodity_subunit: int | None,
        commodity_no_market: bool | None,
    ) -> Commodity:
        update_commodity = UpdateCommodity(
            name=commodity_name,
            code=commodity_code,
            symbol=commodity_symbol,
            subunit=commodity_subunit,
            no_market=commodity_no_market,
            updated_at=commodity_updated_at,
        )
        return await self.dal.update_by_id(commodity_id, update_commodity)

    async def update_ledger_commodity(
        self,
        ledger_id: UUID7,
        commodity_id: UUID7,
        commodity_updated_at: datetime,
        commodity_name: str | None,
        commodity_code: str | None,
        commodity_symbol: str | None,
        commodity_subunit: int | None,
        commodity_no_market: bool | None,
    ) -> Commodity:
        update_commodity = UpdateCommodity(
            name=commodity_name,
            code=commodity_code,
            symbol=commodity_symbol,
            subunit=commodity_subunit,
            no_market=commodity_no_market,
            updated_at=commodity_updated_at,
        )
        return await self.dal.update_ledger_commodity(ledger_id, commodity_id, update_commodity)

    async def get_ledger_commodities(self, ledger_id: UUID7) -> list[Commodity]:
        return await self.dal.get_ledger_commodities(ledger_id=ledger_id)

    async def delete_ledger_commodity(
        self,
        ledger_id: UUID7,
        commodity_id: UUID7,
    ):
        await self.dal.delete_ledger_commodity_by_id(
            ledger_id=ledger_id,
            commodity_id=commodity_id,
        )
