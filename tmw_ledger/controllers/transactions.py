"""Transactions API controller module."""

from asyncio.log import logger
from typing import Annotated

import pendulum
from blacksheep import FromQuery, Response
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController, delete, get, post, put
from essentials.exceptions import ObjectNotFound
from pydantic import BaseModel

from tmw_ledger.controllers.base import IfMatch
from tmw_ledger.domain.ledgers import LedgersBL
from tmw_ledger.domain.transactions import (
    TransactionsBL,
)
from tmw_ledger.domain.types.ledger import LedgerUUID
from tmw_ledger.domain.types.transaction import (
    NewTransaction,
    Transaction,
    TransactionOrdering,
    TransactionUUID,
    UpdateTransaction,
)


class TransactionsPage(BaseModel):
    """Pagination information for transactions."""

    transactions: list[Transaction]
    skip: int
    limit: int
    count: int


class Transactions(APIController):
    """API controller for ledger transactions."""

    @classmethod
    def version(cls) -> str:
        """Show API version."""
        return "v1"

    @auth("authenticated")
    @get("/{ledger_id}")
    async def get_transactions(
        self,
        transactions: TransactionsBL,
        ledger_id: LedgerUUID,
        accounts: FromQuery[list[str]] = FromQuery([]),  # noqa: B008
        after: FromQuery[int | None] = FromQuery(None),  # noqa: B008
        before: FromQuery[int | None] = FromQuery(None),  # noqa: B008
        exchange: FromQuery[bool | None] = FromQuery(None),  # noqa: B008
        skip: FromQuery[int] = FromQuery(0),  # noqa: B008
        limit: FromQuery[int] = FromQuery(20),  # noqa: B008
        order_by: FromQuery[str] = FromQuery("-date_time"),  # noqa: B008
    ) -> TransactionsPage:
        """Get user ledger transactions."""
        # TODO: Add search by tags

        after_dt = pendulum.from_timestamp(after.value) if after.value else None
        before_dt = pendulum.from_timestamp(before.value) if before.value else None

        selected_accounts = accounts.value
        ledger_transactions, count = await transactions.find_ledger_transactions(
            ledger_id=ledger_id,
            accounts=selected_accounts,
            exchange=exchange.value,
            after=after_dt,
            before=before_dt,
            limit=limit.value,
            skip=skip.value,
            order_by=TransactionOrdering(order_by.value),
        )
        return TransactionsPage(
            transactions=ledger_transactions,
            skip=skip.value,
            limit=limit.value,
            count=count,
        )

    @auth("authenticated")
    @get("/{ledger_id}/{transaction_id}")
    async def get_transaction(
        self,
        transactions: TransactionsBL,
        ledger_id: LedgerUUID,
        transaction_id: TransactionUUID,
    ) -> Annotated[Response, Transaction]:
        """Get user ledger transaction."""
        transaction: Transaction = await transactions.get_ledger_transaction(
            ledger_id=ledger_id,
            transaction_id=transaction_id,
        )

        response = self.json(transaction)
        response.add_header(
            b"ETag",
            str(pendulum.instance(transaction.updated_at).timestamp()).encode("utf-8"),
        )

        return response

    @auth("authenticated")
    @post("/{ledger_id}")
    async def add_transaction(
        self,
        ledgers: LedgersBL,
        transactions: TransactionsBL,
        ledger_id: LedgerUUID,
        transaction: NewTransaction,
    ) -> Annotated[Response, Transaction]:
        """Add a new transaction.

        Add a new transaction to the ledger.
        """
        if not await ledgers.exists(ledger_id):
            raise ObjectNotFound("Ledger does not exist.")

        new_transaction = await transactions.create_transaction(
            ledger_id=ledger_id,
            new_transaction=transaction,
        )

        response = self.json(new_transaction)
        response.add_header(
            b"ETag",
            str(new_transaction.updated_at.timestamp()).encode("utf-8"),
        )

        return response

    @auth("authenticated")
    @put("/{ledger_id}/{transaction_id}")
    async def update_transaction(
        self,
        transactions: TransactionsBL,
        ledger_id: LedgerUUID,
        transaction_id: TransactionUUID,
        update_transaction: UpdateTransaction,
        etag: IfMatch | None = None,
    ) -> Annotated[Response, Transaction]:
        """Update transaction.

        Update selected transaction in the ledger.
        """
        try:
            updated_at = pendulum.from_timestamp(float(etag.value)) if etag else None
        except ValueError:
            updated_at = None
            logger.debug("Failed to parse ETag header: %s", etag.value if etag else "None")

        updated_transaction = await transactions.update_transaction(
            ledger_id=ledger_id,
            transaction_id=transaction_id,
            data=update_transaction,
            updated_at=updated_at,
        )

        response = self.json(updated_transaction)
        response.add_header(
            b"ETag",
            str(updated_transaction.updated_at.timestamp()).encode("utf-8"),
        )

        return response

    @auth("authenticated")
    @delete("/{ledger_id}/{transaction_id}")
    async def delete_transaction(
        self,
        transactions: TransactionsBL,
        ledger_id: LedgerUUID,
        transaction_id: TransactionUUID,
        etag: IfMatch | None = None,
    ) -> None:
        """Delete transaction.

        Delete selected transaction from the ledger.
        """
        try:
            updated_at = pendulum.from_timestamp(float(etag.value)) if etag else None
        except ValueError:
            updated_at = None
            logger.debug("Failed to parse ETag header: %s", etag.value if etag else "None")

        await transactions.delete_ledger_transaction(
            ledger_id=ledger_id,
            transaction_id=transaction_id,
            updated_at=updated_at,
        )
