from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Iterator
from dataclasses import dataclass
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, Column, DateTime, Integer, MetaData, String, Table, insert, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints import admin_records, llm_configs, planning_records
from app.core.auth import get_auth_service
from app.core.exceptions import register_exception_handlers
from app.core.security import create_token, hash_secret, utc_now
from app.db.session import get_db_session
from app.models.user import LoginSession, User
from app.services.auth import AuthService


@dataclass
class PermissionClient:
    client: TestClient
    session_factory: async_sessionmaker[AsyncSession]


class FakePlanningRecordsService:
    def __init__(self) -> None:
        self.last_user_id: int | None = None

    async def list_planning_records(
        self,
        _db: AsyncSession,
        *,
        user_id: int,
        page: int,
        page_size: int,
        status: str | None = None,
        keyword: str | None = None,
    ) -> dict:
        self.last_user_id = user_id
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "items": [],
            "filters": {"status": status, "keyword": keyword},
        }


class FakeAdminRecordsService:
    async def list_admin_generation_records(
        self,
        _db: AsyncSession,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        transport_mode: str | None = None,
        user_keyword: str | None = None,
    ) -> dict:
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "items": [],
            "filters": {
                "status": status,
                "transport_mode": transport_mode,
                "user_keyword": user_keyword,
            },
        }


class FakeLlmConfigsService:
    def __init__(self) -> None:
        self.last_operator_id: int | None = None

    async def create_config(
        self,
        _db: AsyncSession,
        *,
        payload,
        operator_id: int,
    ) -> dict:
        self.last_operator_id = operator_id
        return {"id": 1, "api_key_masked": payload.api_key[:2] + "-****"}


def create_auth_schema() -> MetaData:
    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("username", String(64)),
        Column("nickname", String(64)),
        Column("email", String(128)),
        Column("phone", String(32)),
        Column("password_hash", String(255)),
        Column("role", String(20), nullable=False),
        Column("status", String(20), nullable=False),
        Column("guest_token_hash", String(128)),
        Column("last_login_at", DateTime),
        Column("created_at", DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False),
        Column("updated_at", DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False),
        Column("deleted_at", DateTime),
    )
    Table(
        "login_sessions",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("user_id", BigInteger, nullable=False),
        Column("session_token_hash", String(128), nullable=False),
        Column("refresh_token_hash", String(128)),
        Column("client_type", String(20), nullable=False),
        Column("ip_address", String(64)),
        Column("user_agent", String(500)),
        Column("expires_at", DateTime, nullable=False),
        Column("revoked_at", DateTime),
        Column("created_at", DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False),
        Column("updated_at", DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False),
    )
    return metadata


async def create_user_token(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: int,
    role: str,
    status: str = "active",
) -> str:
    token = create_token(
        {"sub": str(user_id), "type": "access", "role": role},
        AuthService()._secret_key,
        expires_delta=timedelta(hours=2),
    )
    now = utc_now()
    async with session_factory() as session:
        await session.execute(
            insert(User).values(
                id=user_id,
                username=f"{role}_{user_id}",
                nickname=f"{role}-{user_id}",
                role=role,
                status=status,
                created_at=now,
                updated_at=now,
            )
        )
        await session.execute(
            insert(LoginSession).values(
                user_id=user_id,
                session_token_hash=hash_secret(token),
                refresh_token_hash=hash_secret(f"refresh-{user_id}"),
                client_type="web",
                expires_at=now + timedelta(days=30),
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()
    return token


def make_permission_app(
    session_factory: async_sessionmaker[AsyncSession],
    planning_service: FakePlanningRecordsService,
    llm_service: FakeLlmConfigsService,
) -> FastAPI:
    async def override_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(planning_records.router, prefix="/api/v1")
    app.include_router(admin_records.router, prefix="/api/v1")
    app.include_router(llm_configs.router, prefix="/api/v1")
    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_auth_service] = lambda: AuthService()

    planning_records.service = planning_service
    admin_records.service = FakeAdminRecordsService()
    llm_configs.service = llm_service
    return app


@pytest.fixture()
def permission_client() -> Iterator[
    tuple[PermissionClient, FakePlanningRecordsService, FakeLlmConfigsService]
]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    metadata = create_auth_schema()

    async def create_schema() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    asyncio.run(create_schema())

    planning_service = FakePlanningRecordsService()
    llm_service = FakeLlmConfigsService()
    original_planning_service = planning_records.service
    original_admin_records_service = admin_records.service
    original_llm_service = llm_configs.service
    app = make_permission_app(session_factory, planning_service, llm_service)

    try:
        with TestClient(app) as test_client:
            yield PermissionClient(test_client, session_factory), planning_service, llm_service
    finally:
        planning_records.service = original_planning_service
        admin_records.service = original_admin_records_service
        llm_configs.service = original_llm_service
        asyncio.run(engine.dispose())


def test_planning_records_requires_authentication(
    permission_client: tuple[
        PermissionClient, FakePlanningRecordsService, FakeLlmConfigsService
    ],
) -> None:
    client, _, _ = permission_client

    response = client.client.get("/api/v1/planning/records")

    assert response.status_code == 401
    assert response.json() == {"code": 401, "message": "请先登录", "data": None}


def test_planning_records_uses_current_user_id(
    permission_client: tuple[
        PermissionClient, FakePlanningRecordsService, FakeLlmConfigsService
    ],
) -> None:
    client, planning_service, _ = permission_client
    token = asyncio.run(
        create_user_token(client.session_factory, user_id=12, role="user")
    )

    response = client.client.get(
        "/api/v1/planning/records",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert planning_service.last_user_id == 12


def test_admin_records_rejects_non_admin_role(
    permission_client: tuple[
        PermissionClient, FakePlanningRecordsService, FakeLlmConfigsService
    ],
) -> None:
    client, _, _ = permission_client
    token = asyncio.run(
        create_user_token(client.session_factory, user_id=12, role="user")
    )

    response = client.client.get(
        "/api/v1/admin/generation_records",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"code": 403, "message": "无管理员权限", "data": None}


def test_admin_llm_config_uses_admin_operator_id(
    permission_client: tuple[
        PermissionClient, FakePlanningRecordsService, FakeLlmConfigsService
    ],
) -> None:
    client, _, llm_service = permission_client
    token = asyncio.run(
        create_user_token(client.session_factory, user_id=1, role="admin")
    )

    response = client.client.post(
        "/api/v1/admin/llm_configs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "默认模型",
            "provider": "openai-compatible",
            "base_url": "https://api.example.com/v1",
            "model_name": "gpt-4.1-mini",
            "api_key": "sk-test",
        },
    )

    assert response.status_code == 200
    assert llm_service.last_operator_id == 1
