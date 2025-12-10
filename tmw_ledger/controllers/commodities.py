"""Commodities API controller module."""

from typing import Annotated

import pendulum
from blacksheep import Response, json
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController, delete, get, post, put
from pydantic import UUID7

from tmw_ledger.controllers.base import IfMatch
from tmw_ledger.core.logging import logger
from tmw_ledger.domain.commodities import CommoditiesBL, Commodity, NewCommodity, UpdateCommodity


class Commodities(APIController):
    """API controller for partnerships."""

    @classmethod
    def version(cls) -> str:
        return "v1"

    @auth(roles=["reader"])
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

    @auth(roles=["writer"])
    @post("/{ledger_id}")
    async def add_commodity(
        self,
        commodities: CommoditiesBL,
        ledger_id: UUID7,
        commodity: NewCommodity,
    ) -> Annotated[Response, Commodity]:
        """Add a new commodity.

        Add a new commodity to the ledger.
        """
        new_commodity = await commodities.create(
            ledger_id=ledger_id,
            commodity_code=commodity.code,
            commodity_name=commodity.name,
            commodity_subunit=commodity.subunit,
            commodity_symbol=commodity.symbol,
            commodity_no_market=commodity.no_market,
        )

        response = json(new_commodity)
        response.add_header(
            b"ETag",
            str(new_commodity.updated_at.timestamp()).encode("utf-8"),
        )

        return response

    @auth(roles=["writer"])
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

    @auth(roles=["writer"])
    @put("/{ledger_id}/{commodity_id}")
    async def update_commodity(
        self,
        commodities: CommoditiesBL,
        ledger_id: UUID7,
        commodity_id: UUID7,
        commodity: UpdateCommodity,
        etag: IfMatch | None = None,
    ) -> Annotated[Response, Commodity]:
        """Update commodity.

        Update selected commodity in the ledger.
        """
        try:
            updated_at = (
                # pendulum.from_format(if_unmodified_since.value, "ddd, DD MMM YYYY HH:mm:ss z")
                pendulum.from_timestamp(float(etag.value)) if etag else None
            )
        except ValueError:
            updated_at = None
            logger.debug("Failed to parse ETag header: %s", etag.value if etag else "None")

        updated_commodity = await commodities.update_one(
            ledger_id=ledger_id,
            commodity_id=commodity_id,
            data=commodity,
            updated_at=updated_at,
        )

        response = json(commodity)
        response.add_header(
            b"ETag",
            str(updated_commodity.updated_at.timestamp()).encode("utf-8"),
        )

        return response
