from datetime import datetime
from typing import Any, Literal
from uuid import uuid7

import pendulum
from beanie import UpdateResponse
from beanie.odm.operators.find.array import All, ElemMatch
from beanie.odm.operators.find.logical import Not
from beanie.odm.operators.update.general import Set
from beanie.odm.queries.find import FindMany
from essentials.exceptions import ObjectNotFound
from pydantic import (
    UUID7,
    TypeAdapter,
)
from pymongo.results import UpdateResult

from tmw_ledger.core.exceptions import PreconditionFailed
from tmw_ledger.core.services import add_service
from tmw_ledger.domain.accounts import AccountsBL
from tmw_ledger.domain.types.account import AccountUUID
from tmw_ledger.domain.types.ledger import LedgerUUID
from tmw_ledger.domain.types.transaction import (
    AccountBalance,
    NewTransaction,
    Transaction,
    TransactionOrdering,
    TransactionState,
    TransactionUUID,
    UpdateTransaction,
)
from tmw_ledger.models.transactions import TransactionModel


@add_service(scope="scoped")
class TransactionsDAL:
    __model__ = TransactionModel

    async def create_transaction(
        self,
        ledger_id: LedgerUUID,
        new_transaction: NewTransaction,
    ) -> Transaction:
        transaction = TransactionModel(
            id=uuid7(),
            ledger_id=ledger_id,
            date_time=new_transaction.date_time,
            description=new_transaction.description,
            details=new_transaction.details,
            tags=new_transaction.tags,
            state=new_transaction.state,
        )

        await transaction.create()
        return await self.get_transaction(transaction.id)

    async def get_transaction(
        self,
        transaction_id: TransactionUUID,
    ) -> Transaction:
        transaction = await TransactionModel.find_one(
            TransactionModel.id == transaction_id,
            TransactionModel.deleted_at == None,  # noqa E711
        )
        if transaction is None:
            raise ObjectNotFound(f"Transaction id {transaction_id} not found")

        return Transaction.model_validate(transaction, from_attributes=True)

    async def get_ledger_transaction(
        self,
        ledger_id: LedgerUUID,
        transaction_id: TransactionUUID,
    ) -> Transaction:
        transaction = await TransactionModel.find_one(
            TransactionModel.id == transaction_id,
            TransactionModel.ledger_id == ledger_id,
            TransactionModel.deleted_at == None,  # noqa E711
        )
        if transaction is None:
            raise ObjectNotFound(f"Transaction id {transaction_id} not found")

        return Transaction.model_validate(transaction, from_attributes=True)

    async def find_ledger_transactions(
        self,
        ledger_id: LedgerUUID,
        # accounts_ids: list[UUID4] | None = None,
        accounts_ids: list[tuple[Literal["=", "-", "+"], UUID7]] | None = None,
        tags: list[str] | None = None,
        state: TransactionState | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
        exchange: bool | None = None,
        limit: int = 20,
        skip: int = 0,
        order_by: TransactionOrdering = TransactionOrdering.DATE_TIME_DESC,
    ) -> tuple[list[Transaction], int]:
        request: FindMany[TransactionModel] = TransactionModel.find(
            TransactionModel.ledger_id == ledger_id,
            TransactionModel.deleted_at == None,  # noqa E711
        ).sort(order_by.value)
        if after:
            request = request.find(
                TransactionModel.date_time >= after,
            )
        if before:
            request = request.find(
                TransactionModel.date_time < before,
            )
        if tags:
            request = request.find(
                All(TransactionModel.tags, tags),
            )
        if state:
            request = request.find(
                TransactionModel.state == state,
            )
        if exchange is True:
            request = request.find(
                # {"details": {"$elemMatch": {"price": {"$ne": None}}}},
                ElemMatch(
                    TransactionModel.details,
                    {"price": {"$ne": None}},
                ),
            )
        if exchange is False:
            request = request.find(
                # {$not :{"details": {"$elemMatch": {"price": None}}}},
                Not(
                    ElemMatch(
                        TransactionModel.details,
                        {"price": {"$ne": None}},
                    )
                ),
            )
        accounts_filters: dict[Literal["+", "-", "="], list[dict[str, Any]]] = {
            "+": [],
            "-": [],
            "=": [],
        }
        for account_type, account_id in accounts_ids or []:
            if account_type == "+":
                accounts_filters["+"].append(
                    {
                        "details": {
                            "$elemMatch": {
                                "account_id": account_id,
                                "amount.amount": {"$gt": 0},
                            }
                        }
                    }
                )
            elif account_type == "-":
                accounts_filters["-"].append(
                    {
                        "details": {
                            "$elemMatch": {
                                "account_id": account_id,
                                "amount.amount": {"$lt": 0},
                            }
                        }
                    }
                )
            elif account_type == "=":
                accounts_filters["="].append(
                    {
                        "details": {
                            "$elemMatch": {
                                "account_id": account_id,
                            }
                        }
                    }
                )
        compiled_filters = {"$and": []}
        if accounts_filters["+"]:
            compiled_filters["$and"].append(
                {
                    "$or": accounts_filters["+"],
                },
            )
        if accounts_filters["-"]:
            compiled_filters["$and"].append(
                {
                    "$or": accounts_filters["-"],
                },
            )
        if accounts_filters["="]:
            compiled_filters["$and"].append(
                {
                    "$or": accounts_filters["="],
                },
            )
        if compiled_filters["$and"]:
            request = request.find(compiled_filters)
        count = await request.count()
        request = request.skip(skip).limit(limit)
        transactions: list[TransactionModel] = await request.to_list()

        return TypeAdapter(list[Transaction]).validate_python(transactions, from_attributes=True), count

    async def update_ledger_transaction(
        self,
        ledger_id: LedgerUUID,
        transaction_id: TransactionUUID,
        data: UpdateTransaction,
        updated_at: pendulum.DateTime | None = None,
    ) -> Transaction:
        transaction_query = TransactionModel.find_one(
            TransactionModel.id == transaction_id,
            TransactionModel.ledger_id == ledger_id,
            TransactionModel.deleted_at == None,  # noqa E711
        )
        transaction = await transaction_query
        if not transaction:
            raise ObjectNotFound("Transaction not found.")

        if updated_at and pendulum.instance(transaction.updated_at) > updated_at:
            raise PreconditionFailed("Transaction has been modified since the provided timestamp.")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = pendulum.now("UTC")

        if updated_at is not None:
            transaction_query = transaction_query.find_one(
                TransactionModel.updated_at == updated_at,
            )

        update_result: UpdateResult = await transaction_query.update(  # pyright: ignore[reportGeneralTypeIssues]
            Set(update_data),
            response_type=UpdateResponse.UPDATE_RESULT,
        )

        if update_result.matched_count == 0:
            raise PreconditionFailed("Transaction has been modified since the provided timestamp.")

        return await self.get_transaction(transaction_id)

    async def delete_ledger_transaction(
        self,
        ledger_id: LedgerUUID,
        transaction_id: TransactionUUID,
        updated_at: pendulum.DateTime | None = None,
    ):
        transaction_query = TransactionModel.find_one(
            TransactionModel.id == transaction_id,
            TransactionModel.ledger_id == ledger_id,
            TransactionModel.deleted_at == None,  # noqa E711
        )
        transaction = await transaction_query
        if not transaction:
            raise ObjectNotFound("Transaction not found.")

        if updated_at and pendulum.instance(transaction.updated_at) > updated_at:
            raise PreconditionFailed("Transaction has been modified since the provided timestamp.")

        if updated_at is not None:
            transaction_query = transaction_query.find_one(
                TransactionModel.updated_at == updated_at,
            )

        update_result: UpdateResult = await transaction_query.update(  # pyright: ignore[reportGeneralTypeIssues]
            Set({"deleted_at": pendulum.now("UTC")}),
            response_type=UpdateResponse.UPDATE_RESULT,
        )

        if update_result.matched_count == 0:
            raise PreconditionFailed("Transaction has been modified since the provided timestamp.")

    async def get_ledger_account_balance(
        self,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
    ) -> list[AccountBalance]:
        aggregation = TransactionModel.aggregate(
            projection_model=AccountBalance,
            aggregation_pipeline=[
                {
                    "$match": {
                        "ledger_id": ledger_id,
                        "details.account_id": account_id,
                    }
                },
                {
                    "$unwind": "$details",
                },
                {
                    "$match": {
                        "details.account_id": account_id,
                    }
                },
                {
                    "$group": {
                        "_id": "$details.amount.commodity_id",
                        "balance": {"$sum": "$details.amount.amount"},
                    }
                },
            ],
        )
        total: list[AccountBalance] = await aggregation.to_list()
        return total


