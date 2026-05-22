from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Iterator
from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, Column, DateTime, Integer, MetaData, String, Table, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints.auth import get_auth_db_session
from app.api.v1.endpoints.auth import router as auth_router
from app.core.exceptions import register_exception_handlers
from app.core.security import hash_secret, verify_password
from app.models.user import LoginSession, User


@dataclass
class AuthClient:
    client: TestClient
    session_factory: async_sessionmaker[AsyncSession]


@pytest.fixture()
def auth_client() -> Iterator[AuthClient]:
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

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

    async def create_schema() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    asyncio.run(create_schema())

    async def override_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(auth_router, prefix="/api/v1")
    app.dependency_overrides[get_auth_db_session] = override_db

    with TestClient(app) as test_client:
        yield AuthClient(client=test_client, session_factory=session_factory)

    asyncio.run(engine.dispose())


async def fetch_user(
    session_factory: async_sessionmaker[AsyncSession],
    username: str | None,
) -> User:
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one()
        session.expunge(user)
        return user


async def fetch_session(
    session_factory: async_sessionmaker[AsyncSession],
    refresh_token_hash: str,
) -> LoginSession:
    async with session_factory() as session:
        result = await session.execute(
            select(LoginSession).where(LoginSession.refresh_token_hash == refresh_token_hash)
        )
        login_session = result.scalar_one()
        session.expunge(login_session)
        return login_session


def test_register_returns_tokens_and_stores_password_hash(auth_client: AuthClient) -> None:
    client = auth_client.client

    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "route_user",
            "password": "password123",
            "nickname": "路书用户",
            "email": "user@example.com",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "注册成功"
    data = body["data"]
    assert data["user"]["username"] == "route_user"
    assert data["user"]["role"] == "user"
    assert data["expires_in"] == 7200
    assert data["access_token"]
    assert data["refresh_token"]

    user = asyncio.run(fetch_user(auth_client.session_factory, "route_user"))
    assert user.password_hash != "password123"
    assert verify_password("password123", user.password_hash)

    login_session = asyncio.run(
        fetch_session(auth_client.session_factory, hash_secret(data["refresh_token"]))
    )
    assert login_session.session_token_hash == hash_secret(data["access_token"])
    assert login_session.session_token_hash != data["access_token"]
    assert login_session.refresh_token_hash == hash_secret(data["refresh_token"])
    assert login_session.refresh_token_hash != data["refresh_token"]


def test_login_initializes_default_admin(auth_client: AuthClient) -> None:
    client = auth_client.client

    response = client.post(
        "/api/v1/auth/login",
        json={"account": "admin", "password": "admin123456", "client_type": "admin"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"
    assert data["access_token"]
    assert data["refresh_token"]

    admin = asyncio.run(fetch_user(auth_client.session_factory, "admin"))
    assert admin.nickname == "管理员"
    assert verify_password("admin123456", admin.password_hash)


def test_guest_session_refresh_and_logout(auth_client: AuthClient) -> None:
    client = auth_client.client

    response = client.post(
        "/api/v1/auth/guest_session",
        json={"client_id": "browser-generated-client-id"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["nickname"] == "游客"
    assert data["user"]["role"] == "guest"

    refresh_response = client.post(
        "/api/v1/auth/refresh_token",
        json={"refresh_token": data["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()["data"]
    assert refreshed["access_token"] != data["access_token"]
    assert refreshed["refresh_token"] != data["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {refreshed['access_token']}"},
    )
    assert logout_response.status_code == 200
    assert logout_response.json() == {"code": 200, "message": "已退出", "data": None}

    expired_response = client.post(
        "/api/v1/auth/refresh_token",
        json={"refresh_token": data["refresh_token"]},
    )
    assert expired_response.status_code == 401


def test_me_returns_current_user(auth_client: AuthClient) -> None:
    client = auth_client.client

    login_response = client.post(
        "/api/v1/auth/login",
        json={"account": "admin", "password": "admin123456", "client_type": "admin"},
    )
    access_token = login_response.json()["data"]["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "id": 1,
        "username": "admin",
        "nickname": "管理员",
        "role": "admin",
        "status": "active",
    }


def test_me_requires_authentication(auth_client: AuthClient) -> None:
    response = auth_client.client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {"code": 401, "message": "请先登录", "data": None}


def test_login_rejects_invalid_password(auth_client: AuthClient) -> None:
    client = auth_client.client

    response = client.post(
        "/api/v1/auth/login",
        json={"account": "admin", "password": "wrong-password", "client_type": "admin"},
    )

    assert response.status_code == 401
    assert response.json()["message"] == "账号或密码错误"
