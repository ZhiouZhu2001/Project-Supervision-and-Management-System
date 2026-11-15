"""One error shape for the whole API.

The frontend branches on `code`, never on the message, so codes are stable
and messages are allowed to change.
"""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}


async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(error_body(exc.code, exc.message, exc.details), status_code=exc.status_code)


def unauthenticated(message: str = "Authentication required") -> ApiError:
    return ApiError(401, "UNAUTHENTICATED", message)


def invalid_credentials() -> ApiError:
    return ApiError(401, "INVALID_CREDENTIALS", "Email or password is incorrect")
