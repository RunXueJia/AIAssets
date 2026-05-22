from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin_actor
from app.core.responses import ApiResponse, success_response
from app.db.session import get_db_session
from app.schemas.records import RecordActor
from app.services.admin_users import AdminUsersService

router = APIRouter(prefix="/admin", tags=["admin-users"])
service = AdminUsersService()


@router.get("/users", response_model=ApiResponse)
async def list_admin_users(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    keyword: str | None = None,
    status: str | None = None,
    role: str | None = None,
) -> ApiResponse:
    data = await service.list_users(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
        role=role,
    )
    return success_response(data=data)


@router.get("/users/{user_id}", response_model=ApiResponse)
async def get_admin_user_detail(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.get_user_detail(db, user_id=user_id)
    return success_response(data=data)


@router.post("/users/{user_id}/disable", response_model=ApiResponse)
async def disable_admin_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.change_user_status(db, user_id=user_id, status="disabled")
    return success_response(data=data, message="操作成功")


@router.post("/users/{user_id}/enable", response_model=ApiResponse)
async def enable_admin_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.change_user_status(db, user_id=user_id, status="active")
    return success_response(data=data, message="操作成功")
