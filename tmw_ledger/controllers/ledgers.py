"""Ledger API controller module."""

from typing import Annotated

import pendulum
from blacksheep import Response, json
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController, get, post, put
from pydantic import UUID7

from tmw_ledger.controllers.base import IfMatch
from tmw_ledger.core.logging import logger
from tmw_ledger.domain.ledgers import Ledger, LedgersBL, NewLedger, UpdateLedger


class Ledgers(APIController):
    """API controller for ledgers."""

    @classmethod
    def version(cls) -> str:
        """Return API version."""
        return "v1"

    @auth(roles=["reader"])
    @get("/")
    async def get_all(
        self,
        ledgers: LedgersBL,
    ) -> list[Ledger]:
        """Get ledgers."""
        all_ledgers = await ledgers.get_all()
        return all_ledgers

    @auth(roles=["reader"])
    @get("/{ledger_id}")
    async def get_one(
        self,
        ledgers: LedgersBL,
        ledger_id: UUID7,
    ) -> Annotated[Response, Ledger]:
        """Get a single ledger by ID."""
        ledger = await ledgers.get_one(ledger_id)
        response = json(ledger)
        response.add_header(
            b"ETag",
            str(ledger.updated_at.timestamp()).encode("utf-8"),
        )
        return response

    @auth(roles=["writer"])
    @post("/")
    async def create(
        self,
        ledgers: LedgersBL,
        new_ledger: NewLedger,
    ) -> Annotated[Response, Ledger]:
        """Create a new ledger."""
        ledger = await ledgers.create(new_ledger.name, new_ledger.description)
        response = json(ledger)
        response.add_header(
            b"ETag",
            str(ledger.updated_at.timestamp()).encode("utf-8"),
        )
        return response

    @auth(roles=["writer"])
    @put("/{ledger_id}")
    async def update_one(
        self,
        ledgers: LedgersBL,
        ledger_id: UUID7,
        updated_ledger: UpdateLedger,
        etag: IfMatch | None = None,
    ) -> Annotated[Response, Ledger]:
        """Update ledger."""
        try:
            updated_at = (
                # pendulum.from_format(if_unmodified_since.value, "ddd, DD MMM YYYY HH:mm:ss z")
                pendulum.from_timestamp(float(etag.value)) if etag else None
            )
        except ValueError:
            updated_at = None
            logger.debug("Failed to parse ETag header: %s", etag.value if etag else "None")

        ledger = await ledgers.update_one(
            ledger_id,
            updated_ledger,
            updated_at=updated_at,
        )
        response = json(ledger)
        response.add_header(
            b"ETag",
            str(ledger.updated_at.timestamp()).encode("utf-8"),
        )
        return response
