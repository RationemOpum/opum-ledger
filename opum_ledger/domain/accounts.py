"""Domain layer for account management in the ledger system."""

from collections import defaultdict
from datetime import datetime
from uuid import uuid7

import pendulum
from beanie import UpdateResponse
from beanie.odm.operators.find.comparison import In
from beanie.odm.operators.update.general import Set
from beanie.odm.queries.find import FindMany
from essentials.exceptions import ConflictException, ObjectNotFound
from pydantic import BaseModel, ConfigDict, TypeAdapter, field_validator, model_validator
from pymongo.errors import DuplicateKeyError
from pymongo.results import UpdateResult

from opum_ledger.core.exceptions import PreconditionFailed
from opum_ledger.core.services import add_service
from opum_ledger.core.utils import split_path
from opum_ledger.domain.types.account import AccountName, AccountPath, AccountUUID
from opum_ledger.domain.types.ledger import LedgerUUID
from opum_ledger.models.accounts import AccountModel

ROOT_PATH = [
    "Assets",
    "Liabilities",
    "Incomes",
    "Expenses",
    "Equity",
]


class AccountBase(BaseModel):
    name: AccountName
    path: AccountPath


class NewAccount(AccountBase):
    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate the path and return the path without trailing semicolons."""
        if split_path(v)[0] not in ROOT_PATH:
            raise ValueError("Invalid root path.")
        return v.strip(":")

    @property
    def paths(self) -> list[AccountPath]:
        return split_path(self.path)


class Account(NewAccount):
    model_config = ConfigDict(
        from_attributes=True,
    )
    id: AccountUUID
    created_at: datetime
    updated_at: datetime


class AccountUpdate(BaseModel):
    name: AccountName | None = None
    path: AccountPath | None = None

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str | None) -> str | None:
        """Validate the path and return the path without trailing semicolons."""
        if v is not None and split_path(v)[0] not in ROOT_PATH:
            raise ValueError("Invalid root path.")
        return v.strip(":") if v else None

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        """Ensure at least one of name or path is provided."""
        if not any([self.name, self.path]):
            raise ValueError("At least one of name or path must be provided.")
        return self


@add_service(scope="scoped")
class AccountsDAL:
    __model__ = AccountModel

    async def create_account(
        self,
        ledger_id: LedgerUUID,
        new_account: NewAccount,
    ) -> Account:
        account = AccountModel(
            id=uuid7(),
            name=new_account.name,
            path=new_account.path,
            paths=new_account.paths,
            ledger_id=ledger_id,
        )

        try:
            account = await account.create()
        except DuplicateKeyError as e:
            raise ConflictException("Duplicate account in the ledger already exists") from e

        return Account.model_validate(account)

    async def get_by_id(self, account_id: AccountUUID) -> Account:
        account = await AccountModel.find_one(
            AccountModel.id == account_id,
            AccountModel.deleted_at == None,  # noqa E711
        )
        return Account.model_validate(account)

    async def get_ledger_account(
        self,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
    ) -> Account:
        account = await AccountModel.find_one(
            AccountModel.id == account_id,
            AccountModel.ledger_id == ledger_id,
            AccountModel.deleted_at == None,  # noqa E711
        )
        if not account:
            raise ObjectNotFound
        return Account.model_validate(account)

    async def get_ledger_accounts(
        self,
        ledger_id: LedgerUUID,
        paths: list[AccountPath] | None = None,
    ) -> list[Account]:
        request: FindMany[AccountModel] = AccountModel.find(
            AccountModel.ledger_id == ledger_id,
            AccountModel.deleted_at == None,  # noqa E711
        )
        if paths:
            request = request.find(
                In(AccountModel.paths, paths),
            )
        accounts = await request.to_list()
        return TypeAdapter(list[Account]).validate_python(accounts)

    async def update_ledger_account(
        self,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
        updated_account: AccountUpdate,
        updated_at: pendulum.DateTime | None = None,
    ) -> Account:
        account_query = AccountModel.find_one(
            AccountModel.id == account_id,
            AccountModel.ledger_id == ledger_id,
            AccountModel.deleted_at == None,  # noqa E711
        )
        account = await account_query
        if not account:
            raise ObjectNotFound

        if updated_at and pendulum.instance(account.updated_at) > updated_at:
            raise PreconditionFailed("Account has been modified since the provided timestamp.")

        update_data = updated_account.model_dump(exclude_unset=True)
        update_data["updated_at"] = pendulum.now("UTC")
        if "path" in update_data:
            update_data["paths"] = AccountModel.parse_path(update_data["path"])

        if updated_at is not None:
            account_query = account_query.find_one(
                AccountModel.updated_at == updated_at,
            )

        update_result: UpdateResult = await account_query.update(  # pyright: ignore[reportGeneralTypeIssues]
            Set(update_data),
            response_type=UpdateResponse.UPDATE_RESULT,
        )

        if update_result.matched_count == 0:
            raise PreconditionFailed("Account has been modified since the provided timestamp.")

        return await self.get_by_id(account_id)

    async def delete_ledger_account(
        self,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
        updated_at: pendulum.DateTime | None = None,
    ):
        account_query = AccountModel.find_one(
            AccountModel.id == account_id,
            AccountModel.ledger_id == ledger_id,
            AccountModel.deleted_at == None,  # noqa E711
        )
        account = await account_query
        if not account:
            raise ObjectNotFound

        if updated_at and pendulum.instance(account.updated_at) > updated_at:
            raise PreconditionFailed("Account has been modified since the provided timestamp.")

        if updated_at is not None:
            account_query = account_query.find_one(
                AccountModel.updated_at == updated_at,
            )

        account_update_result: UpdateResult = await account_query.update(  # pyright: ignore[reportGeneralTypeIssues]
            Set({"deleted_at": pendulum.now()}),
            response_type=UpdateResponse.UPDATE_RESULT,
        )

        if account_update_result.matched_count == 0:
            raise PreconditionFailed("Account has been modified since the provided timestamp.")


@add_service(scope="scoped")
class AccountsBL:
    def __init__(self, dal: AccountsDAL):
        self.dal: AccountsDAL = dal

    async def create_account(
        self,
        ledger_id: LedgerUUID,
        new_account: NewAccount,
    ) -> Account:
        return await self.dal.create_account(
            ledger_id,
            new_account,
        )

    async def update_ledger_account(
        self,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
        updated_account: AccountUpdate,
        updated_at: pendulum.DateTime | None = None,
    ) -> Account:
        return await self.dal.update_ledger_account(
            ledger_id,
            account_id,
            updated_account,
            updated_at=updated_at,
        )

    async def get_ledger_accounts(
        self,
        ledger_id: LedgerUUID,
        paths: list[AccountPath] | None = None,
    ) -> list[Account]:
        return await self.dal.get_ledger_accounts(
            ledger_id=ledger_id,
            paths=paths,
        )

    async def get_ledger_account(
        self,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
    ) -> Account:
        account = await self.dal.get_ledger_account(
            ledger_id=ledger_id,
            account_id=account_id,
        )
        return account

    async def delete_ledger_account(
        self,
        ledger_id: LedgerUUID,
        account_id: AccountUUID,
        updated_at: pendulum.DateTime | None = None,
    ):
        await self.dal.delete_ledger_account(
            ledger_id=ledger_id,
            account_id=account_id,
            updated_at=updated_at,
        )

    async def get_ledger_accounts_tree(
        self,
        ledger_id: LedgerUUID,
    ) -> dict[str, list[Account]]:
        accounts = await self.get_ledger_accounts(
            ledger_id=ledger_id,
        )
        tree = defaultdict(list)
        for account in accounts:
            tree[account.path].append(account)
        return tree
