from typing import Any

from blacksheep import HTTPException, Request, Response
from blacksheep.server import Application
from blacksheep.server.bindings import InvalidRequestBody
from blacksheep.server.responses import pretty_json
from essentials.exceptions import (
    AcceptedException,
    ConflictException,
    ForbiddenException,
    NotImplementedException,
    ObjectNotFound,
    UnauthorizedException,
)
from pydantic import ValidationError

from tmw_ledger.core.exceptions import PreconditionFailed
from tmw_ledger.core.logging import logger


def configure_error_handlers(app: Application) -> None:  # noqa: C901
    """Configure error handlers for the application."""

    async def not_found_handler(_app: Application, _request: Request, exception: Exception) -> Response:
        return pretty_json(
            {
                "detail": str(exception) or "Not found",
                "status_code": 404,
            },
            404,
        )

    async def not_implemented(*args: Any) -> Response:
        return pretty_json(
            {
                "detail": "Not implemented",
                "status_code": 500,
            },
            status=500,
        )

    async def unauthorized(_app: Application, _request: Request, exception: Exception) -> Response:
        logger.debug("Unauthorized ERROR", exc_info=exception)

        return pretty_json(
            {
                "detail": str(exception) or "Unauthorized",
                "status_code": 401,
            },
            status=401,
        )

    async def forbidden(*_args: Any) -> Response:
        return pretty_json(
            {
                "detail": "Forbidden",
                "status_code": 403,
            },
            status=403,
        )

    async def accepted(*_args: Any) -> Response:
        return pretty_json(
            {
                "detail": "Accepted",
                "status_code": 202,
            },
            status=202,
        )

    async def validation_error(_app: Application, _request: Request, exception: Exception) -> Response:
        logger.debug("Validation ERROR", exc_info=exception)

        return pretty_json(
            {
                "detail": str(exception) or "Bad request",
                "status_code": 400,
            },
            status=400,
        )

    async def server_error(_app: Application, _request: Request, exception: Exception) -> Response:
        logger.debug("Server request ERROR", exc_info=exception)

        return pretty_json(
            {
                "detail": "Server error",
                "status_code": 500,
            },
            status=500,
        )

    async def bad_request(_app: Application, _request: Request, exception: HTTPException) -> Response:
        logger.debug(f"Bad request ERROR. Got an exception {type(exception)}", exc_info=exception)

        if exception.__context__ is not None and callable(getattr(exception.__context__, "errors", None)):
            return pretty_json(
                {
                    "detail": str(exception.__context__.errors()),  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue]
                    "status_code": 400,
                },
                status=400,
            )

        return pretty_json(
            {
                "detail": str(exception or "Bad request"),
                "status_code": 400,
            },
            status=400,
        )

    async def invalid_body_error(_app: Application, _request: Request, exception: InvalidRequestBody) -> Response:
        logger.debug("Invalid body ERROR", exc_info=exception)
        return pretty_json(
            {
                "detail": str(exception or "Invalid body"),
                "status_code": 400,
            },
            status=400,
        )

    async def conflict_error(_app: Application, _request: Request, exception: ConflictException) -> Response:
        logger.debug("Conflict ERROR", exc_info=exception)
        if exception.__context__ is not None:
            return pretty_json(
                {
                    "detail": str(exception.__context__),
                    "status_code": 409,
                },
                status=409,
            )
        return pretty_json(
            {
                "detail": str(exception) or "Conflict",
                "status_code": 409,
            },
            status=409,
        )

    async def precondition_failed_error(
        _app: Application, _request: Request, exception: PreconditionFailed
    ) -> Response:
        logger.debug("Precondition Failed ERROR", exc_info=exception)
        return pretty_json(
            {
                "detail": str(exception) or "Precondition Failed",
                "status_code": 412,
            },
            status=412,
        )

    app.exceptions_handlers.update(
        {
            500: server_error,
            400: bad_request,
            ObjectNotFound: not_found_handler,
            NotImplementedException: not_implemented,
            UnauthorizedException: unauthorized,
            ForbiddenException: forbidden,
            AcceptedException: accepted,
            ValidationError: validation_error,
            Exception: server_error,
            InvalidRequestBody: invalid_body_error,
            ConflictException: conflict_error,
            PreconditionFailed: precondition_failed_error,
        }
    )
