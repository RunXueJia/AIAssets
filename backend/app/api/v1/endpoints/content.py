from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.core.exceptions import AppError, NotFoundError
from app.core.response import ok, page_response
from app.db.session import get_db
from app.models.auth import User
from app.models.content import ReviewRecord, Script, ScriptVersion, Storyboard, Topic
from app.repositories.base import BaseRepository
from app.schemas.content import (
    GenerateScriptRequest,
    GenerateStoryboardRequest,
    GenerateTopicsRequest,
    RegenerateScriptRequest,
    ReviewRequest,
    ScriptUpdate,
    StoryboardUpdate,
    TopicActionRequest,
    TopicCreate,
    TopicUpdate,
)
from app.services.content_generation import (
    require_model_template,
    script_variables,
    storyboard_variables,
    topic_variables,
)
from app.services.llm_gateway import LLMGatewayService

router = APIRouter()


async def list_records(db, model, page, page_size, keyword, fields, filters=None):
    items, total = await BaseRepository(model).list(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        keyword_fields=fields,
        filters=filters,
    )
    return page_response([item.to_dict() for item in items], total, page, page_size)


async def get_or_404(db, model, id: str, label: str):
    item = await BaseRepository(model).get(db, id)
    if not item:
        raise NotFoundError(f"{label}不存在")
    return item


def script_snapshot(script: Script) -> dict:
    data = script.to_dict()
    data.pop("created_at", None)
    data.pop("updated_at", None)
    return data


@router.get("/topics/get_topic_list")
async def get_topic_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    column_id: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:topic:read")),
):
    return await list_records(
        db, Topic, page, page_size, keyword, ["title", "subtitle"], {"column_id": column_id, "status": status}
    )


@router.get("/topics/get_topic_detail/{id}")
async def get_topic_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:topic:read")),
):
    return ok((await get_or_404(db, Topic, id, "选题")).to_dict())


@router.post("/topics/create_topic")
async def create_topic(
    payload: TopicCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:topic:create")),
):
    item = await BaseRepository(Topic).create(db, payload.model_dump())
    return ok(item.to_dict())


@router.post("/topics/update_topic")
async def update_topic(
    payload: TopicUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:topic:update")),
):
    repo = BaseRepository(Topic)
    item = await get_or_404(db, Topic, payload.id, "选题")
    item = await repo.update(db, item, payload.model_dump(exclude={"id"}))
    return ok(item.to_dict())


@router.post("/topics/stream_generate_topics")
async def stream_generate_topics(
    payload: GenerateTopicsRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:topic:generate")),
):
    model, template = await require_model_template(db, payload.model_id, payload.prompt_template_id)
    variables = await topic_variables(
        db, payload.channel_id, payload.column_id, payload.count, payload.keyword_seeds
    )
    return StreamingResponse(
        LLMGatewayService().stream_prompt(
            db,
            model=model,
            template=template,
            variables=variables,
            target_type="topic",
            target_id=payload.column_id,
        ),
        media_type="text/event-stream",
    )


@router.post("/topics/lock_topic")
async def lock_topic(
    payload: TopicActionRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:topic:update")),
):
    item = await get_or_404(db, Topic, payload.id, "选题")
    item.status = "locked"
    await db.commit()
    return ok(item.to_dict())


@router.post("/topics/reject_topic")
async def reject_topic(
    payload: TopicActionRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:topic:update")),
):
    item = await get_or_404(db, Topic, payload.id, "选题")
    item.status = "rejected"
    await db.commit()
    return ok(item.to_dict())


@router.post("/topics/stream_generate_script")
async def stream_generate_script(
    payload: GenerateScriptRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:script:generate")),
):
    model, template = await require_model_template(db, payload.model_id, payload.prompt_template_id)
    variables = await script_variables(db, payload.topic_id, payload.duration_type)
    return StreamingResponse(
        LLMGatewayService().stream_prompt(
            db,
            model=model,
            template=template,
            variables=variables,
            target_type="script",
            target_id=payload.topic_id,
        ),
        media_type="text/event-stream",
    )


@router.get("/scripts/get_script_list")
async def get_script_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    topic_id: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:script:read")),
):
    return await list_records(
        db, Script, page, page_size, keyword, ["hook", "platform_title"], {"topic_id": topic_id, "status": status}
    )


@router.get("/scripts/get_script_detail/{id}")
async def get_script_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:script:read")),
):
    return ok((await get_or_404(db, Script, id, "脚本")).to_dict())


@router.post("/scripts/update_script")
async def update_script(
    payload: ScriptUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:script:update")),
):
    script = await get_or_404(db, Script, payload.id, "脚本")
    db.add(
        ScriptVersion(
            script_id=script.id,
            version=script.version,
            snapshot=script_snapshot(script),
            change_reason=payload.change_reason,
        )
    )
    data = payload.model_dump(exclude={"id", "change_reason"}, exclude_none=True)
    for key, value in data.items():
        setattr(script, key, value)
    script.version += 1
    await db.commit()
    await db.refresh(script)
    return ok(script.to_dict())


