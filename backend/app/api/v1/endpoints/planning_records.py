import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_actor
from app.core.exceptions import AppException
from app.core.responses import ApiResponse, success_response
from app.db.session import get_db_session, get_sessionmaker
from app.schemas.generation import GenerateStreamRequest, GenerationStreamEvent
from app.schemas.records import RecordActor, RegenerateRecordRequest
from app.services.generation import DatabaseGenerationRecordStore, GenerationService
from app.services.records import RecordsService

router = APIRouter(prefix="/planning", tags=["planning-records"])
service = RecordsService()
STREAM_EVENT_LIMIT = 100
STREAM_IDLE_TIMEOUT_S = 60
STREAM_POLL_INTERVAL_S = 0.5
TERMINAL_RECORD_STATUSES = {"completed", "failed", "canceled"}


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


@router.post("/records/{record_id}/generate_stream")
async def generate_existing_planning_record_stream(
    record_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    actor: Annotated[RecordActor, Depends(get_current_actor)],
) -> StreamingResponse:
    record = await service.get_stream_record(db, user_id=actor.user_id, record_id=record_id)
    if record.status != "pending":
        raise AppException("只有等待中的记录可以开始生成", code=409, status_code=409)
    detail = await service.get_planning_record_detail(
        db,
        user_id=actor.user_id,
        record_id=record_id,
    )
    request = _request_from_detail(detail)

    generation_service = GenerationService(
        record_store=DatabaseGenerationRecordStore(
            get_sessionmaker(),
            user_id=actor.user_id,
            source_client="web",
        )
    )

    async def event_source() -> AsyncIterator[str]:
        async for event in generation_service.stream_generation(
            request,
            existing_record_id=record_id,
        ):
            yield generation_service.format_sse(event)

    return _sse_response(event_source())


def _request_from_detail(detail: dict) -> GenerateStreamRequest:
    record = detail.get("record") or {}
    input_snapshot = detail.get("input") or {}
    return GenerateStreamRequest(
        origin=input_snapshot.get("origin_text") or record.get("origin_text"),
        destination=input_snapshot.get("destination_text") or record.get("destination_text"),
        range=input_snapshot.get("range_text") or record.get("range_text"),
        transport_mode=record.get("transport_mode") or "mixed",
        travel_date=input_snapshot.get("travel_date"),
        people_count=input_snapshot.get("people_count"),
        preferences=input_snapshot.get("preferences") or [],
        avoidances=input_snapshot.get("avoidances") or [],
    )


@router.get("/records/{record_id}/stream")
async def stream_planning_record_events(
    record_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    actor: Annotated[RecordActor, Depends(get_current_actor)],
    after_sequence: Annotated[int, Query(ge=0)] = 0,
) -> StreamingResponse:
    await service.get_stream_record(db, user_id=actor.user_id, record_id=record_id)

    async def event_source() -> AsyncIterator[str]:
        last_sequence = after_sequence
        idle_elapsed = 0.0
        while idle_elapsed < STREAM_IDLE_TIMEOUT_S:
            async with get_sessionmaker()() as stream_db:
                events = await service.list_stream_events(
                    stream_db,
                    user_id=actor.user_id,
                    record_id=record_id,
                    after_sequence=last_sequence,
                    limit=STREAM_EVENT_LIMIT,
                )
            if events:
                idle_elapsed = 0.0
                for item in events:
                    last_sequence = max(last_sequence, int(item["sequence_no"]))
                    yield _format_stored_sse(item)
                if events[-1]["event"] in {"done", "error"}:
                    return
                continue
            async with get_sessionmaker()() as stream_db:
                record = await service.get_stream_record(
                    stream_db,
                    user_id=actor.user_id,
                    record_id=record_id,
                )
            if record.status in TERMINAL_RECORD_STATUSES:
                return
            await asyncio.sleep(STREAM_POLL_INTERVAL_S)
            idle_elapsed += STREAM_POLL_INTERVAL_S

    return _sse_response(event_source())


@router.post("/records/{record_id}/retry")
async def retry_planning_record(
    record_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    actor: Annotated[RecordActor, Depends(get_current_actor)],
) -> StreamingResponse:
    retry_data = await service.retry_planning_record(
        db,
        user_id=actor.user_id,
        record_id=record_id,
    )
    request = GenerateStreamRequest.model_validate(retry_data["request_payload"])
    generation_service = GenerationService(
        record_store=DatabaseGenerationRecordStore(
            get_sessionmaker(),
            user_id=actor.user_id,
            source_client="web",
        )
    )

    async def event_source() -> AsyncIterator[str]:
        async for event in generation_service.stream_generation(
            request,
            existing_record_id=retry_data["record_id"],
        ):
            yield generation_service.format_sse(event)

    return _sse_response(event_source())


def _format_stored_sse(item: dict) -> str:
    event = GenerationStreamEvent(event=item["event"], data=item["data"])
    payload = json.dumps(event.data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event.event}\ndata: {payload}\n\n"


def _sse_response(event_source: AsyncIterator[str]) -> StreamingResponse:
    return StreamingResponse(
        event_source,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
