"""Accounts API controller module."""

from dataclasses import dataclass
from typing import Annotated

import pendulum
from blacksheep import Response, json
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController, delete, get, post, put
from pydantic import RootModel

from tmw_ledger.controllers.base import IfMatch
from tmw_ledger.core.logging import logger
from tmw_ledger.domain.accounts import Account, AccountsBL, AccountUpdate, NewAccount
from tmw_ledger.domain.types.account import AccountUUID
from tmw_ledger.domain.types.ledger import LedgerUUID


@dataclass
class AccountsResponse:
    """Accounts response."""

    accounts: list[Account]


AccountsTree = RootModel[dict[str, list[Account]]]


class Accounts(APIController):
    """API controller for accounts."""

    @classmethod
    def version(cls) -> str:
        return "v1"

    @auth("authenticated")
    @get("/{ledger_id}")
    async def get_accounts(
        self,
        accounts: AccountsBL,
        ledger_id: LedgerUUID,
    ) -> AccountsResponse:
        """Get ledger accounts.

        This handler returns a list of accounts for the ledger.
        """
        ledger_accounts = await accounts.get_ledger_accounts(ledger_id)
        return AccountsResponse(accounts=ledger_accounts)

    @auth("authenticated")
    @post("/{ledger_id}")
    async def add_account(
        self,
        accounts: AccountsBL,
        ledger_id: LedgerUUID,
        new_account: NewAccount,
    ) -> Annotated[Response, Account]:
        """Add a new account.

        Add a new account to the ledger.
        """
        account = await accounts.create(
            ledger_id=ledger_id,
            new_account=new_account,
        )

        # Return JSON response with ETag header (timestamp of updated_at)
        response = json(account)
        response.add_header(
            b"ETag",
            str(account.updated_at.timestamp()).encode("utf-8"),
        )

        # TODO: Should be an open balance transaction here?

        return response

    @auth("authenticated")
    @delete("/{ledger_id}/{account_id}")
    async def delete_account(
        self,
        accounts: AccountsBL,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
        etag: IfMatch | None = None,
    ) -> None:
        """Delete the account.

        Delete a selected account from the ledger.
        """
        try:
            updated_at = (
                # pendulum.from_format(if_unmodified_since.value, "ddd, DD MMM YYYY HH:mm:ss z")
                pendulum.from_timestamp(float(etag.value)) if etag else None
            )
        except ValueError:
            updated_at = None
            logger.debug("Failed to parse ETag header: %s", etag.value if etag else "None")

        await accounts.delete_ledger_account(
            ledger_id=ledger_id,
            account_id=account_id,
            updated_at=updated_at,
        )
        # TODO: Should be a close balance transaction here?

    @auth("authenticated")
    @get("/{ledger_id}/{account_id}")
    async def get_account(
        self,
        accounts: AccountsBL,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
    ) -> Account:
        """Get the account.

        Get a selected account from the ledger.
        """
        return await accounts.get_ledger_account(
            ledger_id=ledger_id,
            account_id=account_id,
        )

    @auth("authenticated")
    @put("/{ledger_id}/{account_id}")
    async def update_account(
        self,
        accounts: AccountsBL,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
        account: AccountUpdate,
        etag: IfMatch | None = None,
    ) -> Annotated[Response, Account]:
        """Update the account.

        Update a selected account in the ledger.
        """
        try:
            updated_at = pendulum.from_timestamp(float(etag.value)) if etag else None
        except ValueError:
            updated_at = None
            logger.debug("Failed to parse ETag header: %s", etag.value if etag else "None")

        updated_account = await accounts.update_ledger_account(
            ledger_id=ledger_id,
            account_id=account_id,
            updated_account=account,
            updated_at=updated_at,
        )

        response = json(updated_account)
        response.add_header(
            b"ETag",
            str(updated_account.updated_at.timestamp()).encode("utf-8"),
        )

        return response

    @auth("authenticated")
    @get("/tree/{ledger_id}")
    async def get_accounts_tree(
        self,
        accounts: AccountsBL,
        ledger_id: LedgerUUID,
    ) -> dict[str, list[Account]]:
        """Get ledger accounts tree.

        This handler returns a tree of accounts for the ledger.
        """
        tree = await accounts.get_ledger_accounts_tree(ledger_id)
        return tree
