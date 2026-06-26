from typing import cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from app.schemas.error import ErrorResponse


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        code: str | None = None,
        errors: list[dict] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
        self.errors = errors


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found", code: str | None = None) -> None:
        super().__init__(status_code=404, detail=detail, code=code or "NOT_FOUND")


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request", code: str | None = None, errors: list[dict] | None = None) -> None:
        super().__init__(status_code=400, detail=detail, code=code or "BAD_REQUEST", errors=errors)


class ConflictException(AppException):
    def __init__(self, detail: str = "Conflict", code: str | None = None) -> None:
        super().__init__(status_code=409, detail=detail, code=code or "CONFLICT")


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=exc.detail, code=exc.code, errors=exc.errors).model_dump(),
    )


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=str(exc.detail), code="HTTP_ERROR").model_dump(),
    )


async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            detail="Validation error",
            code="VALIDATION_ERROR",
            errors=cast(list[dict], exc.errors()),
        ).model_dump(),
    )


async def generic_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail="Internal server error", code="INTERNAL_ERROR").model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(Exception, generic_exception_handler)
