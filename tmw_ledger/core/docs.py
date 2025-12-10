from blacksheep import Application
from blacksheep.server.openapi.v3 import OpenAPIHandler
from openapidocs.v3 import APIKeySecurity, Info, ParameterLocation

from tmw_ledger.settings import Settings


def configure_docs(app: Application, settings: Settings):
    """Configure the OpenAPI documentation for the application."""
    docs = OpenAPIHandler(
        info=Info(
            title=settings.info.title,
            version=settings.info.version,
            description=settings.info.description,
        ),
        anonymous_access=True,
        security_schemes={"ApiKeyAuth": APIKeySecurity(name="x-api-key", in_=ParameterLocation.HEADER)},
    )

    # include only endpoints whose path starts with "/api/"
    docs.include = lambda path, _: "/api/" in path

    docs.bind_app(app)
