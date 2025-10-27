import logging

import pytest
from pytest_mongo import factories

from tests.fixtures.api_client import (
    api_client,  # noqa: F401
)
from tmw_ledger.settings import Settings, load_settings

mongo_proc = factories.mongo_proc()
mongodb = factories.mongodb("mongo_proc")

logging.getLogger("pymongo").setLevel(logging.INFO)
logging.getLogger("faker.factory").setLevel(logging.INFO)


@pytest.fixture(scope="session")
def app_settings(request: type[pytest.FixtureRequest]) -> Settings:
    return load_settings()


@pytest.fixture
async def init_db(request: type[pytest.FixtureRequest], app_settings: Settings):
    from tmw_ledger.db import init_db

    await init_db(app_settings)
