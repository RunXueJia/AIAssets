from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GenerationRecord, User


class AdminUsersRepository:
    async def list_users(
        self,
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        keyword: str | None = None,
        status: str | None = None,
        role: str | None = None,
    ) -> tuple[int, list[User]]:
        filters = self._user_filters(keyword=keyword, status=status, role=role)
        total = await self._count(db, select(User).where(*filters))
        stmt = (
            select(User)
            .where(*filters)
            .order_by(User.created_at.desc(), User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        return total, list(result.scalars().all())

    async def get_user(self, db: AsyncSession, *, user_id: int) -> User | None:
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def count_generation_records(self, db: AsyncSession, *, user_id: int) -> int:
        result = await db.execute(
            select(func.count()).select_from(
                select(GenerationRecord.id)
                .where(
                    GenerationRecord.user_id == user_id,
                    GenerationRecord.deleted_at.is_(None),
                )
                .subquery()
            )
        )
        return int(result.scalar_one())

    async def change_status(self, db: AsyncSession, *, user: User, status: str) -> User:
        user.status = status
        await db.flush()
        return user

    async def _count(self, db: AsyncSession, stmt: Select[tuple[Any, ...]]) -> int:
        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        result = await db.execute(count_stmt)
        return int(result.scalar_one())

    def _user_filters(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        role: str | None = None,
    ) -> list[Any]:
        filters: list[Any] = [User.deleted_at.is_(None)]
        if status:
            filters.append(User.status == status)
        if role:
            filters.append(User.role == role)
        if keyword:
            keyword_like = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    User.username.like(keyword_like),
                    User.nickname.like(keyword_like),
                    User.email.like(keyword_like),
                    User.phone.like(keyword_like),
                )
            )
        return filters
