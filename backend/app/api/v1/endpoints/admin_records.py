from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin_actor
from app.core.responses import ApiResponse, success_response
from app.db.session import get_db_session
from app.schemas.records import RecordActor
from app.services.records import RecordsService

router = APIRouter(prefix="/admin", tags=["admin-records"])
service = RecordsService()


@router.get("/generation_records", response_model=ApiResponse)
async def list_admin_generation_records(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: str | None = None,
    transport_mode: str | None = None,
    user_keyword: str | None = None,
) -> ApiResponse:
    data = await service.list_admin_generation_records(
        db,
        page=page,
        page_size=page_size,
        status=status,
        transport_mode=transport_mode,
        user_keyword=user_keyword,
    )
    return success_response(data=data)


@router.get("/generation_records/{record_id}", response_model=ApiResponse)
async def get_admin_generation_record_detail(
    record_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.get_admin_generation_record_detail(db, record_id=record_id)
    return success_response(data=data)


@router.post("/generation_records/{record_id}/retry", response_model=ApiResponse)
async def retry_admin_generation_record(
    record_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.retry_admin_generation_record(db, record_id=record_id)
    return success_response(data=data, message="已创建重试任务")


@router.delete("/generation_records/{record_id}", response_model=ApiResponse)
async def delete_admin_generation_record(
    record_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    await service.delete_admin_generation_record(db, record_id=record_id)
    return success_response(message="已删除")
