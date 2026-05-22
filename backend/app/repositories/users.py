from __future__ import annotations

from datetime import datetime

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import LoginSession, User


class UserRepository:
    async def get_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        result = await db.execute(
            select(User).where(User.username == username, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_account(self, db: AsyncSession, account: str) -> User | None:
        result = await db.execute(
            select(User).where(
                or_(User.username == account, User.email == account),
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_guest_token_hash(
        self,
        db: AsyncSession,
        guest_token_hash: str,
    ) -> User | None:
        result = await db.execute(
            select(User).where(
                User.guest_token_hash == guest_token_hash,
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        db: AsyncSession,
        *,
        username: str | None,
        password_hash: str | None,
        nickname: str | None,
        email: str | None,
        role: str,
        status: str = "active",
        guest_token_hash: str | None = None,
    ) -> User:
        user = User(
            username=username,
            password_hash=password_hash,
            nickname=nickname,
            email=email,
            role=role,
            status=status,
            guest_token_hash=guest_token_hash,
        )
        db.add(user)
        await db.flush()
        return user

    async def touch_last_login(
        self,
        db: AsyncSession,
        user: User,
        *,
        logged_in_at: datetime,
    ) -> None:
        user.last_login_at = logged_in_at
        await db.flush()


class LoginSessionRepository:
    async def get_by_session_token_hash(
        self,
        db: AsyncSession,
        session_token_hash: str,
    ) -> LoginSession | None:
        result = await db.execute(
            select(LoginSession).where(
                LoginSession.session_token_hash == session_token_hash,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_refresh_token_hash(
        self,
        db: AsyncSession,
        refresh_token_hash: str,
    ) -> LoginSession | None:
        result = await db.execute(
            select(LoginSession).where(
                LoginSession.refresh_token_hash == refresh_token_hash,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        session_token_hash: str,
        refresh_token_hash: str,
        client_type: str,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> LoginSession:
        session = LoginSession(
            user_id=user_id,
            session_token_hash=session_token_hash,
            refresh_token_hash=refresh_token_hash,
            client_type=client_type,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        db.add(session)
        await db.flush()
        return session

    async def revoke(
        self, db: AsyncSession, session: LoginSession, *, revoked_at: datetime
    ) -> None:
        session.revoked_at = revoked_at
        await db.flush()

    async def revoke_by_session_token_hash(
        self,
        db: AsyncSession,
        session_token_hash: str,
        *,
        revoked_at: datetime,
    ) -> int:
        result = await db.execute(
            update(LoginSession)
            .where(
                LoginSession.session_token_hash == session_token_hash,
                LoginSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await db.flush()
        return result.rowcount or 0
