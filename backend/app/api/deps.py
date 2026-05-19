from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.auth import User
from app.services.auth import get_user_with_permissions, user_permissions

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise UnauthorizedError()
    try:
        payload = decode_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise UnauthorizedError() from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("Token 类型错误")
    return await get_user_with_permissions(db, payload["sub"])


def require_permission(permission: str) -> Callable:
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.is_superuser or permission in user_permissions(user):
            return user
        raise ForbiddenError()

    return dependency
