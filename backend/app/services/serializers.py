#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:50
# @File     : serializers.py
# @Desc     : ORM to API response serializers.

from app.models.entities import (
    DailyReport,
    GenerationTask,
    MonitorTask,
    PublishPackage,
    PublishRecord,
    RenderTask,
    ReviewRecord,
    Script,
    SourceItem,
    SourceSummary,
    Storyboard,
    Subtitle,
    Topic,
    VideoAsset,
)
from app.utils.time import format_date, format_dt


def task_to_dict(item: GenerationTask) -> dict:
    return {
        "id": item.id,
        "direction": item.direction,
        "topic": item.topic,
        "audience": item.audience,
        "count": item.count,
        "column": item.column_code,
        "generation_type": item.generation_type,
        "start_mode": item.start_mode,
        "status": item.status,
        "current_stage": item.current_stage,
        "progress": item.progress,
        "source_summary_id": item.source_summary_id,
        "selected_topic_id": item.selected_topic_id,
        "final_script_id": item.final_script_id,
        "final_render_task_id": item.final_render_task_id,
        "created_by": item.created_by,
        "created_at": format_dt(item.created_at),
        "updated_at": format_dt(item.updated_at),
        "error_message": item.error_message or "",
    }


def source_item_to_dict(item: SourceItem) -> dict:
    return {
        "id": item.id,
        "task_id": item.generation_task_id,
        "summary_id": item.source_summary_id,
        "title": item.title,
        "site_name": item.site_name,
        "url": item.url,
        "published_at": format_dt(item.published_at),
        "summary": item.summary_text,
        "relevance_reason": item.relevance_reason,
        "key_points": item.key_points_json or [],
        "status": item.status,
        "need_human_confirm": item.need_human_confirm,
        "created_at": format_dt(item.created_at),
    }


def source_summary_to_dict(item: SourceSummary) -> dict:
    return {
        "id": item.id,
        "task_id": item.generation_task_id,
        "monitor_id": item.monitor_task_id,
        "date": format_date(item.summary_date),
        "title": item.title,
        "summary": item.summary_text,
        "key_points": item.key_points_json or [],
        "risk_notes": item.risk_notes_json or [],
        "source_count": item.source_count,
        "usable_source_count": item.usable_source_count,
        "need_human_confirm": item.need_human_confirm,
        "created_at": format_dt(item.created_at),
    }


def topic_to_dict(item: Topic) -> dict:
    return {
        "id": item.id,
        "task_id": item.generation_task_id,
        "source_summary_id": item.source_summary_id,
        "title": item.title,
        "audience": item.audience,
        "angle": item.angle,
        "column": item.recommended_column,
        "duration_seconds": item.duration_seconds,
        "keywords": item.keywords_json or [],
        "reason": item.reason,
        "score": item.score,
        "status": item.status,
        "need_human_confirm": item.need_human_confirm,
        "created_at": format_dt(item.created_at),
    }


def script_to_dict(item: Script) -> dict:
    return {
        "id": item.id,
        "topic_id": item.topic_id,
        "task_id": item.generation_task_id,
        "source_summary_id": item.source_summary_id,
        "title": item.title,
        "hook": item.hook,
        "pain_point": item.pain_point,
        "method": item.method,
        "steps": item.steps_json or [],
        "example": item.example_text,
        "summary": item.summary_text,
        "cta": item.cta_text,
        "platform_title": item.platform_title,
        "description": item.description,
        "tags": item.tags_json or [],
        "cover_text": item.cover_text,
        "pinned_comment": item.pinned_comment,
        "status": item.status,
        "version": item.current_version_no,
        "need_human_confirm": item.need_human_confirm,
        "risk_notes": item.risk_notes_json or [],
        "created_at": format_dt(item.created_at),
        "updated_at": format_dt(item.updated_at),
    }


def storyboard_to_dict(item: Storyboard) -> dict:
    return {
        "id": item.id,
        "script_id": item.script_id,
        "shot_no": item.shot_no,
        "duration_seconds": item.duration_seconds,
        "voiceover": item.voiceover,
        "subtitle": item.subtitle,
        "visual_type": item.visual_type,
        "material_suggestion": item.material_suggestion,
        "motion_suggestion": item.motion_suggestion,
        "scene_note": item.scene_note,
        "status": item.status,
    }


