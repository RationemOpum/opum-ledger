"""Commodities API controller module."""

from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController, delete, get, post, put
from pydantic import UUID7

from tmw_ledger.domain.commodities import CommoditiesBL, Commodity, NewCommodity, UpdateCommodity


class Commodities(APIController):
    """API controller for partnerships."""

    @classmethod
    def version(cls) -> str:
        return "v1"

    @auth("authenticated")
    @get("/{ledger_id}")
    async def get_commodities(
        self,
        commodities: CommoditiesBL,
        ledger_id: UUID7,
    ) -> list[Commodity]:
        """Get ledger commodities.

        This handler returns a list of commodities for the partnership.
        """
        partnership_commodities: list[Commodity] = await commodities.get_ledger_commodities(ledger_id)
        return partnership_commodities

    @auth("authenticated")
    @post("/{ledger_id}")
    async def add_commodity(
        self,
        commodities: CommoditiesBL,
        ledger_id: UUID7,
        commodity: NewCommodity,
    ) -> Commodity:
        """Add a new commodity.

        Add a new commodity to the ledger.
        """
        new_commodity = await commodities.create(
            commodity_code=commodity.code,
            commodity_name=commodity.name,
            commodity_symbol=commodity.symbol,
            ledger_id=ledger_id,
        )
        return new_commodity

    @auth("authenticated")
    @delete("/{ledger_id}/{commodity_id}")
    async def delete_commodity(
        self,
        commodities: CommoditiesBL,
        ledger_id: UUID7,
        commodity_id: UUID7,
    ) -> None:
        """Delete a commodity.

        Delete a commodity from the ledger.
        You can not delete a commodity if it is used in a transaction.
        """
        await commodities.delete_ledger_commodity(
            ledger_id=ledger_id,
            commodity_id=commodity_id,
        )

    @auth("authenticated")
    @put("/{ledger_id}/{commodity_id}")
    async def update_commodity(
        self,
        commodities: CommoditiesBL,
        ledger_id: UUID7,
        commodity_id: UUID7,
        commodity: UpdateCommodity,
    ):
        """Update commodity.

        Update selected commodity in the ledger.
        """
        await commodities.update_ledger_commodity(
            ledger_id=ledger_id,
            commodity_id=commodity_id,
            commodity_updated_at=UpdateCommodity.updated_at,
            commodity_code=commodity.code,
            commodity_name=commodity.name,
            commodity_symbol=commodity.symbol,
            commodity_subunit=commodity.subunit,
            commodity_no_market=commodity.no_market,
        )
