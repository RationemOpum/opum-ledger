"""Application configuration."""

import uvicorn
from blacksheep import Application
from blacksheep.server.diagnostics import get_diagnostic_app
from rodi import Container

from tmw_ledger.core.docs import configure_docs
from tmw_ledger.core.errors import configure_error_handlers
from tmw_ledger.core.json import use_orjson
from tmw_ledger.core.logging import config_logger
from tmw_ledger.core.services import configure_services
from tmw_ledger.db import use_beanie
from tmw_ledger.settings import Settings, load_configuration


def configure_application(
    services: Container,
    settings: Settings,
) -> Application:
    config_logger(settings)

    app = Application(
        services=services,
        show_error_details=settings.app.show_error_details,
    )

    use_beanie(app, settings)

    app.use_cors(  # pyright: ignore[reportUnusedCallResult]
        allow_methods="GET POST PUT DELETE",
        allow_origins=settings.app.cors_origins,
        allow_headers="Content-Type",
        allow_credentials=True,
    )

    # TODO:
    # pass orjson to pydantic
    use_orjson()

    configure_error_handlers(app)

    if settings.app.static.serve_static:
        app.serve_files(settings.app.static.static_path)

    configure_docs(app, settings)

    return app


def get_app() -> Application:
    """Return the application instance.

    This function initializes and configures the application instance.

    In case of any errors during initialization, it returns a diagnostic application instance.

    Returns:
        Application: The configured application instance.

    """
    try:
        return configure_application(*configure_services(load_configuration()))
    except Exception as exc:
        return get_diagnostic_app(exc)


app = get_app()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")
