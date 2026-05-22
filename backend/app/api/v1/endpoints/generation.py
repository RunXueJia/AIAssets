from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.auth import get_current_actor
from app.core.exceptions import AppException
from app.core.responses import ApiResponse, success_response
from app.db.session import get_sessionmaker
from app.schemas.generation import GenerateStreamRequest
from app.schemas.records import RecordActor
from app.services.generation import DatabaseGenerationRecordStore, GenerationService

router = APIRouter(prefix="/planning", tags=["planning"])


def get_generation_service(
    actor: Annotated[RecordActor, Depends(get_current_actor)],
) -> GenerationService:
    return GenerationService(
        record_store=DatabaseGenerationRecordStore(
            get_sessionmaker(),
            user_id=actor.user_id,
            source_client="web",
        )
    )


@router.post("/generate_stream")
async def generate_stream(
    request: GenerateStreamRequest,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> StreamingResponse:
    async def event_source() -> AsyncIterator[str]:
        async for event in service.stream_generation(request):
            yield service.format_sse(event)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/cancel/{record_id}", response_model=ApiResponse)
async def cancel_generation(
    record_id: int,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> ApiResponse:
    data = await service.cancel_generation(record_id)
    if data["status"] == "not_found":
        raise AppException("记录不存在", code=404, status_code=404)
    return success_response(data=data, message="已取消")
