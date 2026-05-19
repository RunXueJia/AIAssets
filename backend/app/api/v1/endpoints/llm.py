from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.crypto import encrypt_text
from app.core.exceptions import NotFoundError
from app.core.response import ok, page_response
from app.core.security import mask_secret
from app.db.session import get_db
from app.models.auth import User
from app.models.llm import LLMCallLog, LLMModel, LLMProvider, LLMStreamChunk, PromptTemplate
from app.repositories.base import BaseRepository
from app.schemas.common import StatusPayload
from app.schemas.llm import (
    LLMCallRetryRequest,
    LLMModelCreate,
    LLMModelUpdate,
    LLMProviderCreate,
    LLMProviderUpdate,
    PromptStreamTestRequest,
    PromptTemplateCreate,
    PromptTemplatePublish,
    PromptTemplateUpdate,
)
from app.services.llm_gateway import LLMGatewayService

router = APIRouter()


def provider_dict(item: LLMProvider) -> dict:
    data = item.to_dict()
    data["api_key"] = mask_secret(data.pop("api_key_encrypted", ""))
    return data


async def list_items(db, model, page, page_size, keyword, keyword_fields, filters=None):
    items, total = await BaseRepository(model).list(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        keyword_fields=keyword_fields,
        filters=filters,
    )
    return items, total


@router.get("/llm_providers/get_llm_provider_list")
async def get_llm_provider_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:provider:read")),
):
    items, total = await list_items(db, LLMProvider, page, page_size, keyword, ["name", "base_url"])
    return page_response([provider_dict(item) for item in items], total, page, page_size)


@router.get("/llm_providers/get_llm_provider_detail/{id}")
async def get_llm_provider_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:provider:read")),
):
    item = await BaseRepository(LLMProvider).get(db, id)
    if not item:
        raise NotFoundError("LLM 供应商不存在")
    return ok(provider_dict(item))


@router.post("/llm_providers/create_llm_provider")
async def create_llm_provider(
    payload: LLMProviderCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:provider:create")),
):
    data = payload.model_dump(exclude={"api_key"})
    data["api_key_encrypted"] = encrypt_text(payload.api_key) if payload.api_key else ""
    item = await BaseRepository(LLMProvider).create(db, data)
    return ok(provider_dict(item))


@router.post("/llm_providers/update_llm_provider")
async def update_llm_provider(
    payload: LLMProviderUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:provider:update")),
):
    repo = BaseRepository(LLMProvider)
    item = await repo.get(db, payload.id)
    if not item:
        raise NotFoundError("LLM 供应商不存在")
    data = payload.model_dump(exclude={"id", "api_key"}, exclude_none=True)
    if payload.api_key:
        data["api_key_encrypted"] = encrypt_text(payload.api_key)
    item = await repo.update(db, item, data)
    return ok(provider_dict(item))


@router.post("/llm_providers/change_llm_provider_status")
async def change_llm_provider_status(
    payload: StatusPayload,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:provider:update")),
):
    repo = BaseRepository(LLMProvider)
    item = await repo.get(db, payload.id)
    if not item:
        raise NotFoundError("LLM 供应商不存在")
    item = await repo.update(db, item, {"status": payload.status})
    return ok(provider_dict(item))


@router.post("/llm_providers/test_llm_provider")
async def test_llm_provider(_: dict, __: User = Depends(require_permission("llm:provider:test"))):
    return ok({"reachable": True, "message": "请通过 Prompt 调试接口验证完整 SSE 调用"})


@router.get("/llm_models/get_llm_model_list")
async def get_llm_model_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    provider_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:model:read")),
):
    items, total = await list_items(
        db,
        LLMModel,
        page,
        page_size,
        keyword,
        ["model_name", "display_name"],
        {"provider_id": provider_id},
    )
    return page_response([item.to_dict() for item in items], total, page, page_size)


@router.get("/llm_models/get_llm_model_detail/{id}")
async def get_llm_model_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:model:read")),
):
    item = await BaseRepository(LLMModel).get(db, id)
    if not item:
        raise NotFoundError("LLM 模型不存在")
    return ok(item.to_dict())


@router.post("/llm_models/create_llm_model")
async def create_llm_model(
    payload: LLMModelCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:model:create")),
):
    item = await BaseRepository(LLMModel).create(db, payload.model_dump())
    return ok(item.to_dict())


@router.post("/llm_models/update_llm_model")
async def update_llm_model(
    payload: LLMModelUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:model:update")),
):
    repo = BaseRepository(LLMModel)
    item = await repo.get(db, payload.id)
    if not item:
        raise NotFoundError("LLM 模型不存在")
    item = await repo.update(db, item, payload.model_dump(exclude={"id"}))
    return ok(item.to_dict())


