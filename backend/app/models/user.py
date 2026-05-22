from datetime import datetime

from sqlalchemy import DateTime, Index, String, text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BigIntPrimaryKeyMixin, TimestampMixin


class User(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_role_status", "role", "status"),
        Index("idx_users_created_at", "created_at"),
        {"comment": "用户账号"},
    )

    username: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'user'"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'"))
    guest_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LoginSession(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "login_sessions"
    __table_args__ = (
        Index("idx_login_sessions_user_id", "user_id"),
        Index("idx_login_sessions_expires_at", "expires_at"),
        Index("idx_login_sessions_revoked_at", "revoked_at"),
        {"comment": "登录会话"},
    )

    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    session_token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    refresh_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    client_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'web'")
    )
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
