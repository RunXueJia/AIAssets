from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    async def get(self, db: AsyncSession, item_id: str) -> ModelT | None:
        return await db.get(self.model, item_id)

    async def get_by_field(self, db: AsyncSession, field: str, value: Any) -> ModelT | None:
        stmt = select(self.model).where(getattr(self.model, field) == value)
        return (await db.execute(stmt)).scalars().first()

    async def list(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        keyword_fields: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        order_desc: bool = True,
    ) -> tuple[list[ModelT], int]:
        stmt: Select[tuple[ModelT]] = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)
        filters = filters or {}
        for key, value in filters.items():
            if value is not None and hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
                count_stmt = count_stmt.where(getattr(self.model, key) == value)
        if keyword and keyword_fields:
            conditions = [
                getattr(self.model, field).ilike(f"%{keyword}%")
                for field in keyword_fields
                if hasattr(self.model, field)
            ]
            if conditions:
                condition = conditions[0]
                for item in conditions[1:]:
                    condition = condition | item
                stmt = stmt.where(condition)
                count_stmt = count_stmt.where(condition)
        if hasattr(self.model, "created_at"):
            order_by = self.model.created_at.desc() if order_desc else self.model.created_at.asc()
            stmt = stmt.order_by(order_by)
        total = (await db.execute(count_stmt)).scalar_one()
        result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().unique().all()), total

    async def create(self, db: AsyncSession, data: dict[str, Any]) -> ModelT:
        item = self.model(**data)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def update(self, db: AsyncSession, item: ModelT, data: dict[str, Any]) -> ModelT:
        for key, value in data.items():
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)
        await db.commit()
        await db.refresh(item)
        return item

    async def delete(self, db: AsyncSession, item: ModelT) -> None:
        await db.delete(item)
        await db.commit()
