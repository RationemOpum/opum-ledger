from beanie import Document, init_beanie
from blacksheep.server.application import Application
from pymongo import AsyncMongoClient

from opum_ledger.models.accounts import AccountModel
from opum_ledger.models.commodities import CommodityModel
from opum_ledger.models.ledger import LedgerModel
from opum_ledger.models.transactions import TransactionModel
from opum_ledger.settings import Settings

DOCUMENT_MODELS: list[type[Document]] = [
    CommodityModel,
    LedgerModel,
    AccountModel,
    TransactionModel,
]


async def init_db(settings: Settings) -> AsyncMongoClient:
    # Create Motor client
    driver: str = settings.db.driver
    host: str = settings.db.host
    user: str | None = settings.db.user
    password: str | None = settings.db.password
    port: int = settings.db.port
    database: str = settings.db.database
    client: AsyncMongoClient
    if user and password:
        client = AsyncMongoClient(
            f"{driver}://{user}:{password}@{host}:{port}/{database}",
            uuidRepresentation="standard",
            tz_aware=True,
        )
    else:
        client = AsyncMongoClient(
            f"{driver}://{host}:{port}/{database}",
            uuidRepresentation="standard",
            tz_aware=True,
        )

    await init_beanie(
        database=getattr(client, database),
        document_models=DOCUMENT_MODELS,
    )

    return client


def use_beanie(app: Application, settings: Settings):
    @app.lifespan
    async def db_lifespan_hook():  # pyright: ignore[reportUnusedFunction]
        client = await init_db(settings)

        yield

        await client.close()
