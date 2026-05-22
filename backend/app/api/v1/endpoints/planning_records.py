from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_actor
from app.core.responses import ApiResponse, success_response
from app.db.session import get_db_session
from app.schemas.records import RecordActor, RegenerateRecordRequest
from app.services.records import RecordsService

router = APIRouter(prefix="/planning", tags=["planning-records"])
service = RecordsService()


@router.get("/records", response_model=ApiResponse)
async def list_planning_records(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    actor: Annotated[RecordActor, Depends(get_current_actor)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: str | None = None,
    keyword: str | None = None,
) -> ApiResponse:
    data = await service.list_planning_records(
        db,
        user_id=actor.user_id,
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword,
    )
    return success_response(data=data)


@router.get("/records/{record_id}", response_model=ApiResponse)
async def get_planning_record_detail(
    record_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    actor: Annotated[RecordActor, Depends(get_current_actor)],
) -> ApiResponse:
    data = await service.get_planning_record_detail(
        db,
        user_id=actor.user_id,
        record_id=record_id,
    )
    return success_response(data=data)


@router.get("/records/{record_id}/route_map", response_model=ApiResponse)
async def get_planning_route_map(
    record_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    actor: Annotated[RecordActor, Depends(get_current_actor)],
) -> ApiResponse:
    data = await service.get_planning_route_map(
        db,
        user_id=actor.user_id,
        record_id=record_id,
    )
    return success_response(data=data)


@router.post("/records/{record_id}/regenerate", response_model=ApiResponse)
async def regenerate_planning_record(
    record_id: int,
    payload: RegenerateRecordRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    actor: Annotated[RecordActor, Depends(get_current_actor)],
) -> ApiResponse:
    data = await service.regenerate_record(
        db,
        user_id=actor.user_id,
        record_id=record_id,
        payload=payload,
    )
    return success_response(data=data, message="已创建重新生成任务")
