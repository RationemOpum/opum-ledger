"""Common fixtures for tests."""

from uuid import uuid7

import pytest

from opum_ledger.domain.accounts import Account
from opum_ledger.domain.commodities import Commodity
from opum_ledger.domain.ledgers import Ledger
from opum_ledger.models.accounts import AccountModel
from opum_ledger.models.commodities import CommodityModel
from opum_ledger.models.ledger import LedgerModel


@pytest.fixture
async def ledger_one(init_db) -> Ledger:
    """Create and return the first test ledger."""
    ledger_model = LedgerModel(
        id=uuid7(),
        name="Test Ledger One",
        description="First test ledger for fixtures",
    )
    await ledger_model.create()
    return Ledger.model_validate(ledger_model)


@pytest.fixture
async def ledger_two(init_db) -> Ledger:
    """Create and return the second test ledger."""
    ledger_model = LedgerModel(
        id=uuid7(),
        name="Test Ledger Two",
        description="Second test ledger for fixtures",
    )
    await ledger_model.create()
    return Ledger.model_validate(ledger_model)


@pytest.fixture
async def commodity_usd_ledger_one(ledger_one: Ledger) -> Commodity:
    """Create and return USD commodity for ledger one."""
    commodity_model = CommodityModel(
        id=uuid7(),
        name="US Dollar",
        code="USD",
        symbol="$",
        subunit=100,
        no_market=False,
        ledger_id=ledger_one.id,
    )
    await commodity_model.create()
    return Commodity.model_validate(commodity_model)


@pytest.fixture
async def commodity_eur_ledger_one(ledger_one: Ledger) -> Commodity:
    """Create and return EUR commodity for ledger one."""
    commodity_model = CommodityModel(
        id=uuid7(),
        name="Euro",
        code="EUR",
        symbol="€",
        subunit=100,
        no_market=False,
        ledger_id=ledger_one.id,
    )
    await commodity_model.create()
    return Commodity.model_validate(commodity_model)


@pytest.fixture
async def commodity_usd_ledger_two(ledger_two: Ledger) -> Commodity:
    """Create and return USD commodity for ledger two."""
    commodity_model = CommodityModel(
        id=uuid7(),
        name="US Dollar",
        code="USD",
        symbol="$",
        subunit=100,
        no_market=False,
        ledger_id=ledger_two.id,
    )
    await commodity_model.create()
    return Commodity.model_validate(commodity_model)


@pytest.fixture
async def commodity_gbp_ledger_two(ledger_two: Ledger) -> Commodity:
    """Create and return GBP commodity for ledger two."""
    commodity_model = CommodityModel(
        id=uuid7(),
        name="British Pound",
        code="GBP",
        symbol="£",
        subunit=100,
        no_market=False,
        ledger_id=ledger_two.id,
    )
    await commodity_model.create()
    return Commodity.model_validate(commodity_model)


@pytest.fixture
async def account_assets_cash_ledger_one(ledger_one: Ledger) -> Account:
    """Create and return Assets:Cash account for ledger one."""
    account_model = AccountModel(
        id=uuid7(),
        name="Cash",
        path="Assets:Cash",
        paths=["Assets", "Assets:Cash"],
        ledger_id=ledger_one.id,
    )
    await account_model.create()
    return Account.model_validate(account_model)


@pytest.fixture
async def account_expenses_food_ledger_one(ledger_one: Ledger) -> Account:
    """Create and return Expenses:Food account for ledger one."""
    account_model = AccountModel(
        id=uuid7(),
        name="Food",
        path="Expenses:Food",
        paths=["Expenses", "Expenses:Food"],
        ledger_id=ledger_one.id,
    )
    await account_model.create()
    return Account.model_validate(account_model)


@pytest.fixture
async def account_incomes_salary_ledger_one(ledger_one: Ledger) -> Account:
    """Create and return Incomes:Salary account for ledger one."""
    account_model = AccountModel(
        id=uuid7(),
        name="Salary",
        path="Incomes:Salary",
        paths=["Incomes", "Incomes:Salary"],
        ledger_id=ledger_one.id,
    )
    await account_model.create()
    return Account.model_validate(account_model)


@pytest.fixture
async def account_assets_bank_ledger_two(ledger_two: Ledger) -> Account:
    """Create and return Assets:Bank account for ledger two."""
    account_model = AccountModel(
        id=uuid7(),
        name="Bank",
        path="Assets:Bank",
        paths=["Assets", "Assets:Bank"],
        ledger_id=ledger_two.id,
    )
    await account_model.create()
    return Account.model_validate(account_model)


@pytest.fixture
async def account_expenses_transport_ledger_two(ledger_two: Ledger) -> Account:
    """Create and return Expenses:Transport account for ledger two."""
    account_model = AccountModel(
        id=uuid7(),
        name="Transport",
        path="Expenses:Transport",
        paths=["Expenses", "Expenses:Transport"],
        ledger_id=ledger_two.id,
    )
    await account_model.create()
    return Account.model_validate(account_model)


@pytest.fixture
async def account_liabilities_creditcard_ledger_two(ledger_two: Ledger) -> Account:
    """Create and return Liabilities:CreditCard account for ledger two."""
    account_model = AccountModel(
        id=uuid7(),
        name="CreditCard",
        path="Liabilities:CreditCard",
        paths=["Liabilities", "Liabilities:CreditCard"],
        ledger_id=ledger_two.id,
    )
    await account_model.create()
    return Account.model_validate(account_model)


@pytest.fixture
async def account_expenses_groceries_ledger_one(ledger_one: Ledger) -> Account:
    """Create and return Expenses:Groceries account for ledger one."""
    account_model = AccountModel(
        id=uuid7(),
        name="Groceries",
        path="Expenses:Groceries",
        paths=["Expenses", "Expenses:Groceries"],
        ledger_id=ledger_one.id,
    )
    await account_model.create()
    return Account.model_validate(account_model)


@pytest.fixture
async def account_expenses_rent_ledger_one(ledger_one: Ledger) -> Account:
    """Create and return Expenses:Rent account for ledger one."""
    account_model = AccountModel(
        id=uuid7(),
        name="Rent",
        path="Expenses:Rent",
        paths=["Expenses", "Expenses:Rent"],
        ledger_id=ledger_one.id,
    )
    await account_model.create()
    return Account.model_validate(account_model)


@pytest.fixture
async def account_assets_cash_usd_ledger_one(ledger_one: Ledger) -> Account:
    """Create and return Assets:Cash:USD account for ledger one."""
    account_model = AccountModel(
        id=uuid7(),
        name="USD Cash",
        path="Assets:Cash:USD",
        paths=["Assets", "Assets:Cash", "Assets:Cash:USD"],
        ledger_id=ledger_one.id,
    )
    await account_model.create()
    return Account.model_validate(account_model)


@pytest.fixture
async def account_assets_cash_eur_ledger_one(ledger_one: Ledger) -> Account:
    """Create and return Assets:Cash:EUR account for ledger one."""
    account_model = AccountModel(
        id=uuid7(),
        name="EUR Cash",
        path="Assets:Cash:EUR",
        paths=["Assets", "Assets:Cash", "Assets:Cash:EUR"],
        ledger_id=ledger_one.id,
    )
    await account_model.create()
    return Account.model_validate(account_model)
