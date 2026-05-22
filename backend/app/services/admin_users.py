from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.repositories.admin_users import AdminUsersRepository
from app.schemas.admin_users import (
    AdminUserDetail,
    AdminUserListItem,
    AdminUserStatusResponse,
    PaginationResponse,
)


class AdminUsersService:
    def __init__(self, repo: AdminUsersRepository | None = None) -> None:
        self.repo = repo or AdminUsersRepository()

    async def list_users(
        self,
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        keyword: str | None = None,
        status: str | None = None,
        role: str | None = None,
    ) -> dict[str, Any]:
        page, page_size = self._normalize_pagination(page, page_size)
        total, users = await self.repo.list_users(
            db,
            page=page,
            page_size=page_size,
            keyword=self._blank_to_none(keyword),
            status=self._blank_to_none(status),
            role=self._blank_to_none(role),
        )
        items = [
            AdminUserListItem.model_validate(user, from_attributes=True).model_dump(mode="json")
            for user in users
        ]
        return PaginationResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
        ).model_dump(mode="json")

    async def get_user_detail(self, db: AsyncSession, *, user_id: int) -> dict[str, Any]:
        user = await self.repo.get_user(db, user_id=user_id)
        if user is None:
            raise AppException("用户不存在", code=404, status_code=404)

        generation_count = await self.repo.count_generation_records(db, user_id=user.id)
        return AdminUserDetail(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            email=user.email,
            role=user.role,
            status=user.status,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            generation_count=generation_count,
        ).model_dump(mode="json")

    async def change_user_status(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        status: str,
    ) -> dict[str, Any]:
        user = await self.repo.get_user(db, user_id=user_id)
        if user is None:
            raise AppException("用户不存在", code=404, status_code=404)
        if user.role == "admin" and status == "disabled":
            raise AppException("管理员账号不能禁用", code=409, status_code=409)

        await self.repo.change_status(db, user=user, status=status)
        await db.commit()
        return AdminUserStatusResponse(id=user.id, status=user.status).model_dump(mode="json")

    def _normalize_pagination(self, page: int, page_size: int) -> tuple[int, int]:
        return max(page, 1), min(max(page_size, 1), 100)

    def _blank_to_none(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
