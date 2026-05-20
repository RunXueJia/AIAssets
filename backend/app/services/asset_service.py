#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:03
# @File     : asset_service.py
# @Desc     : Render, package, publish, report and settings services.

import hashlib
import json
import zipfile
from datetime import date, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import (
    CONTENT_APPROVED,
    CONTENT_APPROVED_WITH_EDIT,
    CONTENT_RENDERING,
    CONTENT_RENDERED,
    TASK_PENDING,
    TASK_SUCCESS,
)
from app.core.exceptions import AppError
from app.models.entities import (
    DailyReport,
    GenerationTask,
    PublishPackage,
    PublishRecord,
    RenderTask,
    Script,
    SourceItem,
    SystemSetting,
    Topic,
    VideoAsset,
)
from app.schemas.assets import CreatePackageRequest, CreatePublishRecordRequest, CreateRenderTaskRequest, UpdateSettingRequest
from app.services.ffmpeg_service import render_placeholder_video
from app.services.serializers import (
    daily_report_to_dict,
    package_to_dict,
    publish_record_to_dict,
    render_task_to_dict,
    script_to_dict,
    video_to_dict,
)
from app.utils.id import new_id


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def create_render_task(db: Session, payload: CreateRenderTaskRequest, user_id: str | None) -> RenderTask:
    script = db.get(Script, payload.script_id)
    if script is None:
        raise AppError(40400, "脚本不存在", 404)
    if script.status not in {CONTENT_APPROVED, CONTENT_APPROVED_WITH_EDIT, CONTENT_RENDERED}:
        raise AppError(40900, "内容未审核通过，不能进入合成队列", 409)
    render = RenderTask(
        id=new_id("render"),
        generation_task_id=script.generation_task_id,
        script_id=script.id,
        template_code=payload.template_id,
        status=TASK_PENDING if settings.enable_celery_tasks else TASK_SUCCESS,
        progress=0 if settings.enable_celery_tasks else 100,
        start_mode=payload.start_mode,
        started_at=None if settings.enable_celery_tasks else datetime.now(),
        finished_at=None if settings.enable_celery_tasks else datetime.now(),
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(render)
    db.flush()
    if settings.enable_celery_tasks:
        script.status = CONTENT_RENDERING
        db.commit()
        from app.tasks.render_tasks import run_render_task

        run_render_task.delay(render.id)
        db.refresh(render)
        return render

    execute_render_task(db, render.id)
    db.refresh(render)
    return render


def execute_render_task(db: Session, render_task_id: str) -> RenderTask:
    render = db.get(RenderTask, render_task_id)
    if render is None:
        raise AppError(40400, "合成任务不存在", 404)
    script = db.get(Script, render.script_id)
    if script is None:
        raise AppError(40400, "脚本不存在", 404)
    render.status = TASK_SUCCESS
    render.progress = 100
    render.started_at = render.started_at or datetime.now()
    videos_dir = settings.storage_root / "videos"
    _ensure_dir(videos_dir)
    video_path = videos_dir / f"{render.id}.mp4"
    render_placeholder_video(video_path, script.title)
    checksum = hashlib.sha256(video_path.read_bytes()).hexdigest()
    video = VideoAsset(
        id=new_id("video"),
        script_id=script.id,
        render_task_id=render.id,
        file_name=video_path.name,
        file_path=str(video_path),
        file_size=video_path.stat().st_size,
        checksum=checksum,
        status="created",
    )
    db.add(video)
    db.flush()
    render.output_video_asset_id = video.id
    render.finished_at = datetime.now()
    script.status = CONTENT_RENDERED
    db.commit()
    return render


def list_renders(db: Session, status: str | None, page: int, page_size: int) -> tuple[list[dict], int]:
    query = db.query(RenderTask)
    if status:
        query = query.filter(RenderTask.status == status)
    total = query.count()
    renders = query.order_by(RenderTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for render in renders:
        items.append(render_task_to_dict(render, db.get(Script, render.script_id)))
    return items, total


def retry_render(db: Session, render_task_id: str, user_id: str | None) -> dict:
    render = db.get(RenderTask, render_task_id)
    if render is None:
        raise AppError(40400, "合成任务不存在", 404)
    render.retry_count += 1
    render.updated_by = user_id
    if settings.enable_celery_tasks:
        render.status = TASK_PENDING
        render.progress = 0
        db.commit()
        from app.tasks.render_tasks import run_render_task

        run_render_task.delay(render.id)
    else:
        execute_render_task(db, render.id)
    return {"render_task_id": render.id, "status": render.status}


def get_video_detail(db: Session, video_id: str) -> dict:
    video = db.get(VideoAsset, video_id)
    if video is None:
        raise AppError(40400, "视频不存在", 404)
    return video_to_dict(video, db.get(Script, video.script_id))


def _get_video_for_package(db: Session, payload: CreatePackageRequest) -> VideoAsset | None:
    if payload.video_id:
        return db.get(VideoAsset, payload.video_id)
    render = (
        db.query(RenderTask)
        .filter(RenderTask.script_id == payload.script_id, RenderTask.output_video_asset_id.isnot(None))
        .order_by(RenderTask.created_at.desc())
        .first()
    )
    if render and render.output_video_asset_id:
        return db.get(VideoAsset, render.output_video_asset_id)
    return None


def create_package(db: Session, payload: CreatePackageRequest, user_id: str | None) -> PublishPackage:
    script = db.get(Script, payload.script_id)
    if script is None:
        raise AppError(40400, "脚本不存在", 404)
    video = _get_video_for_package(db, payload)
    if video is None:
        raise AppError(40900, "缺少已合成视频，不能导出发布包", 409)
    package_id = new_id("pkg")
    package_dir = settings.storage_root / "publish-packages"
    _ensure_dir(package_dir)
    package_path = package_dir / f"{package_id}.zip"
    with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("script.json", json.dumps(script_to_dict(script), ensure_ascii=False, indent=2))
        archive.writestr("README.txt", "发布包包含视频占位文件、标题、简介、标签、口播稿和分镜表。")
        if Path(video.file_path).exists():
            archive.write(video.file_path, arcname=video.file_name)
    checksum = hashlib.sha256(package_path.read_bytes()).hexdigest()
    package = PublishPackage(
        id=package_id,
        script_id=script.id,
        render_task_id=video.render_task_id,
        video_asset_id=video.id,
        package_name=script.title,
        platform_title=script.platform_title,
        description=script.description,
        tags_json=script.tags_json,
        pinned_comment=script.pinned_comment,
        platforms_json=payload.platforms,
        package_status="exported",
        file_name=package_path.name,
        file_path=str(package_path),
        file_size=package_path.stat().st_size,
        checksum=checksum,
        exported_by=user_id,
        exported_at=datetime.now(),
    )
    db.add(package)
    db.commit()
    db.refresh(package)
    return package


def list_packages(db: Session, keyword: str | None, page: int, page_size: int) -> tuple[list[dict], int]:
    query = db.query(PublishPackage)
    if keyword:
        query = query.filter(PublishPackage.package_name.like(f"%{keyword}%"))
    total = query.count()
    packages = query.order_by(PublishPackage.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [package_to_dict(item, db.get(Script, item.script_id)) for item in packages], total


def get_package_detail(db: Session, package_id: str) -> dict:
    package = db.get(PublishPackage, package_id)
    if package is None:
        raise AppError(40400, "发布包不存在", 404)
    script = db.get(Script, package.script_id)
    if script is None:
        raise AppError(40400, "脚本不存在", 404)
    return {
        "id": package.id,
        "title": script.title,
        "video_file": {"name": package.file_name, "download_url": f"/api/v1/file/download_video/{package.video_asset_id}"},
        "cover_file": None,
        "platform_title": script.platform_title,
        "description": script.description,
        "tags": script.tags_json or [],
        "pinned_comment": script.pinned_comment,
        "script_text": "\n".join(filter(None, [script.hook, script.pain_point, script.method, script.summary_text, script.cta_text])),
        "storyboards": [],
        "knowledge_cards": [],
        "download_draft": "MVP 资料包草稿占位内容",
        "download_url": f"/api/v1/package/download_package/{package.id}",
        "created_at": package.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def create_publish_record(db: Session, payload: CreatePublishRecordRequest, user_id: str | None) -> PublishRecord:
    package = db.get(PublishPackage, payload.package_id)
    if package is None:
        raise AppError(40400, "发布包不存在", 404)
    record = PublishRecord(
        id=new_id("pub"),
        package_id=package.id,
        script_id=package.script_id,
        platform=payload.platform,
        platform_url=payload.platform_url,
        published_at=datetime.fromisoformat(payload.published_at) if payload.published_at else datetime.now(),
        status=payload.status,
        remark=payload.remark,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_publish_record(db: Session, record_id: str, data: dict, user_id: str | None) -> dict:
    record = db.get(PublishRecord, record_id)
    if record is None:
        raise AppError(40400, "发布记录不存在", 404)
    for field in ("platform_url", "status", "remark"):
        if field in data:
            setattr(record, field, data[field])
    if data.get("published_at"):
        record.published_at = datetime.fromisoformat(data["published_at"])
    record.updated_by = user_id
    db.commit()
    return {"record_id": record.id, "status": record.status}


def list_publish_records(
    db: Session,
    package_id: str | None,
    platform: str | None,
    status: str | None,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    query = db.query(PublishRecord)
    if package_id:
        query = query.filter(PublishRecord.package_id == package_id)
    if platform:
        query = query.filter(PublishRecord.platform == platform)
    if status:
        query = query.filter(PublishRecord.status == status)
    total = query.count()
    records = query.order_by(PublishRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [publish_record_to_dict(item, db.get(PublishPackage, item.package_id)) for item in records], total


def dashboard_overview(db: Session, target_date: date | None = None) -> dict:
    target_date = target_date or date.today()
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())
    return {
        "generation_task_count": db.query(GenerationTask).filter(GenerationTask.created_at.between(start, end)).count(),
        "fetch_task_count": db.query(GenerationTask).filter(GenerationTask.source_summary_id.isnot(None)).count(),
        "source_item_count": db.query(SourceItem).filter(SourceItem.created_at.between(start, end)).count(),
        "topic_count": db.query(Topic).filter(Topic.created_at.between(start, end)).count(),
        "script_count": db.query(Script).filter(Script.created_at.between(start, end)).count(),
        "video_count": db.query(VideoAsset).filter(VideoAsset.created_at.between(start, end)).count(),
        "pending_review_count": db.query(Script).filter(Script.status == "pending_review").count(),
        "render_failed_count": db.query(RenderTask).filter(RenderTask.status == "failed").count(),
        "package_count": db.query(PublishPackage).filter(PublishPackage.created_at.between(start, end)).count(),
    }


def dashboard_trend(db: Session, range_value: str) -> dict:
    days = 1 if range_value == "today" else 30 if range_value == "30d" else 7
    dates = [date.today().fromordinal(date.today().toordinal() - offset) for offset in range(days - 1, -1, -1)]
    generation_counts = []
    source_counts = []
    script_counts = []
    video_counts = []
    for day in dates:
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        generation_counts.append(db.query(GenerationTask).filter(GenerationTask.created_at.between(start, end)).count())
        source_counts.append(db.query(SourceItem).filter(SourceItem.created_at.between(start, end)).count())
        script_counts.append(db.query(Script).filter(Script.created_at.between(start, end)).count())
        video_counts.append(db.query(VideoAsset).filter(VideoAsset.created_at.between(start, end)).count())
    total_tasks = db.query(GenerationTask).count() or 1
    success_tasks = db.query(GenerationTask).filter(GenerationTask.status == TASK_SUCCESS).count()
    failed_tasks = db.query(GenerationTask).filter(GenerationTask.status == "failed").count()
    return {
        "dates": [item.isoformat() for item in dates],
        "generation_task_counts": generation_counts,
        "source_item_counts": source_counts,
        "script_counts": script_counts,
        "video_counts": video_counts,
        "task_success_rate": round(success_tasks / total_tasks, 4),
        "task_failed_rate": round(failed_tasks / total_tasks, 4),
        "fetch_success_rate": 1.0,
        "llm_success_rate": 1.0,
        "sse_disconnect_rate": 0.0,
        "avg_generation_seconds": 0,
        "avg_render_seconds": 0,
        "package_export_count": db.query(PublishPackage).count(),
    }


def list_reports(db: Session, start_date: str | None, end_date: str | None, page: int, page_size: int) -> tuple[list[dict], int]:
    query = db.query(DailyReport)
    if start_date:
        query = query.filter(DailyReport.report_date >= start_date)
    if end_date:
        query = query.filter(DailyReport.report_date <= end_date)
    total = query.count()
    reports = query.order_by(DailyReport.report_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [daily_report_to_dict(item) for item in reports], total


def get_or_create_report(db: Session, report_id: str | None = None) -> DailyReport:
    if report_id:
        report = db.get(DailyReport, report_id)
        if report:
            return report
    today = date.today()
    report = db.query(DailyReport).filter(DailyReport.report_date == today).one_or_none()
    if report is None:
        overview = dashboard_overview(db, today)
        report = DailyReport(
            id=new_id("report"),
            report_date=today,
            title=f"{today.isoformat()} 每日产出报告",
            generation_task_count=overview["generation_task_count"],
            source_item_count=overview["source_item_count"],
            topic_count=overview["topic_count"],
            script_count=overview["script_count"],
            render_count=overview["video_count"],
            package_count=overview["package_count"],
            failed_task_count=db.query(GenerationTask).filter(GenerationTask.status == "failed").count(),
            success_rate=1.0,
            overview_json=overview,
            content_json={"tomorrow_suggestions": ["优先审核待处理脚本", "复盘合成失败原因"]},
        )
        db.add(report)
        db.commit()
        db.refresh(report)
    return report


def report_detail(db: Session, report_id: str) -> dict:
    report = get_or_create_report(db, report_id)
    data = daily_report_to_dict(report)
    data.update(
        {
            "overview": report.overview_json or {},
            "source_summaries": [],
            "generated_contents": [],
            "pending_reviews": [],
            "render_success_items": [],
            "failed_tasks": [],
            "exported_packages": [],
            "tomorrow_suggestions": (report.content_json or {}).get("tomorrow_suggestions", []),
            "markdown": f"# {report.title}\n\n今日生成任务：{report.generation_task_count}\n",
        }
    )
    return data


def get_settings_data(db: Session) -> dict:
    settings_rows = {item.setting_key: item for item in db.query(SystemSetting).all()}
    def value(key: str, default=None):
        item = settings_rows.get(key)
        if item is None:
            return default
        if item.is_secret and item.setting_value_json:
            text = str(item.setting_value_json)
            return text[:3] + "****" + text[-4:] if len(text) > 8 else "****"
        return item.setting_value_json

    return {
        "default_count": value("default_count", 5),
        "default_fetch_limit": value("default_fetch_limit", 20),
        "enabled_columns": value("enabled_columns", []),
        "storage_type": value("storage_type", "local"),
        "model_provider": value("model_provider", "openai_compatible"),
        "model_base_url": value("model_base_url", ""),
        "model_name": value("model_name", ""),
        "model_timeout_seconds": value("model_timeout_seconds", 60),
        "model_key_masked": value("model_api_key", ""),
    }


def update_settings(db: Session, payload: UpdateSettingRequest, user_id: str | None) -> bool:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if value is None:
            continue
        setting = db.query(SystemSetting).filter(SystemSetting.setting_key == key).one_or_none()
        if setting is None:
            setting = SystemSetting(
                id=new_id("set"),
                setting_key=key,
                setting_name=key,
                setting_group="custom",
                setting_value_json=value,
                is_secret=key.endswith("_key"),
                updated_by=user_id,
            )
            db.add(setting)
        else:
            setting.setting_value_json = value
            setting.updated_by = user_id
    db.commit()
    return True


def get_download_path(db: Session, asset_type: str, asset_id: str) -> Path:
    if asset_type == "video":
        item = db.get(VideoAsset, asset_id)
        if item is None:
            raise AppError(40400, "视频不存在", 404)
        return Path(item.file_path)
    if asset_type == "package":
        item = db.get(PublishPackage, asset_id)
        if item is None:
            raise AppError(40400, "发布包不存在", 404)
        return Path(item.file_path or "")
    raise AppError(40400, "文件不存在", 404)
