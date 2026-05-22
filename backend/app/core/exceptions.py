import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.responses import error_response

logger = logging.getLogger(__name__)


class AppException(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: int = 400,
        status_code: int | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code or code


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return error_response(code=exc.code, message=exc.message, status_code=exc.status_code)


async def http_exception_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "请求失败"
    return error_response(code=exc.status_code, message=message, status_code=exc.status_code)


async def validation_exception_handler(
    _request: Request,
    _exc: RequestValidationError,
) -> JSONResponse:
    return error_response(code=400, message="参数错误", status_code=400)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled error request_id=%s path=%s", request_id, request.url.path)
    return error_response(code=500, message="服务内部错误", status_code=500)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
