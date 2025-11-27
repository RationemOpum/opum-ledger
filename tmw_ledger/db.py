from beanie import Document, init_beanie
from blacksheep.server.application import Application
from pymongo import AsyncMongoClient

from tmw_ledger.models.commodities import CommodityModel
from tmw_ledger.models.ledger import LedgerModel
from tmw_ledger.models.accounts import AccountModel
from tmw_ledger.settings import Settings

DOCUMENT_MODELS: list[type[Document]] = [
    CommodityModel,
    LedgerModel,
    AccountModel,
]


async def init_db(settings: Settings) -> AsyncMongoClient:
    # Create Motor client
    driver: str = settings.db.driver
    host: str = settings.db.host
    user: str = settings.db.user
    password: str = settings.db.password
    port: int = settings.db.port
    database: str = settings.db.database
    if user and password:
        client = AsyncMongoClient(
            f"{driver}://{user}:{password}@{host}:{port}/{database}",
            uuidRepresentation="standard",
        )
    else:
        client = AsyncMongoClient(
            f"{driver}://{host}:{port}/{database}",
            uuidRepresentation="standard",
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
