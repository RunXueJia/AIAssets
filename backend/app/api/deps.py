#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:45
# @File     : deps.py
# @Desc     : FastAPI dependencies.

from collections.abc import Callable

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.entities import Permission, Role, RolePermission, User
from app.schemas.auth import CurrentUser


def _load_permissions(db: Session, role_id: str) -> tuple[str, list[str]]:
    role = db.get(Role, role_id)
    if role is None:
        return "", []
    permission_ids = [
        item.permission_id for item in db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
    ]
    if not permission_ids:
        return role.code, []
    permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    return role.code, [item.code for item in permissions]


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AppError(40100, "未登录或 Token 过期", 401)
    payload = decode_access_token(authorization.split(" ", 1)[1])
    user = db.get(User, payload.get("sub", ""))
    if user is None or user.deleted_at is not None or user.status != "enabled":
        raise AppError(40100, "未登录或 Token 过期", 401)
    role_code, permissions = _load_permissions(db, user.role_id)
    return CurrentUser(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=role_code,
        permissions=permissions,
    )


def require_permission(permission: str) -> Callable[[CurrentUser], CurrentUser]:
    def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if "*" not in current_user.permissions and permission not in current_user.permissions:
            raise AppError(40300, "当前账号无权限操作", 403)
        return current_user

    return checker
