from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.responses import ApiResponse, success_response
from app.schemas.auth import (
    GuestSessionRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    UserPublic,
)
from app.services.auth import AuthService, RequestContext

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    return AuthService()


async def get_auth_db_session() -> AsyncGenerator[AsyncSession, None]:
    from app.db.session import get_db_session

    async for session in get_db_session():
        yield session


def build_context(request: Request, client_type: str = "web") -> RequestContext:
    return RequestContext(
        client_type=client_type,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


@router.post("/register", response_model=ApiResponse)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_auth_db_session)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse:
    data = await service.register(
        db,
        username=payload.username,
        password=payload.password,
        nickname=payload.nickname,
        email=str(payload.email) if payload.email else None,
        context=build_context(request, "web"),
    )
    return success_response(data=data, message="注册成功")


@router.post("/login", response_model=ApiResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_auth_db_session)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse:
    data = await service.login(
        db,
        account=payload.account,
        password=payload.password,
        context=build_context(request, payload.client_type),
    )
    return success_response(data=data, message="登录成功")


@router.post("/guest_session", response_model=ApiResponse)
async def guest_session(
    payload: GuestSessionRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_auth_db_session)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse:
    data = await service.guest_session(
        db,
        client_id=payload.client_id,
        context=build_context(request, "web"),
    )
    return success_response(data=data)


@router.post("/refresh_token", response_model=ApiResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_auth_db_session)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse:
    data = await service.refresh_token(
        db,
        refresh_token=payload.refresh_token,
        context=build_context(request, "web"),
    )
    return success_response(data=data)


@router.get("/me", response_model=ApiResponse)
async def me(
    db: Annotated[AsyncSession, Depends(get_auth_db_session)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> ApiResponse:
    access_token = extract_bearer_token(authorization)
    if access_token is None:
        raise AppException("请先登录", code=401, status_code=401)

    user = await service.authenticate_access_token(db, access_token=access_token)
    return success_response(data=UserPublic.model_validate(user))


@router.post("/logout", response_model=ApiResponse)
async def logout(
    db: Annotated[AsyncSession, Depends(get_auth_db_session)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> ApiResponse:
    await service.logout(db, access_token=extract_bearer_token(authorization))
    return success_response(message="已退出")
