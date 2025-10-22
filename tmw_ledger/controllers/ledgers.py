"""Ledger API controller module."""

from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController, get, post, put
from pydantic import UUID7

from tmw_ledger.domain.ledgers import Ledger, LedgersBL, NewLedger, UpdateLedger


class Ledgers(APIController):
    """API controller for ledgers."""

    @classmethod
    def version(cls) -> str:
        return "v1"

    @auth("authenticated")
    @get("/")
    async def get_ledgers(
        self,
        ledgers: LedgersBL,
    ) -> list[Ledger]:
        """Get ledgers."""
        ledgers = await ledgers.get_all()
        return ledgers

    @auth("authenticated")
    @post("/")
    async def create_partnership(
        self,
        ledgers: LedgersBL,
        new_ledger: NewLedger,
    ) -> Ledger:
        """Create a new ledger."""
        ledger = await ledgers.create(new_ledger.name, new_ledger.description)
        return ledger

    @auth("authenticated")
    @put("/{ledger_id}")
    async def update_partnership(
        self,
        ledgers: LedgersBL,
        ledger_id: UUID7,
        updated_ledger: UpdateLedger,
    ) -> Ledger:
        """Update ledger."""
        ledger = await ledgers.update(ledger_id, updated_ledger)
        return ledger
