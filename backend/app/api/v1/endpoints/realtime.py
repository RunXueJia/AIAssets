from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.auth import require_admin_actor
from app.core.responses import ApiResponse, success_response
from app.schemas.realtime import RealtimeCategory
from app.schemas.records import RecordActor
from app.services.realtime import RealtimeService, realtime_service

router = APIRouter(prefix="/realtime", tags=["realtime"])


def get_realtime_service() -> RealtimeService:
    return realtime_service


@router.get("/search", response_model=ApiResponse)
async def realtime_search(
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
    service: Annotated[RealtimeService, Depends(get_realtime_service)],
    keyword: Annotated[str, Query(min_length=1, max_length=200)],
    category: RealtimeCategory = "news",
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> ApiResponse:
    data = await service.search(keyword=keyword, category=category, limit=limit)
    return success_response(data=data)
