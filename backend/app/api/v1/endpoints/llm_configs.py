import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin_actor
from app.core.responses import ApiResponse, success_response
from app.db.session import get_db_session
from app.schemas.llm_configs import (
    LlmConfigCreateRequest,
    LlmConfigTestRequest,
    LlmConfigUpdateRequest,
)
from app.schemas.records import RecordActor
from app.services.llm_configs import LlmConfigsService

router = APIRouter(prefix="/admin", tags=["llm-configs"])
service = LlmConfigsService()


@router.get("/llm_configs", response_model=ApiResponse)
async def list_llm_configs(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: str | None = None,
) -> ApiResponse:
    data = await service.list_configs(db, page=page, page_size=page_size, status=status)
    return success_response(data=data)


@router.post("/llm_configs", response_model=ApiResponse)
async def create_llm_config(
    payload: LlmConfigCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.create_config(db, payload=payload, operator_id=actor.user_id)
    return success_response(data=data, message="创建成功")


@router.get("/llm_configs/{config_id}", response_model=ApiResponse)
async def get_llm_config_detail(
    config_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.get_detail(db, config_id=config_id)
    return success_response(data=data)


@router.put("/llm_configs/{config_id}", response_model=ApiResponse)
async def update_llm_config(
    config_id: int,
    payload: LlmConfigUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.update_config(
        db,
        config_id=config_id,
        payload=payload,
        operator_id=actor.user_id,
    )
    return success_response(data=data, message="更新成功")


@router.post("/llm_configs/{config_id}/test", response_model=ApiResponse)
async def test_llm_config(
    config_id: int,
    payload: LlmConfigTestRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.test_config(
        db,
        config_id=config_id,
        test_prompt=payload.test_prompt,
    )
    return success_response(data=data, message="连接测试成功")


@router.post("/llm_configs/{config_id}/test_stream")
async def test_llm_config_stream(
    config_id: int,
    payload: LlmConfigTestRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> StreamingResponse:
    async def event_source():
        async for event in service.stream_test_config(
            db,
            config_id=config_id,
            test_prompt=payload.test_prompt,
        ):
            event_type = str(event.get("type") or "message")
            data = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
            yield f"event: {event_type}\ndata: {data}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/llm_configs/{config_id}/enable", response_model=ApiResponse)
async def enable_llm_config(
    config_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.change_status(db, config_id=config_id, status="enabled")
    return success_response(data=data, message="操作成功")


@router.post("/llm_configs/{config_id}/disable", response_model=ApiResponse)
async def disable_llm_config(
    config_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.change_status(db, config_id=config_id, status="disabled")
    return success_response(data=data, message="操作成功")
