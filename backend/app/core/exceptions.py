#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:35
# @File     : exceptions.py
# @Desc     : API exception types and handlers.

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Business exception carrying frontend-safe error codes."""

    def __init__(self, code: int, message: str, http_status: int = 400, data: dict | None = None) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        self.data = data


def error_payload(code: int, message: str, data: dict | None = None) -> dict:
    return {"code": code, "message": message, "data": data}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.http_status, content=error_payload(exc.code, exc.message, exc.data))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(part) for part in first_error.get("loc", []) if part != "body")
        message = "参数不完整，请检查后重试"
        return JSONResponse(status_code=422, content=error_payload(40001, message, {"field": field}))

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = 40400 if exc.status_code == 404 else exc.status_code
        message = "数据不存在" if exc.status_code == 404 else str(exc.detail)
        return JSONResponse(status_code=exc.status_code, content=error_payload(code, message))