@router.post("/llm_models/change_llm_model_status")
async def change_llm_model_status(
    payload: StatusPayload,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:model:update")),
):
    repo = BaseRepository(LLMModel)
    item = await repo.get(db, payload.id)
    if not item:
        raise NotFoundError("LLM 模型不存在")
    item = await repo.update(db, item, {"status": payload.status})
    return ok(item.to_dict())


@router.get("/prompt_templates/get_prompt_template_list")
async def get_prompt_template_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    scene: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:prompt:read")),
):
    items, total = await list_items(
        db, PromptTemplate, page, page_size, keyword, ["name", "scene"], {"scene": scene}
    )
    return page_response([item.to_dict() for item in items], total, page, page_size)


@router.get("/prompt_templates/get_prompt_template_detail/{id}")
async def get_prompt_template_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:prompt:read")),
):
    item = await BaseRepository(PromptTemplate).get(db, id)
    if not item:
        raise NotFoundError("Prompt 模板不存在")
    return ok(item.to_dict())


@router.post("/prompt_templates/create_prompt_template")
async def create_prompt_template(
    payload: PromptTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:prompt:create")),
):
    item = await BaseRepository(PromptTemplate).create(db, payload.model_dump())
    return ok(item.to_dict())


@router.post("/prompt_templates/update_prompt_template")
async def update_prompt_template(
    payload: PromptTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:prompt:update")),
):
    repo = BaseRepository(PromptTemplate)
    item = await repo.get(db, payload.id)
    if not item:
        raise NotFoundError("Prompt 模板不存在")
    item = await repo.update(db, item, payload.model_dump(exclude={"id"}))
    return ok(item.to_dict())


@router.post("/prompt_templates/publish_prompt_template")
async def publish_prompt_template(
    payload: PromptTemplatePublish,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:prompt:publish")),
):
    repo = BaseRepository(PromptTemplate)
    item = await repo.get(db, payload.id)
    if not item:
        raise NotFoundError("Prompt 模板不存在")
    item = await repo.update(db, item, {"status": "enabled"})
    return ok(item.to_dict())


@router.post("/prompt_templates/change_prompt_template_status")
async def change_prompt_template_status(
    payload: StatusPayload,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:prompt:update")),
):
    repo = BaseRepository(PromptTemplate)
    item = await repo.get(db, payload.id)
    if not item:
        raise NotFoundError("Prompt 模板不存在")
    item = await repo.update(db, item, {"status": payload.status})
    return ok(item.to_dict())


@router.post("/prompt_templates/stream_test_prompt_template")
async def stream_test_prompt_template(
    payload: PromptStreamTestRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:prompt:test")),
):
    model = await BaseRepository(LLMModel).get(db, payload.model_id)
    template = await BaseRepository(PromptTemplate).get(db, payload.prompt_template_id)
    if not model or not template:
        raise NotFoundError("模型或 Prompt 模板不存在")
    return StreamingResponse(
        LLMGatewayService().stream_prompt(
            db,
            model=model,
            template=template,
            variables=payload.variables,
            target_type="prompt_test",
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/llm_call_logs/get_llm_call_log_list")
async def get_llm_call_log_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:log:read")),
):
    items, total = await list_items(
        db, LLMCallLog, page, page_size, keyword, ["scene", "target_type"], {"status": status}
    )
    return page_response([item.to_dict() for item in items], total, page, page_size)


@router.get("/llm_call_logs/get_llm_call_log_detail/{id}")
async def get_llm_call_log_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:log:read")),
):
    item = await BaseRepository(LLMCallLog).get(db, id)
    if not item:
        raise NotFoundError("LLM 调用日志不存在")
    return ok(item.to_dict())


@router.get("/llm_call_logs/get_llm_cost_summary")
async def get_llm_cost_summary(_: User = Depends(require_permission("llm:log:read"))):
    return ok({"estimated_cost": 0.0})


@router.get("/llm_call_logs/get_llm_stream_chunks/{id}")
async def get_llm_stream_chunks(
    id: str,
    page: int = 1,
    page_size: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("llm:log:read")),
):
    items, total = await BaseRepository(LLMStreamChunk).list(
        db, page=page, page_size=page_size, filters={"call_log_id": id}, order_desc=False
    )
    return page_response([item.to_dict() for item in items], total, page, page_size)


@router.post("/llm_call_logs/stream_retry_llm_call")
async def stream_retry_llm_call(
    _: LLMCallRetryRequest,
    __: User = Depends(require_permission("llm:call:retry")),
):
    return StreamingResponse(iter(["data: [DONE]\n\n"]), media_type="text/event-stream")
