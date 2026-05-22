from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ApiResponse(BaseModel):
    code: int = 200
    message: str = "成功"
    data: Any = None


def success_response(data: Any = None, message: str = "成功") -> ApiResponse:
    return ApiResponse(code=200, message=message, data=data)


def error_response(
    code: int,
    message: str,
    status_code: int | None = None,
    data: Any = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code or code,
        content=ApiResponse(code=code, message=message, data=data).model_dump(),
    )
