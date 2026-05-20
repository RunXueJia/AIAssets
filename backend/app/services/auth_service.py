#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:50
# @File     : auth_service.py
# @Desc     : Authentication service.

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import create_access_token, verify_password
from app.models.entities import Permission, Role, RolePermission, User
from app.schemas.auth import CurrentUser, LoginResponse


def get_user_permissions(db: Session, role_id: str) -> tuple[str, list[str]]:
    role = db.get(Role, role_id)
    if role is None:
        return "", []
    permission_ids = [
        item.permission_id for item in db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
    ]
    permissions = []
    if permission_ids:
        permissions = [item.code for item in db.query(Permission).filter(Permission.id.in_(permission_ids)).all()]
    return role.code, permissions


def login(db: Session, username: str, password: str, ip: str | None = None) -> LoginResponse:
    user = db.query(User).filter(User.username == username, User.deleted_at.is_(None)).one_or_none()
    if user is None or user.status != "enabled" or not verify_password(password, user.password_hash):
        raise AppError(40100, "账号或密码错误，请检查后重试", 401)
    role_code, permissions = get_user_permissions(db, user.role_id)
    token = create_access_token(user.id, permissions)
    user.last_login_at = datetime.now()
    user.last_login_ip = ip
    db.commit()
    return LoginResponse(
        access_token=token,
        expires_in=settings.access_token_expire_seconds,
        user=CurrentUser(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=role_code,
            permissions=permissions,
        ),
    )
