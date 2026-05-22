from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AdminUserListItem(BaseModel):
    id: int
    username: str | None = None
    nickname: str | None = None
    email: str | None = None
    role: str
    status: str
    last_login_at: datetime | None = None
    created_at: datetime | None = None


class AdminUserDetail(AdminUserListItem):
    generation_count: int = 0


class AdminUserStatusResponse(BaseModel):
    id: int
    status: str


class PaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[dict[str, Any]]
