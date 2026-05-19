from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.exceptions import NotFoundError
from app.core.response import ok, page_response
from app.db.session import get_db
from app.models.auth import User
from app.models.configuration import (
    ArticleTemplate,
    Column,
    ContentChannel,
    PlatformConfig,
    VideoTemplate,
)
from app.repositories.base import BaseRepository
from app.schemas.common import StatusPayload
from app.schemas.configuration import (
    ArticleTemplateCreate,
    ArticleTemplateUpdate,
    ColumnCreate,
    ColumnUpdate,
    ContentChannelCreate,
    ContentChannelUpdate,
    PlatformUpdate,
    VideoTemplateCreate,
    VideoTemplateUpdate,
)

router = APIRouter()


async def list_endpoint(
    db: AsyncSession,
    repo: BaseRepository,
    page: int,
    page_size: int,
    keyword: str | None,
    keyword_fields: list[str],
    filters: dict | None = None,
):
    items, total = await repo.list(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        keyword_fields=keyword_fields,
        filters=filters,
    )
    return page_response([item.to_dict() for item in items], total, page, page_size)


async def detail_endpoint(db: AsyncSession, repo: BaseRepository, id: str, label: str):
    item = await repo.get(db, id)
    if not item:
        raise NotFoundError(f"{label}不存在")
    return ok(item.to_dict())


async def update_endpoint(db: AsyncSession, repo: BaseRepository, payload, label: str):
    item = await repo.get(db, payload.id)
    if not item:
        raise NotFoundError(f"{label}不存在")
    item = await repo.update(db, item, payload.model_dump(exclude={"id"}, exclude_none=True))
    return ok(item.to_dict())


@router.get("/content_channels/get_content_channel_list")
async def get_content_channel_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:channel:read")),
):
    return await list_endpoint(
        db, BaseRepository(ContentChannel), page, page_size, keyword, ["name", "description"]
    )


@router.get("/content_channels/get_content_channel_detail/{id}")
async def get_content_channel_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:channel:read")),
):
    return await detail_endpoint(db, BaseRepository(ContentChannel), id, "内容方向")


@router.post("/content_channels/create_content_channel")
async def create_content_channel(
    payload: ContentChannelCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:channel:create")),
):
    item = await BaseRepository(ContentChannel).create(db, payload.model_dump())
    return ok(item.to_dict())


@router.post("/content_channels/update_content_channel")
async def update_content_channel(
    payload: ContentChannelUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:channel:update")),
):
    return await update_endpoint(db, BaseRepository(ContentChannel), payload, "内容方向")


@router.post("/content_channels/change_content_channel_status")
async def change_content_channel_status(
    payload: StatusPayload,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:channel:update")),
):
    return await update_endpoint(db, BaseRepository(ContentChannel), payload, "内容方向")


@router.get("/columns/get_column_list")
async def get_column_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    channel_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:column:read")),
):
    return await list_endpoint(
        db,
        BaseRepository(Column),
        page,
        page_size,
        keyword,
        ["name", "description"],
        {"channel_id": channel_id},
    )


@router.get("/columns/get_column_detail/{id}")
async def get_column_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:column:read")),
):
    return await detail_endpoint(db, BaseRepository(Column), id, "栏目")


@router.post("/columns/create_column")
async def create_column(
    payload: ColumnCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:column:create")),
):
    item = await BaseRepository(Column).create(db, payload.model_dump())
    return ok(item.to_dict())


@router.post("/columns/update_column")
async def update_column(
    payload: ColumnUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:column:update")),
):
    return await update_endpoint(db, BaseRepository(Column), payload, "栏目")


@router.post("/columns/change_column_status")
async def change_column_status(
    payload: StatusPayload,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:column:update")),
):
    return await update_endpoint(db, BaseRepository(Column), payload, "栏目")


@router.get("/video_templates/get_video_template_list")
async def get_video_template_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("template:video:read")),
):
    return await list_endpoint(db, BaseRepository(VideoTemplate), page, page_size, keyword, ["name"])


@router.post("/video_templates/create_video_template")
async def create_video_template(
    payload: VideoTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("template:video:create")),
):
    item = await BaseRepository(VideoTemplate).create(db, payload.model_dump())
    return ok(item.to_dict())


@router.post("/video_templates/update_video_template")
async def update_video_template(
    payload: VideoTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("template:video:update")),
):
    return await update_endpoint(db, BaseRepository(VideoTemplate), payload, "视频模板")


@router.get("/article_templates/get_article_template_list")
async def get_article_template_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("template:article:read")),
):
    return await list_endpoint(db, BaseRepository(ArticleTemplate), page, page_size, keyword, ["name"])


@router.post("/article_templates/create_article_template")
async def create_article_template(
    payload: ArticleTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("template:article:create")),
):
    item = await BaseRepository(ArticleTemplate).create(db, payload.model_dump())
    return ok(item.to_dict())


@router.post("/article_templates/update_article_template")
async def update_article_template(
    payload: ArticleTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("template:article:update")),
):
    return await update_endpoint(db, BaseRepository(ArticleTemplate), payload, "图文模板")


@router.get("/platforms/get_platform_list")
async def get_platform_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("publish:platform:read")),
):
    return await list_endpoint(
        db, BaseRepository(PlatformConfig), page, page_size, keyword, ["platform_name"]
    )


@router.post("/platforms/update_platform")
async def update_platform(
    payload: PlatformUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("publish:platform:update")),
):
    repo = BaseRepository(PlatformConfig)
    if payload.id:
        item = await repo.get(db, payload.id)
        if not item:
            raise NotFoundError("平台配置不存在")
        item = await repo.update(db, item, payload.model_dump(exclude={"id"}))
    else:
        existing = await repo.get_by_field(db, "platform_name", payload.platform_name)
        item = (
            await repo.update(db, existing, payload.model_dump(exclude={"id"}))
            if existing
            else await repo.create(db, payload.model_dump(exclude={"id"}))
        )
    return ok(item.to_dict())
