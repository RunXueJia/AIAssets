from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.exceptions import NotFoundError
from app.core.response import ok, page_response
from app.db.session import get_db
from app.models.assets import (
    ArticlePage,
    DownloadAsset,
    KnowledgeCard,
    Lead,
    PublicEvent,
    PublishRecord,
    VideoAsset,
)
from app.models.auth import User
from app.models.content import Script, Topic
from app.models.task import DailyReport, ScheduleConfig, TaskLog
from app.repositories.base import BaseRepository

router = APIRouter()


async def list_endpoint(db, model, page, page_size, keyword=None, fields=None, filters=None):
    items, total = await BaseRepository(model).list(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        keyword_fields=fields or [],
        filters=filters,
    )
    return page_response([item.to_dict() for item in items], total, page, page_size)


async def get_item(db, model, id: str, label: str):
    item = await BaseRepository(model).get(db, id)
    if not item:
        raise NotFoundError(f"{label}不存在")
    return item


@router.get("/videos/get_video_list")
async def get_video_list(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("asset:video:read")),
):
    return await list_endpoint(db, VideoAsset, page, page_size, filters={"status": status})


@router.get("/videos/get_video_detail/{id}")
async def get_video_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("asset:video:read")),
):
    return ok((await get_item(db, VideoAsset, id, "视频")).to_dict())


@router.post("/videos/create_render_task")
async def create_render_task(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("asset:video:render")),
):
    item = await BaseRepository(VideoAsset).create(
        db,
        {
            "script_id": payload["script_id"],
            "template_id": payload.get("template_id"),
            "status": "waiting",
        },
    )
    db.add(TaskLog(task_type="render_video", target_id=item.id, payload=payload, status="queued"))
    await db.commit()
    return ok(item.to_dict())


@router.post("/videos/retry_render_task")
async def retry_render_task(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("asset:video:render")),
):
    item = await get_item(db, VideoAsset, payload["id"], "视频")
    item.status = "waiting"
    item.retry_count += 1
    item.error_message = None
    await db.commit()
    return ok(item.to_dict())


@router.post("/videos/regenerate_cover")
async def regenerate_cover(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("asset:video:update")),
):
    item = await get_item(db, VideoAsset, payload["id"], "视频")
    item.cover_url = payload.get("cover_url", item.cover_url)
    await db.commit()
    return ok(item.to_dict())


@router.get("/videos/get_video_download_url/{id}")
async def get_video_download_url(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("asset:video:download")),
):
    item = await get_item(db, VideoAsset, id, "视频")
    return ok({"url": item.file_url})


@router.get("/knowledge_cards/get_knowledge_card_list")
async def get_knowledge_card_list(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("asset:card:read")),
):
    return await list_endpoint(db, KnowledgeCard, page, page_size)


@router.post("/knowledge_cards/stream_generate_knowledge_cards")
async def stream_generate_knowledge_cards(_: dict):
    return ok({"message": "知识卡片生成任务已预留，MVP 阶段先通过任务日志跟踪"})


@router.get("/download_assets/get_download_asset_list")
async def get_download_asset_list(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("asset:download:read")),
):
    return await list_endpoint(db, DownloadAsset, page, page_size, fields=["title"])


@router.post("/download_assets/stream_generate_download_asset")
async def stream_generate_download_asset(_: dict):
    return ok({"message": "资料包生成任务已预留，MVP 阶段先通过任务日志跟踪"})


@router.get("/article_pages/get_article_page_list")
async def get_article_page_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:article:read")),
):
    return await list_endpoint(db, ArticlePage, page, page_size, keyword, ["title", "slug"])


@router.get("/article_pages/get_article_page_detail/{id}")
async def get_article_page_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:article:read")),
):
    return ok((await get_item(db, ArticlePage, id, "图文页")).to_dict())


@router.post("/article_pages/stream_generate_article_page")
async def stream_generate_article_page(_: dict):
    return ok({"message": "图文页生成任务已预留，MVP 阶段先通过任务日志跟踪"})


@router.post("/article_pages/update_article_page")
async def update_article_page(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:article:update")),
):
    repo = BaseRepository(ArticlePage)
    item = await repo.get(db, payload.get("id", ""))
    if item:
        item = await repo.update(db, item, {k: v for k, v in payload.items() if k != "id"})
    else:
        item = await repo.create(db, payload)
    return ok(item.to_dict())


