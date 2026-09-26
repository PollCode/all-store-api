import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.exceptions import AppException, ConflictError, UnprocessableEntityError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos los handlers globales de excepciones."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(
            "AppException on %s %s -> [%s] %s",
            request.method,
            request.url.path,
            exc.error_type,
            exc.message,
        )
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        wrapped = UnprocessableEntityError(
            message="Validation failed",
            details={"errors": exc.errors()},
        )
        return JSONResponse(status_code=wrapped.status_code, content=wrapped.to_dict())

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.exception("Database integrity error")
        wrapped = ConflictError(
            message="Database integrity constraint violated",
            details={"hint": str(exc.orig) if hasattr(exc, "orig") else None},
        )
        return JSONResponse(status_code=wrapped.status_code, content=wrapped.to_dict())

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        from ..core.exceptions import AppException as _AppException

        wrapped = _AppException(
            message=str(exc.detail),
            status_code=exc.status_code,
            error_type="http_error",
        )
        return JSONResponse(
            status_code=wrapped.status_code,
            content=wrapped.to_dict(),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        from ..core.exceptions import InternalServerError

        wrapped = InternalServerError()
        return JSONResponse(status_code=wrapped.status_code, content=wrapped.to_dict())