from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
import logging

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        error_content = {
            "code": exc.code,
            "message": exc.message,
        }
        if exc.details is not None:
            error_content["details"] = jsonable_encoder(exc.details)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error_content},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        first_error_msg = exc.errors()[0]["msg"] if exc.errors() else "Validation error"
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": first_error_msg,
                    "details": jsonable_encoder(exc.errors()),
                }
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning(f"Database integrity error: {exc}")
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "RESOURCE_CONFLICT",
                    "message": "A database constraint violation occurred.",
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled server error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                }
            },
        )
