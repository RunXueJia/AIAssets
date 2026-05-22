from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_SECONDS,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_token,
    decode_token,
    hash_password,
    hash_secret,
    utc_now,
    verify_password,
)
from app.models.user import LoginSession, User
from app.repositories.users import LoginSessionRepository, UserRepository
from app.schemas.auth import AuthData, RefreshTokenData, UserPublic

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123456"
DEFAULT_ADMIN_NICKNAME = "管理员"


@dataclass(frozen=True)
class RequestContext:
    client_type: str = "web"
    ip_address: str | None = None
    user_agent: str | None = None


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository | None = None,
        session_repo: LoginSessionRepository | None = None,
    ) -> None:
        self.user_repo = user_repo or UserRepository()
        self.session_repo = session_repo or LoginSessionRepository()
        self.settings = get_settings()

    async def ensure_default_admin(self, db: AsyncSession) -> User:
        admin = await self.user_repo.get_by_username(db, DEFAULT_ADMIN_USERNAME)
        if admin:
            return admin

        try:
            admin = await self.user_repo.create_user(
                db,
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                nickname=DEFAULT_ADMIN_NICKNAME,
                email=None,
                role="admin",
                status="active",
            )
            await db.commit()
        except IntegrityError:
            await db.rollback()
            admin = await self.user_repo.get_by_username(db, DEFAULT_ADMIN_USERNAME)
            if admin is None:
                raise
        return admin

    async def register(
        self,
        db: AsyncSession,
        *,
        username: str,
        password: str,
        nickname: str | None,
        email: str | None,
        context: RequestContext,
    ) -> AuthData:
        if await self.user_repo.get_by_username(db, username):
            raise AppException("用户名已存在", code=409, status_code=409)
        if email and await self.user_repo.get_by_email(db, email):
            raise AppException("邮箱已存在", code=409, status_code=409)

        try:
            user = await self.user_repo.create_user(
                db,
                username=username,
                password_hash=hash_password(password),
                nickname=nickname or username,
                email=email,
                role="user",
                status="active",
            )
            auth_data = await self._issue_tokens(db, user=user, context=context)
            await db.commit()
            return auth_data
        except IntegrityError as exc:
            await db.rollback()
            raise AppException("用户已存在", code=409, status_code=409) from exc

    async def login(
        self,
        db: AsyncSession,
        *,
        account: str,
        password: str,
        context: RequestContext,
    ) -> AuthData:
        await self.ensure_default_admin(db)
        user = await self.user_repo.get_by_account(db, account)
        if user is None or not verify_password(password, user.password_hash):
            raise AppException("账号或密码错误", code=401, status_code=401)
        if user.status != "active":
            raise AppException("账号已被禁用", code=403, status_code=403)

        auth_data = await self._issue_tokens(db, user=user, context=context)
        await db.commit()
        return auth_data

    async def guest_session(
        self,
        db: AsyncSession,
        *,
        client_id: str,
        context: RequestContext,
    ) -> AuthData:
        client_hash = hash_secret(client_id)
        user = await self.user_repo.get_by_guest_token_hash(db, client_hash)

        if user is None:
            user = await self.user_repo.create_user(
                db,
                username=None,
                password_hash=None,
                nickname="游客",
                email=None,
                role="guest",
                status="active",
                guest_token_hash=client_hash,
            )
        elif user.status != "active":
            raise AppException("账号已被禁用", code=403, status_code=403)

        auth_data = await self._issue_tokens(db, user=user, context=context)
        await db.commit()
        return auth_data

    async def refresh_token(
        self,
        db: AsyncSession,
        *,
        refresh_token: str,
        context: RequestContext,
    ) -> RefreshTokenData:
        payload = decode_token(refresh_token, self._secret_key)
        if payload is None or payload.get("type") != "refresh":
            raise AppException("Token 已失效", code=401, status_code=401)

        session = await self.session_repo.get_by_refresh_token_hash(
            db,
            hash_secret(refresh_token),
        )
        if not self._is_session_active(session):
            raise AppException("Token 已失效", code=401, status_code=401)

        user = await self.user_repo.get_by_id(db, int(payload["sub"]))
        if user is None or user.status != "active" or session.user_id != user.id:
            raise AppException("Token 已失效", code=401, status_code=401)

        await self.session_repo.revoke(db, session, revoked_at=utc_now())
        auth_data = await self._issue_tokens(db, user=user, context=context)
        await db.commit()
        return RefreshTokenData(
            access_token=auth_data.access_token,
            refresh_token=auth_data.refresh_token,
            expires_in=auth_data.expires_in,
        )

    async def logout(self, db: AsyncSession, *, access_token: str | None) -> None:
        if access_token:
            await self.session_repo.revoke_by_session_token_hash(
                db,
                hash_secret(access_token),
                revoked_at=utc_now(),
            )
            await db.commit()

    async def authenticate_access_token(
        self,
        db: AsyncSession,
        *,
        access_token: str,
    ) -> User:
        payload = decode_token(access_token, self._secret_key)
        if payload is None or payload.get("type") != "access":
            raise AppException("Token 已失效", code=401, status_code=401)

        session = await self.session_repo.get_by_session_token_hash(
            db,
            hash_secret(access_token),
        )
        if not self._is_session_active(session):
            raise AppException("Token 已失效", code=401, status_code=401)

        user = await self.user_repo.get_by_id(db, int(payload["sub"]))
        if user is None or user.status != "active" or session.user_id != user.id:
            raise AppException("Token 已失效", code=401, status_code=401)
        return user

    async def _issue_tokens(
        self,
        db: AsyncSession,
        *,
        user: User,
        context: RequestContext,
    ) -> AuthData:
        now = utc_now()
        access_token = create_token(
            {"sub": str(user.id), "type": "access", "role": user.role},
            self._secret_key,
            expires_delta=timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS),
        )
        refresh_token = create_token(
            {"sub": str(user.id), "type": "refresh", "role": user.role},
            self._secret_key,
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self.session_repo.create(
            db,
            user_id=user.id,
            session_token_hash=hash_secret(access_token),
            refresh_token_hash=hash_secret(refresh_token),
            client_type=context.client_type,
            expires_at=now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=context.ip_address,
            user_agent=context.user_agent,
        )
        await self.user_repo.touch_last_login(db, user, logged_in_at=now)
        return AuthData(
            user=UserPublic.model_validate(user),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
        )

    def _is_session_active(self, session: LoginSession | None) -> bool:
        if session is None:
            return False
        now = utc_now()
        return session.revoked_at is None and session.expires_at > now

    @property
    def _secret_key(self) -> str:
        return (
            os.getenv("BACKEND_AUTH_SECRET_KEY")
            or os.getenv("BACKEND_SECRET_KEY")
            or f"{self.settings.app_name}:{self.settings.app_env}:local-auth-secret"
        )