@add_service(scope="scoped")
class TransactionsBL:
    def __init__(
        self,
        dal: TransactionsDAL,
        accounts: AccountsBL,
    ):
        self.dal: TransactionsDAL = dal
        self.accounts: AccountsBL = accounts

    @staticmethod
    def group_accounts(accounts: list[str] | None) -> dict[Literal["+", "-", "="], list[str]]:
        """Group accounts by source and destination.

        Account with minus sign is a source account and account with plus sign is a destination account.
        Account with no sign or equal sign is a source and destination account.

        If accounts is empty, return dict with empty lists.

        Args:
            accounts (list[str] | None): List of account names.

        """
        grouped_accounts: dict[Literal["+", "-", "="], list[str]] = {
            "+": [],
            "-": [],
            "=": [],
        }
        if not accounts:
            return grouped_accounts

        for account in accounts:
            if account.startswith("+"):
                grouped_accounts["+"].append(account[1:])
            elif account.startswith("-"):
                grouped_accounts["-"].append(account[1:])
            elif account.startswith("="):
                grouped_accounts["="].append(account[1:])
            else:
                grouped_accounts["="].append(account)

        return grouped_accounts

    async def create_transaction(
        self,
        ledger_id: LedgerUUID,
        new_transaction: NewTransaction,
    ) -> Transaction:
        return await self.dal.create_transaction(
            ledger_id=ledger_id,
            new_transaction=new_transaction,
        )

    async def update_ledger_transaction(
        self,
        ledger_id: LedgerUUID,
        transaction_id: TransactionUUID,
        data: UpdateTransaction,
        updated_at: pendulum.DateTime | None = None,
    ) -> Transaction:
        transaction = await self.dal.update_ledger_transaction(
            ledger_id=ledger_id,
            transaction_id=transaction_id,
            data=data,
            updated_at=updated_at,
        )

        return transaction

    async def find_ledger_transactions(
        self,
        ledger_id: LedgerUUID,
        accounts: list[str] | None = None,
        tags: list[str] | None = None,
        state: TransactionState | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
        exchange: bool | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: TransactionOrdering = TransactionOrdering.DATE_TIME_DESC,
    ) -> tuple[list[Transaction], int]:
        grouped_accounts = self.group_accounts(accounts)
        ledger_accounts = {
            "-": (
                await self.accounts.get_ledger_accounts(ledger_id=ledger_id, paths=grouped_accounts["-"])
                if grouped_accounts["-"]
                else []
            ),
            "+": (
                await self.accounts.get_ledger_accounts(ledger_id=ledger_id, paths=grouped_accounts["+"])
                if grouped_accounts["+"]
                else []
            ),
            "=": (
                await self.accounts.get_ledger_accounts(ledger_id=ledger_id, paths=grouped_accounts["="])
                if grouped_accounts["="]
                else []
            ),
        }
        accounts_ids: list[tuple[Literal["=", "-", "+"], UUID7]] = []
        accounts_ids.extend(("+", account.id) for account in ledger_accounts["+"])
        accounts_ids.extend(("-", account.id) for account in ledger_accounts["-"])
        accounts_ids.extend(("=", account.id) for account in ledger_accounts["="])

        transactions, count = await self.dal.find_ledger_transactions(
            ledger_id=ledger_id,
            accounts_ids=accounts_ids,
            tags=tags,
            state=state,
            after=after,
            before=before,
            exchange=exchange,
            skip=skip,
            limit=limit,
            order_by=order_by,
        )
        return transactions, count

    async def get_ledger_transaction(
        self,
        ledger_id: LedgerUUID,
        transaction_id: TransactionUUID,
    ) -> Transaction:
        return await self.dal.get_ledger_transaction(
            ledger_id=ledger_id,
            transaction_id=transaction_id,
        )

    async def delete_ledger_transaction(
        self,
        ledger_id: LedgerUUID,
        transaction_id: TransactionUUID,
        updated_at: pendulum.DateTime | None = None,
    ):
        await self.dal.delete_ledger_transaction(
            ledger_id=ledger_id,
            transaction_id=transaction_id,
            updated_at=updated_at,
        )

    async def get_ledger_account_balance(
        self,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
    ) -> list[AccountBalance]:
        balance = await self.dal.get_ledger_account_balance(
            ledger_id=ledger_id,
            account_id=account_id,
        )
        return balance

    async def find_ledger_account_transactions(
        self,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
        after: datetime | None = None,
        before: datetime | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: TransactionOrdering = TransactionOrdering.DATE_TIME_DESC,
    ) -> tuple[list[Transaction], int]:
        transactions, count = await self.dal.find_ledger_transactions(
            ledger_id=ledger_id,
            accounts_ids=[("=", account_id)],
            after=after,
            before=before,
            skip=skip,
            limit=limit,
            order_by=order_by,
        )
        return transactions, count
