import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.endpoints import admin_users
from app.core.exceptions import AppException
from app.services.admin_users import AdminUsersService


def make_user(**overrides):
    values = {
        "id": 12,
        "username": "route_user",
        "nickname": "路书用户",
        "email": "user@example.com",
        "role": "user",
        "status": "active",
        "last_login_at": datetime(2026, 5, 21, 9, 30, 0),
        "created_at": datetime(2026, 5, 21, 9, 0, 0),
        "deleted_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_admin_user_router_exposes_integration_contract_paths() -> None:
    paths = {route.path for route in admin_users.router.routes}

    assert "/admin/users" in paths
    assert "/admin/users/{user_id}" in paths
    assert "/admin/users/{user_id}/disable" in paths
    assert "/admin/users/{user_id}/enable" in paths


def test_list_users_returns_paginated_payload() -> None:
    repo = SimpleNamespace(list_users=AsyncMock(return_value=(1, [make_user()])))
    service = AdminUsersService(repo=repo)

    data = asyncio.run(
        service.list_users(
            db=SimpleNamespace(),
            page=1,
            page_size=20,
            keyword="route",
            status="active",
            role="user",
        )
    )

    assert data["total"] == 1
    assert data["items"][0]["username"] == "route_user"
    assert data["items"][0]["created_at"] == "2026-05-21T09:00:00"


def test_get_user_detail_includes_generation_count() -> None:
    repo = SimpleNamespace(
        get_user=AsyncMock(return_value=make_user()),
        count_generation_records=AsyncMock(return_value=18),
    )
    service = AdminUsersService(repo=repo)

    data = asyncio.run(service.get_user_detail(db=SimpleNamespace(), user_id=12))

    assert data["id"] == 12
    assert data["generation_count"] == 18


def test_change_user_status_commits() -> None:
    user = make_user()

    async def change_status(_db, *, user, status):
        user.status = status
        return user

    repo = SimpleNamespace(
        get_user=AsyncMock(return_value=user),
        change_status=change_status,
    )
    db = SimpleNamespace(commit=AsyncMock())
    service = AdminUsersService(repo=repo)

    data = asyncio.run(service.change_user_status(db=db, user_id=12, status="disabled"))

    assert data == {"id": 12, "status": "disabled"}
    db.commit.assert_awaited_once()


def test_disable_admin_user_rejected() -> None:
    repo = SimpleNamespace(get_user=AsyncMock(return_value=make_user(role="admin")))
    service = AdminUsersService(repo=repo)

    with pytest.raises(AppException) as exc_info:
        asyncio.run(
            service.change_user_status(
                db=SimpleNamespace(),
                user_id=1,
                status="disabled",
            )
        )

    assert exc_info.value.code == 409