@router.post("/scripts/stream_regenerate_script")
async def stream_regenerate_script(
    payload: RegenerateScriptRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:script:generate")),
):
    model, template = await require_model_template(db, payload.model_id, payload.prompt_template_id)
    variables = await script_variables(db, payload.topic_id, payload.duration_type)
    return StreamingResponse(
        LLMGatewayService().stream_prompt(
            db,
            model=model,
            template=template,
            variables=variables,
            target_type="script",
            target_id=payload.script_id or payload.topic_id,
        ),
        media_type="text/event-stream",
    )


@router.get("/scripts/get_script_versions/{id}")
async def get_script_versions(
    id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:script:read")),
):
    return await list_records(
        db, ScriptVersion, page, page_size, None, [], {"script_id": id}
    )


@router.post("/scripts/stream_generate_storyboard")
async def stream_generate_storyboard(
    payload: GenerateStoryboardRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:storyboard:generate")),
):
    model, template = await require_model_template(db, payload.model_id, payload.prompt_template_id)
    variables = await storyboard_variables(db, payload.script_id)
    return StreamingResponse(
        LLMGatewayService().stream_prompt(
            db,
            model=model,
            template=template,
            variables=variables,
            target_type="storyboard",
            target_id=payload.script_id,
        ),
        media_type="text/event-stream",
    )


@router.get("/storyboards/get_storyboard_list")
async def get_storyboard_list(
    page: int = 1,
    page_size: int = 20,
    script_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:storyboard:read")),
):
    return await list_records(db, Storyboard, page, page_size, None, [], {"script_id": script_id})


@router.get("/storyboards/get_storyboard_detail/{script_id}")
async def get_storyboard_detail(
    script_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:storyboard:read")),
):
    items, total = await BaseRepository(Storyboard).list(
        db, page=1, page_size=100, filters={"script_id": script_id}, order_desc=False
    )
    return ok({"total": total, "items": [item.to_dict() for item in items]})


@router.post("/storyboards/update_storyboard")
async def update_storyboard(
    payload: StoryboardUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:storyboard:update")),
):
    item = await get_or_404(db, Storyboard, payload.id, "分镜")
    item = await BaseRepository(Storyboard).update(
        db, item, payload.model_dump(exclude={"id"}, exclude_none=True)
    )
    return ok(item.to_dict())


@router.post("/storyboards/stream_regenerate_storyboard")
async def stream_regenerate_storyboard(
    payload: GenerateStoryboardRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:storyboard:generate")),
):
    return await stream_generate_storyboard(payload, db, _)


async def update_review_target(db: AsyncSession, target_type: str, target_id: str, status: str) -> dict:
    model_map = {"topic": Topic, "script": Script, "storyboard": Storyboard}
    model = model_map.get(target_type)
    if not model:
        raise AppError("不支持的审核对象")
    item = await get_or_404(db, model, target_id, "审核对象")
    before = item.to_dict()
    item.status = status
    await db.flush()
    return before


@router.get("/reviews/get_review_queue")
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("review:content:read")),
):
    scripts, _ = await BaseRepository(Script).list(
        db, page=1, page_size=100, filters={"status": "pending_review"}
    )
    return ok({"items": [{"target_type": "script", **script.to_dict()} for script in scripts]})


@router.get("/reviews/get_review_records")
async def get_review_records(
    page: int = 1,
    page_size: int = 20,
    target_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("review:content:read")),
):
    return await list_records(
        db, ReviewRecord, page, page_size, None, [], {"target_type": target_type}
    )


@router.post("/reviews/approve_content")
async def approve_content(
    payload: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("review:content:approve")),
):
    before = await update_review_target(db, payload.target_type, payload.target_id, "approved")
    db.add(
        ReviewRecord(
            target_type=payload.target_type,
            target_id=payload.target_id,
            action="approve",
            reason=payload.comment or "",
            reviewer_id=user.id,
            before_snapshot=before,
        )
    )
    await db.commit()
    return ok()


@router.post("/reviews/reject_content")
async def reject_content(
    payload: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("review:content:reject")),
):
    if not payload.reason:
        raise AppError("驳回必须填写原因")
    before = await update_review_target(db, payload.target_type, payload.target_id, "rejected")
    db.add(
        ReviewRecord(
            target_type=payload.target_type,
            target_id=payload.target_id,
            action="reject",
            reason=payload.reason,
            reviewer_id=user.id,
            before_snapshot=before,
        )
    )
    await db.commit()
    return ok()


@router.post("/reviews/approve_content_with_changes")
async def approve_content_with_changes(
    payload: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("review:content:approve")),
):
    before = await update_review_target(db, payload.target_type, payload.target_id, "approved")
    db.add(
        ReviewRecord(
            target_type=payload.target_type,
            target_id=payload.target_id,
            action="approve_with_changes",
            reason=payload.comment or "",
            reviewer_id=user.id,
            before_snapshot=before,
            after_snapshot=payload.changes or {},
        )
    )
    await db.commit()
    return ok()


@router.post("/reviews/stream_request_regeneration")
async def stream_request_regeneration(
    _: ReviewRequest,
    __: User = Depends(get_current_user),
):
    return StreamingResponse(iter(["data: [DONE]\n\n"]), media_type="text/event-stream")