@router.post("/article_pages/change_article_page_status")
async def change_article_page_status(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("content:article:publish")),
):
    item = await get_item(db, ArticlePage, payload["id"], "图文页")
    item.status = payload["status"]
    if item.status == "published":
        item.published_at = datetime.now(UTC)
    await db.commit()
    return ok(item.to_dict())


@router.get("/publish_queue/get_publish_queue_list")
async def get_publish_queue_list(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("publish:queue:read")),
):
    return await list_endpoint(db, PublishRecord, page, page_size, filters={"status": status})


@router.get("/publish_queue/get_publish_package_detail/{id}")
async def get_publish_package_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("publish:queue:read")),
):
    return ok((await get_item(db, PublishRecord, id, "发布包")).to_dict())


@router.post("/publish_queue/create_publish_package")
async def create_publish_package(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("publish:package:create")),
):
    item = await BaseRepository(PublishRecord).create(
        db,
        {
            "content_id": payload["content_id"],
            "platform": payload.get("platform", "manual"),
            "status": "pending_publish",
        },
    )
    return ok(item.to_dict())


@router.get("/publish_queue/get_publish_package_download_url/{id}")
async def get_publish_package_download_url(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("publish:package:download")),
):
    item = await get_item(db, PublishRecord, id, "发布包")
    return ok({"url": item.package_url})


@router.post("/publish_queue/mark_as_published")
async def mark_as_published(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("publish:queue:update")),
):
    item = await get_item(db, PublishRecord, payload["publish_item_id"], "发布记录")
    item.status = "published"
    item.platform_url = payload.get("platform_url", "")
    item.operator_id = user.id
    item.published_at = datetime.fromisoformat(payload["published_at"]) if payload.get("published_at") else None
    await db.commit()
    return ok(item.to_dict())


@router.post("/publish_queue/mark_as_offline")
async def mark_as_offline(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("publish:queue:update")),
):
    item = await get_item(db, PublishRecord, payload["publish_item_id"], "发布记录")
    item.status = "offline"
    item.operator_id = user.id
    await db.commit()
    return ok(item.to_dict())


@router.get("/leads/get_lead_list")
async def get_lead_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("lead:lead:read")),
):
    return await list_endpoint(db, Lead, page, page_size, keyword, ["name", "contact", "company"])


@router.get("/leads/get_lead_detail/{id}")
async def get_lead_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("lead:lead:read")),
):
    return ok((await get_item(db, Lead, id, "线索")).to_dict())


@router.get("/leads/export_leads")
async def export_leads(_: User = Depends(require_permission("lead:lead:export"))):
    return ok({"url": ""})


@router.post("/public/leads/submit_lead")
async def submit_lead(payload: dict, db: AsyncSession = Depends(get_db)):
    item = await BaseRepository(Lead).create(db, payload)
    return ok(item.to_dict())


@router.post("/public/downloads/request_download")
async def request_download(payload: dict, db: AsyncSession = Depends(get_db)):
    item = await BaseRepository(Lead).create(db, payload)
    return ok({"lead_id": item.id, "download_url": ""})


@router.get("/dashboard/get_today_overview")
async def get_today_overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("dashboard:overview:read")),
):
    async def count(model):
        return (await db.execute(select(func.count()).select_from(model))).scalar_one()

    return ok(
        {
            "date": date.today().isoformat(),
            "topics_count": await count(Topic),
            "scripts_count": await count(Script),
            "videos_count": await count(VideoAsset),
            "article_pages_count": await count(ArticlePage),
            "knowledge_cards_count": await count(KnowledgeCard),
            "download_assets_count": await count(DownloadAsset),
            "published_count": await count(PublishRecord),
            "visit_count": await count(PublicEvent),
            "download_count": 0,
            "lead_count": await count(Lead),
            "task_success_rate": 0.0,
            "task_failed_rate": 0.0,
        }
    )


@router.get("/dashboard/get_channel_performance")
async def get_channel_performance(_: User = Depends(require_permission("dashboard:overview:read"))):
    return ok({"items": []})


@router.get("/dashboard/get_task_metrics")
async def get_task_metrics(_: User = Depends(require_permission("dashboard:task:read"))):
    return ok({"items": []})


@router.get("/dashboard/get_asset_growth")
async def get_asset_growth(_: User = Depends(require_permission("dashboard:overview:read"))):
    return ok({"items": []})


