"""Application Settings."""

import os

from blacksheep.server.env import is_development
from config.common import ConfigurationBuilder
from config.env import EnvVars
from config.user import UserSettings
from config.yaml import YAMLFile
from pydantic import BaseModel


class APIInfo(BaseModel):
    title: str = "Ledger API"
    version: str = "0.0.1"
    description: str = "Service to track ledger with double-entry accounting"


class Auth(BaseModel):
    x_api_key: str = "secret"


class Database(BaseModel):
    driver: str = "mongodb"
    host: str = "localhost"
    port: int = 27017
    user: str | None = "user"
    password: str | None = "password"
    database: str = "ledger"


class StaticSettings(BaseModel):
    serve_static: bool = False
    static_path: str = "static"


class App(BaseModel):
    debug: bool = True
    show_error_details: bool = True
    cors_origins: str = "http://localhost:8000,http://localhost:5173"
    import_file_size_limit: int = 5242880  # bytes
    static: StaticSettings = StaticSettings()


class Settings(BaseModel):
    info: APIInfo = APIInfo()
    app: App = App()
    auth: Auth = Auth()
    db: Database = Database()


def load_settings() -> Settings:
    """Load the application settings.

    Returns:
        Configuration: The loaded configuration.

    """
    settings_file = os.environ.get("APP_SETTINGS_FILE", "settings.yaml")
    builder = ConfigurationBuilder(
        YAMLFile(settings_file),
        EnvVars(
            prefix="APP_",
            file=".env",
        ),
    )

    if is_development():
        # for development environment, settings stored in the user folder
        builder.add_source(UserSettings())

    configuration = builder.build()

    return configuration.bind(Settings)
