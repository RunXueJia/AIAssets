import asyncio

from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models import *  # noqa: F403
from app.services.auth import seed_rbac


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await seed_rbac(db)


if __name__ == "__main__":
    asyncio.run(init_db())