@router.get("/reports/get_daily_report_list")
async def get_daily_report_list(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report:daily:read")),
):
    return await list_endpoint(db, DailyReport, page, page_size)


@router.get("/reports/get_daily_report_detail/{id}")
async def get_daily_report_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report:daily:read")),
):
    return ok((await get_item(db, DailyReport, id, "日报")).to_dict())


@router.post("/reports/stream_generate_daily_report")
async def stream_generate_daily_report(_: dict):
    return ok({"message": "日报生成任务已预留，MVP 阶段先通过任务日志跟踪"})


@router.get("/reports/export_daily_report/{id}")
async def export_daily_report(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("report:daily:export")),
):
    item = await get_item(db, DailyReport, id, "日报")
    return ok({"url": item.export_file_url})


@router.get("/tasks/get_task_log_list")
async def get_task_log_list(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:task:read")),
):
    return await list_endpoint(db, TaskLog, page, page_size, filters={"status": status})


@router.get("/tasks/get_task_log_detail/{id}")
async def get_task_log_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:task:read")),
):
    return ok((await get_item(db, TaskLog, id, "任务")).to_dict())


@router.post("/tasks/run_task")
async def run_task(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:task:run")),
):
    item = await BaseRepository(TaskLog).create(
        db,
        {
            "task_type": payload["task_type"],
            "target_id": payload.get("target_id"),
            "payload": payload.get("payload", {}),
            "status": "queued",
        },
    )
    return ok(item.to_dict())


@router.post("/tasks/retry_task")
async def retry_task(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:task:run")),
):
    item = await get_item(db, TaskLog, payload["id"], "任务")
    item.status = "retrying"
    item.retry_count += 1
    await db.commit()
    return ok(item.to_dict())


@router.post("/tasks/cancel_task")
async def cancel_task(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:task:update")),
):
    item = await get_item(db, TaskLog, payload["id"], "任务")
    item.status = "cancelled"
    await db.commit()
    return ok(item.to_dict())


@router.post("/tasks/pause_schedule")
async def pause_schedule(_: dict, __: User = Depends(require_permission("system:task:update"))):
    return ok()


@router.post("/tasks/resume_schedule")
async def resume_schedule(_: dict, __: User = Depends(require_permission("system:task:update"))):
    return ok()


@router.get("/tasks/get_schedule_config")
async def get_schedule_config(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:task:read")),
):
    return await list_endpoint(db, ScheduleConfig, page, page_size)


@router.post("/tasks/update_schedule_config")
async def update_schedule_config(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:task:update")),
):
    repo = BaseRepository(ScheduleConfig)
    item = await repo.get(db, payload.get("id", ""))
    item = await repo.update(db, item, payload) if item else await repo.create(db, payload)
    return ok(item.to_dict())


@router.get("/public/home/get_home_data")
async def get_home_data():
    return ok({"featured_articles": [], "featured_videos": []})


@router.get("/public/columns/get_column_list")
async def public_column_list():
    return ok({"items": []})


@router.get("/public/columns/get_column_detail/{id}")
async def public_column_detail(id: str):
    return ok({"id": id})


@router.get("/public/articles/get_article_list")
async def public_article_list():
    return ok({"items": []})


@router.get("/public/articles/get_article_detail/{slug}")
async def public_article_detail(slug: str, db: AsyncSession = Depends(get_db)):
    item = await BaseRepository(ArticlePage).get_by_field(db, "slug", slug)
    if not item or item.status != "published":
        raise NotFoundError("公开内容不存在")
    return ok(item.to_dict())


@router.get("/public/videos/get_video_detail/{id}")
async def public_video_detail(id: str, db: AsyncSession = Depends(get_db)):
    return ok((await get_item(db, VideoAsset, id, "视频")).to_dict())


@router.get("/public/topics/get_topic_page/{slug}")
async def public_topic_page(slug: str):
    return ok({"slug": slug})


@router.get("/public/download_assets/get_download_asset_list")
async def public_download_asset_list():
    return ok({"items": []})


@router.get("/public/tools/get_tool_recommendation_list")
async def public_tool_recommendation_list():
    return ok({"items": []})


@router.post("/public/analytics/track_event")
async def track_event(payload: dict, db: AsyncSession = Depends(get_db)):
    item = await BaseRepository(PublicEvent).create(db, payload)
    return ok(item.to_dict())
