from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    code: int = 200
    message: str = "成功"
    data: Any = None


class PageData(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]


def ok(data: Any = None, message: str = "成功") -> ApiResponse:
    return ApiResponse(code=200, message=message, data=data)


def page_response(items: list[Any], total: int, page: int, page_size: int) -> ApiResponse:
    return ok(PageData(total=total, page=page, page_size=page_size, items=items).model_dump())
