import pytest
from blacksheep.testing import TestClient


async def make_api_client():
    from tmw_ledger.app import app

    await app.start()

    return TestClient(app)


@pytest.fixture
async def api_client(mongodb, init_db) -> TestClient:
    return await make_api_client()
