import logging
import os

import pytest
from pytest_mongo import factories

from opum_ledger.settings import Settings, load_settings
from tests.fixtures.api_client import (
    api_client,  # noqa: F401
    api_client_ro,  # noqa: F401
)
from tests.fixtures.common import (  # noqa: F401
    account_assets_bank_ledger_two,
    account_assets_cash_eur_ledger_one,
    account_assets_cash_ledger_one,
    account_assets_cash_usd_ledger_one,
    account_expenses_food_ledger_one,
    account_expenses_groceries_ledger_one,
    account_expenses_rent_ledger_one,
    account_expenses_transport_ledger_two,
    account_incomes_salary_ledger_one,
    account_liabilities_creditcard_ledger_two,
    commodity_eur_ledger_one,
    commodity_gbp_ledger_two,
    commodity_usd_ledger_one,
    commodity_usd_ledger_two,
    ledger_one,
    ledger_two,
)

logging.info(os.environ)
if os.environ.get("CI"):
    mongo_external = factories.mongodb("mongo_noproc")
else:
    mongo_proc = factories.mongo_proc()
    mongodb = factories.mongodb("mongo_proc")

logging.getLogger("pymongo").setLevel(logging.INFO)
logging.getLogger("faker.factory").setLevel(logging.INFO)


@pytest.fixture(scope="session")
def app_settings(request: type[pytest.FixtureRequest]) -> Settings:
    return load_settings()


@pytest.fixture
async def init_db(request: type[pytest.FixtureRequest], app_settings: Settings) -> None:
    from opum_ledger.db import init_db

    await init_db(app_settings)
