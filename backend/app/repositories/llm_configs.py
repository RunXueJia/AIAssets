from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LlmConfig


class LlmConfigsRepository:
    async def list_configs(
        self,
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
    ) -> tuple[int, list[LlmConfig]]:
        filters = self._filters(status=status)
        total = await self._count(db, select(LlmConfig).where(*filters))
        stmt = (
            select(LlmConfig)
            .where(*filters)
            .order_by(LlmConfig.created_at.desc(), LlmConfig.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        return total, list(result.scalars().all())

    async def get_config(self, db: AsyncSession, *, config_id: int) -> LlmConfig | None:
        result = await db.execute(
            select(LlmConfig).where(LlmConfig.id == config_id, LlmConfig.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_active_default_config(self, db: AsyncSession) -> LlmConfig | None:
        stmt = (
            select(LlmConfig)
            .where(
                LlmConfig.deleted_at.is_(None),
                LlmConfig.status == "enabled",
            )
            .order_by(LlmConfig.is_default.desc(), LlmConfig.updated_at.desc(), LlmConfig.id.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_config(self, db: AsyncSession, *, config: LlmConfig) -> LlmConfig:
        db.add(config)
        await db.flush()
        return config

    async def clear_default(self, db: AsyncSession) -> None:
        result = await db.execute(
            select(LlmConfig).where(LlmConfig.deleted_at.is_(None), LlmConfig.is_default.is_(True))
        )
        for config in result.scalars().all():
            config.is_default = False
        await db.flush()

    async def _count(self, db: AsyncSession, stmt: Select[tuple[Any, ...]]) -> int:
        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        result = await db.execute(count_stmt)
        return int(result.scalar_one())

    def _filters(self, *, status: str | None = None) -> list[Any]:
        filters: list[Any] = [LlmConfig.deleted_at.is_(None)]
        if status:
            filters.append(LlmConfig.status == status)
        return filters