def subtitle_to_dict(item: Subtitle) -> dict:
    return {
        "id": item.id,
        "script_id": item.script_id,
        "line_no": item.line_no,
        "start_time_ms": item.start_time_ms,
        "end_time_ms": item.end_time_ms,
        "text": item.text,
        "speaker": item.speaker,
        "style_name": item.style_name,
    }


def review_record_to_dict(item: ReviewRecord, script: Script | None = None) -> dict:
    data = {
        "id": item.id,
        "content_id": item.content_id,
        "content_type": item.content_type,
        "generation_task_id": item.generation_task_id,
        "action": item.action,
        "before_status": item.before_status,
        "after_status": item.after_status,
        "reason": item.reason,
        "comment": item.comment,
        "reviewer_id": item.reviewer_id,
        "reviewer_name": item.reviewer_name,
        "created_at": format_dt(item.created_at),
    }
    if script:
        data.update(
            {
                "title": script.title,
                "status": script.status,
                "need_human_confirm": script.need_human_confirm,
                "risk_notes": script.risk_notes_json or [],
            }
        )
    return data


def monitor_to_dict(item: MonitorTask) -> dict:
    return {
        "id": item.id,
        "topic": item.topic,
        "audience": item.audience,
        "schedule_time": item.schedule_time,
        "fetch_limit": item.fetch_limit,
        "auto_generate_topics": item.auto_generate_topics,
        "status": item.status,
        "last_run_at": format_dt(item.last_run_at),
        "next_run_at": format_dt(item.next_run_at),
        "last_summary_id": item.last_summary_id,
        "created_at": format_dt(item.created_at),
        "updated_at": format_dt(item.updated_at),
    }


def render_task_to_dict(item: RenderTask, script: Script | None = None) -> dict:
    return {
        "id": item.id,
        "script_id": item.script_id,
        "title": script.title if script else None,
        "status": item.status,
        "progress": item.progress,
        "video_id": item.output_video_asset_id,
        "duration_seconds": 60,
        "error_message": item.error_message or "",
        "created_at": format_dt(item.created_at),
        "updated_at": format_dt(item.updated_at),
    }


def video_to_dict(item: VideoAsset, script: Script | None = None) -> dict:
    return {
        "id": item.id,
        "script_id": item.script_id,
        "title": script.title if script else None,
        "duration_seconds": item.duration_seconds,
        "width": item.width,
        "height": item.height,
        "format": "mp4",
        "preview_url": f"/api/v1/file/preview_video/{item.id}",
        "download_url": f"/api/v1/file/download_video/{item.id}",
        "cover_url": None,
        "created_at": format_dt(item.created_at),
    }


def package_to_dict(item: PublishPackage, script: Script | None = None) -> dict:
    return {
        "id": item.id,
        "title": script.title if script else item.package_name,
        "video_id": item.video_asset_id,
        "script_id": item.script_id,
        "platforms": item.platforms_json or [],
        "file_size": item.file_size,
        "download_url": f"/api/v1/package/download_package/{item.id}",
        "status": item.package_status,
        "created_at": format_dt(item.created_at),
    }


def publish_record_to_dict(item: PublishRecord, package: PublishPackage | None = None) -> dict:
    return {
        "id": item.id,
        "package_id": item.package_id,
        "title": package.package_name if package else None,
        "platform": item.platform,
        "platform_url": item.platform_url,
        "published_at": format_dt(item.published_at),
        "status": item.status,
        "remark": item.remark,
        "created_by": item.created_by,
        "created_at": format_dt(item.created_at),
    }


def daily_report_to_dict(item: DailyReport) -> dict:
    return {
        "id": item.id,
        "date": format_date(item.report_date),
        "title": item.title,
        "generation_task_count": item.generation_task_count,
        "source_item_count": item.source_item_count,
        "topic_count": item.topic_count,
        "script_count": item.script_count,
        "video_count": item.render_count,
        "package_count": item.package_count,
        "failed_task_count": item.failed_task_count,
        "created_at": format_dt(item.created_at),
    }
