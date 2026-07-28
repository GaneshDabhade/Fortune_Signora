"""The single error contract shared by every endpoint (19-api-conventions.md).

Domain and application code raises domain exceptions and knows nothing about
HTTP. Translation happens here, once, via a mapping supplied by the
composition root — which is what keeps this module free of any dependency on
``modules`` while still handling module-specific errors.
"""

from collections.abc import Mapping
from typing import Final
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException

from signora_platform.auth import AuthenticationError, ExpiredTokenError
from signora_platform.authorization import AuthorizationDeniedError

CORRELATION_ID_HEADER: Final[str] = "X-Correlation-ID"


class ErrorDetail(BaseModel):
    model_config = ConfigDict(frozen=True)

    field: str
    message: str


class ErrorBody(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    details: list[ErrorDetail] | None = None
    correlation_id: UUID


class ErrorResponse(BaseModel):
    """The envelope every error response uses, without exception."""

    model_config = ConfigDict(frozen=True)

    error: ErrorBody


ErrorMapping = Mapping[type[Exception], tuple[int, str]]
"""Domain exception type -> (HTTP status, stable machine-readable code)."""


def correlation_id_of(request: Request) -> UUID:
    """The correlation id for this request, generated on first access.

    Ties an error response to server-side logs and traces
    (07-data-flow.md). Stored on request state so a single request reports
    one id everywhere.
    """
    existing = getattr(request.state, "correlation_id", None)
    if isinstance(existing, UUID):
        return existing
    generated = uuid4()
    request.state.correlation_id = generated
    return generated


def _error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    correlation_id = correlation_id_of(request)
    body = ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details, correlation_id=correlation_id)
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json", exclude_none=True),
        headers={CORRELATION_ID_HEADER: str(correlation_id)},
    )


def register_exception_handlers(app: FastAPI, *, domain_errors: ErrorMapping) -> None:
    """Install the handlers that produce the standard envelope.

    ``domain_errors`` is supplied by the composition root, which is the only
    place that may know about both ``signora_platform`` and ``modules``.
    """

    @app.exception_handler(AuthenticationError)
    async def _authentication(request: Request, exc: Exception) -> JSONResponse:
        # Expiry is distinguished from other failures because it is the one
        # case a legitimate client can act on: refresh and retry.
        code = "token_expired" if isinstance(exc, ExpiredTokenError) else "unauthenticated"
        return _error_response(
            request=request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=code,
            message=str(exc),
        )

    @app.exception_handler(AuthorizationDeniedError)
    async def _authorization(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(
            request=request,
            status_code=status.HTTP_403_FORBIDDEN,
            code="forbidden",
            message="You do not have permission to perform this action.",
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, RequestValidationError)
        details = [
            ErrorDetail(
                # Drop the leading location segment ("body"/"query"/"path"),
                # which is transport noise rather than a field name.
                field=".".join(str(part) for part in error["loc"][1:]) or str(error["loc"][0]),
                message=error["msg"],
            )
            for error in exc.errors()
        ]
        return _error_response(
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="validation_error",
            message="The request failed validation.",
            details=details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, StarletteHTTPException)
        # Covers framework-raised errors such as 404 for an unrouted path,
        # so even those use the standard envelope.
        return _error_response(
            request=request,
            status_code=exc.status_code,
            code=_DEFAULT_CODES.get(exc.status_code, "error"),
            message=str(exc.detail),
        )

    for exception_type, (status_code, code) in domain_errors.items():
        app.add_exception_handler(
            exception_type, _domain_handler(status_code=status_code, code=code)
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Fails closed: an unmapped exception never leaks its message, type,
        # or stack trace to the caller. The correlation id is the bridge to
        # the full detail in logs and Sentry.
        return _error_response(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_error",
            message="An unexpected error occurred.",
        )


def _domain_handler(*, status_code: int, code: str):  # type: ignore[no-untyped-def]
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(
            request=request, status_code=status_code, code=code, message=str(exc)
        )

    return handler


_DEFAULT_CODES: Final[dict[int, str]] = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "unauthenticated",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_409_CONFLICT: "conflict",
}
