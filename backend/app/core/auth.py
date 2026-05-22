from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.db.session import get_db_session
from app.schemas.records import RecordActor
from app.services.auth import AuthService


def get_auth_service() -> AuthService:
    return AuthService()


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


async def get_current_actor(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> RecordActor:
    access_token = extract_bearer_token(authorization)
    if access_token is None:
        raise AppException("请先登录", code=401, status_code=401)

    try:
        user = await service.authenticate_access_token(db, access_token=access_token)
    except (KeyError, TypeError, ValueError) as exc:
        raise AppException("Token 已失效", code=401, status_code=401) from exc

    return RecordActor(user_id=user.id, role=user.role)


async def require_admin_actor(
    actor: Annotated[RecordActor, Depends(get_current_actor)],
) -> RecordActor:
    if actor.role != "admin":
        raise AppException("无管理员权限", code=403, status_code=403)
    return actor
