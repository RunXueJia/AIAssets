#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:38
# @File     : entities.py
# @Desc     : Database models for the AI growth asset engine.

from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


ID_LENGTH = 32


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


def pk() -> Mapped[str]:
    return mapped_column(String(ID_LENGTH), primary_key=True)


class Role(Base, TimestampMixin):
    __tablename__ = "role"

    id: Mapped[str] = pk()
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="enabled", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Permission(Base, TimestampMixin):
    __tablename__ = "permission"
    __table_args__ = (Index("idx_permission_module_type", "module", "type"),)

    id: Mapped[str] = pk()
    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="enabled", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class RolePermission(Base, CreatedAtMixin):
    __tablename__ = "role_permission"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uk_role_permission_role_permission"),
        Index("idx_role_permission_permission_id", "permission_id"),
    )

    id: Mapped[str] = pk()
    role_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False, index=True)
    permission_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "user"
    __table_args__ = (Index("idx_user_status", "status"),)

    id: Mapped[str] = pk()
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(128))
    role_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="enabled", nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_login_ip: Mapped[str | None] = mapped_column(String(64))


class AuditLog(Base, CreatedAtMixin):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("idx_audit_log_user_id_created_at", "user_id", "created_at"),
        Index("idx_audit_log_resource", "resource_type", "resource_id"),
        Index("idx_audit_log_created_at", "created_at"),
    )

    id: Mapped[str] = pk()
    user_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    username: Mapped[str | None] = mapped_column(String(64))
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    request_method: Mapped[str | None] = mapped_column(String(16))
    request_path: Mapped[str | None] = mapped_column(String(255))
    request_params_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    response_status: Mapped[int | None] = mapped_column(Integer)
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    result: Mapped[str | None] = mapped_column(String(32))
    message: Mapped[str | None] = mapped_column(String(512))


class GenerationTask(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "generation_task"
    __table_args__ = (
        Index("idx_generation_task_status_created_at", "status", "created_at"),
        Index("idx_generation_task_created_by", "created_by"),
        Index("idx_generation_task_current_stage", "current_stage"),
        Index("idx_generation_task_source_summary_id", "source_summary_id"),
    )

    id: Mapped[str] = pk()
    direction: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(255))
    audience: Mapped[str | None] = mapped_column(String(255))
    count: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    column_code: Mapped[str] = mapped_column(String(64), default="auto", nullable=False)
    generation_type: Mapped[str] = mapped_column(String(64), default="full_script_storyboard", nullable=False)
    start_mode: Mapped[str] = mapped_column(String(32), default="now", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    current_stage: Mapped[str] = mapped_column(String(64), default="create_task", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parent_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    source_summary_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    selected_topic_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    final_script_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    final_render_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    input_payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    result_payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    updated_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))


class RenderTask(Base, TimestampMixin):
    __tablename__ = "render_task"
    __table_args__ = (
        Index("idx_render_task_script_id", "script_id"),
        Index("idx_render_task_status_created_at", "status", "created_at"),
        Index("idx_render_task_generation_task_id", "generation_task_id"),
    )

    id: Mapped[str] = pk()
    generation_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    script_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    template_code: Mapped[str] = mapped_column(String(64), default="default_vertical", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    start_mode: Mapped[str] = mapped_column(String(32), default="now", nullable=False)
    input_payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    output_video_asset_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    updated_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))


class MonitorTask(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "monitor_task"
    __table_args__ = (
        Index("idx_monitor_task_status", "status"),
        Index("idx_monitor_task_next_run_at", "next_run_at"),
        Index("idx_monitor_task_created_by", "created_by"),
    )

    id: Mapped[str] = pk()
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    audience: Mapped[str | None] = mapped_column(String(255))
    schedule_time: Mapped[str] = mapped_column(String(16), default="09:00", nullable=False)
    fetch_limit: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    auto_generate_topics: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="enabled", nullable=False)
    cron_expression: Mapped[str | None] = mapped_column(String(64))
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_summary_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    created_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    updated_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))


class SourceSummary(Base, TimestampMixin):
    __tablename__ = "source_summary"
    __table_args__ = (
        Index("idx_source_summary_generation_task_id", "generation_task_id"),
        Index("idx_source_summary_monitor_task_id_summary_date", "monitor_task_id", "summary_date"),
        Index("idx_source_summary_type_created_at", "summary_type", "created_at"),
    )

    id: Mapped[str] = pk()
    summary_type: Mapped[str] = mapped_column(String(32), nullable=False)
    generation_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    monitor_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    summary_date: Mapped[date | None] = mapped_column(Date)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary_text: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    key_points_json: Mapped[list[Any] | None] = mapped_column(JSON)
    risk_notes_json: Mapped[list[Any] | None] = mapped_column(JSON)
    source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usable_source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    need_human_confirm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    llm_model_name: Mapped[str | None] = mapped_column(String(128))
    llm_raw_output: Mapped[str | None] = mapped_column(LONGTEXT)
    created_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))


class SourceItem(Base, TimestampMixin):
    __tablename__ = "source_item"
    __table_args__ = (
        Index("idx_source_item_source_summary_id", "source_summary_id"),
        Index("idx_source_item_generation_task_id", "generation_task_id"),
        Index("idx_source_item_monitor_task_id", "monitor_task_id"),
        Index("idx_source_item_status", "status"),
        Index("idx_source_item_source_hash", "source_hash"),
        Index("idx_source_item_url", "url"),
    )

    id: Mapped[str] = pk()
    source_summary_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    generation_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    monitor_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    site_name: Mapped[str | None] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    author: Mapped[str | None] = mapped_column(String(128))
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    summary_text: Mapped[str | None] = mapped_column(Text)
    relevance_reason: Mapped[str | None] = mapped_column(Text)
    key_points_json: Mapped[list[Any] | None] = mapped_column(JSON)
    raw_content_text: Mapped[str | None] = mapped_column(LONGTEXT)
    status: Mapped[str] = mapped_column(String(32), default="usable", nullable=False)
    need_human_confirm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fetch_status: Mapped[str] = mapped_column(String(32), default="success", nullable=False)
    fetch_error_message: Mapped[str | None] = mapped_column(Text)
    source_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Topic(Base, TimestampMixin):
    __tablename__ = "topic"
    __table_args__ = (
        Index("idx_topic_generation_task_id", "generation_task_id"),
        Index("idx_topic_source_summary_id", "source_summary_id"),
        Index("idx_topic_status", "status"),
        Index("idx_topic_lock_user_id", "lock_user_id"),
    )

    id: Mapped[str] = pk()
    generation_task_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    source_summary_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    audience: Mapped[str | None] = mapped_column(String(255))
    angle: Mapped[str | None] = mapped_column(Text)
    recommended_column: Mapped[str | None] = mapped_column(String(64))
    duration_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    keywords_json: Mapped[list[Any] | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    need_human_confirm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lock_user_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    lock_at: Mapped[datetime | None] = mapped_column(DateTime)
    reject_reason: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)


class Script(Base, TimestampMixin):
    __tablename__ = "script"
    __table_args__ = (
        Index("idx_script_topic_id", "topic_id"),
        Index("idx_script_generation_task_id", "generation_task_id"),
        Index("idx_script_status", "status"),
    )

    id: Mapped[str] = pk()
    topic_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    generation_task_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    source_summary_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    hook: Mapped[str | None] = mapped_column(Text)
    pain_point: Mapped[str | None] = mapped_column(Text)
    method: Mapped[str | None] = mapped_column(Text)
    steps_json: Mapped[list[Any] | None] = mapped_column(JSON)
    example_text: Mapped[str | None] = mapped_column(Text)
    summary_text: Mapped[str | None] = mapped_column(Text)
    cta_text: Mapped[str | None] = mapped_column(Text)
    platform_title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    tags_json: Mapped[list[Any] | None] = mapped_column(JSON)
    cover_text: Mapped[str | None] = mapped_column(String(255))
    pinned_comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending_review", nullable=False)
    current_version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    need_human_confirm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_notes_json: Mapped[list[Any] | None] = mapped_column(JSON)


class Storyboard(Base, TimestampMixin):
    __tablename__ = "storyboard"
    __table_args__ = (
        UniqueConstraint("script_id", "shot_no", name="uk_storyboard_script_shot_no"),
        Index("idx_storyboard_script_id", "script_id"),
    )

    id: Mapped[str] = pk()
    script_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    shot_no: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    voiceover: Mapped[str] = mapped_column(Text, nullable=False)
    subtitle: Mapped[str] = mapped_column(Text, nullable=False)
    visual_type: Mapped[str] = mapped_column(String(64), nullable=False)
    material_suggestion: Mapped[str | None] = mapped_column(Text)
    motion_suggestion: Mapped[str | None] = mapped_column(Text)
    scene_note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)


class Subtitle(Base, TimestampMixin):
    __tablename__ = "subtitle"
    __table_args__ = (
        UniqueConstraint("script_id", "line_no", name="uk_subtitle_script_line_no"),
        Index("idx_subtitle_script_id", "script_id"),
    )

    id: Mapped[str] = pk()
    script_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    speaker: Mapped[str | None] = mapped_column(String(64))
    style_name: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)


class ContentVersion(Base, CreatedAtMixin):
    __tablename__ = "content_version"
    __table_args__ = (
        UniqueConstraint("content_type", "content_id", "version_no", name="uk_content_version_type_id_no"),
        Index("idx_content_version_content_id", "content_id"),
    )

    id: Mapped[str] = pk()
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    change_note: Mapped[str | None] = mapped_column(String(255))
    operator_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))


class ReviewRecord(Base, CreatedAtMixin):
    __tablename__ = "review_record"
    __table_args__ = (
        Index("idx_review_record_content", "content_type", "content_id"),
        Index("idx_review_record_generation_task_id", "generation_task_id"),
        Index("idx_review_record_reviewer_id", "reviewer_id"),
    )

    id: Mapped[str] = pk()
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    generation_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    before_status: Mapped[str | None] = mapped_column(String(32))
    after_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)
    edited_payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    reviewer_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    reviewer_name: Mapped[str | None] = mapped_column(String(64))


class VideoAsset(Base, TimestampMixin):
    __tablename__ = "video_asset"
    __table_args__ = (Index("idx_video_asset_script_id", "script_id"), Index("idx_video_asset_render_task_id", "render_task_id"))

    id: Mapped[str] = pk()
    script_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    render_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), default="video/mp4", nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=1080, nullable=False)
    height: Mapped[int] = mapped_column(Integer, default=1920, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="created", nullable=False)


class CoverAsset(Base, TimestampMixin):
    __tablename__ = "cover_asset"
    __table_args__ = (Index("idx_cover_asset_script_id", "script_id"), Index("idx_cover_asset_package_id", "package_id"))

    id: Mapped[str] = pk()
    script_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    package_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), default="image/jpeg", nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    checksum: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="created", nullable=False)


class CardAsset(Base, TimestampMixin):
    __tablename__ = "card_asset"
    __table_args__ = (Index("idx_card_asset_script_id", "script_id"), Index("idx_card_asset_package_id", "package_id"))

    id: Mapped[str] = pk()
    script_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    package_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), default="image/png", nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="created", nullable=False)


class DownloadAsset(Base, TimestampMixin):
    __tablename__ = "download_asset"
    __table_args__ = (Index("idx_download_asset_script_id", "script_id"), Index("idx_download_asset_package_id", "package_id"))

    id: Mapped[str] = pk()
    script_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    package_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    draft_name: Mapped[str] = mapped_column(String(255), nullable=False)
    draft_text: Mapped[str | None] = mapped_column(LONGTEXT)
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(1024))
    storage_provider: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    checksum: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)


class PublishPackage(Base, TimestampMixin):
    __tablename__ = "publish_package"
    __table_args__ = (
        Index("idx_publish_package_script_id", "script_id"),
        Index("idx_publish_package_render_task_id", "render_task_id"),
        Index("idx_publish_package_status", "package_status"),
    )

    id: Mapped[str] = pk()
    script_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    render_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    video_asset_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    cover_asset_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    card_asset_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    download_asset_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    tags_json: Mapped[list[Any] | None] = mapped_column(JSON)
    pinned_comment: Mapped[str | None] = mapped_column(Text)
    platforms_json: Mapped[list[Any] | None] = mapped_column(JSON)
    package_status: Mapped[str] = mapped_column(String(32), default="exported", nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(1024))
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128))
    exported_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    exported_at: Mapped[datetime | None] = mapped_column(DateTime)


class PublishRecord(Base, TimestampMixin):
    __tablename__ = "publish_record"
    __table_args__ = (
        Index("idx_publish_record_package_id", "package_id"),
        Index("idx_publish_record_platform", "platform"),
        Index("idx_publish_record_status", "status"),
    )

    id: Mapped[str] = pk()
    package_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    script_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    platform_url: Mapped[str | None] = mapped_column(String(1024))
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    remark: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    updated_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))


class TaskLog(Base, CreatedAtMixin):
    __tablename__ = "task_log"
    __table_args__ = (
        Index("idx_task_log_task_type_task_id", "task_type", "task_id"),
        Index("idx_task_log_related_content", "related_content_type", "related_content_id"),
        Index("idx_task_log_level_created_at", "level", "created_at"),
        Index("idx_task_log_created_at", "created_at"),
    )

    id: Mapped[str] = pk()
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    task_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    generation_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    monitor_task_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    related_content_type: Mapped[str | None] = mapped_column(String(32))
    related_content_id: Mapped[str | None] = mapped_column(String(ID_LENGTH))
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(64))
    level: Mapped[str] = mapped_column(String(16), default="info", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    detail_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)


class DailyReport(Base, TimestampMixin):
    __tablename__ = "daily_report"

    id: Mapped[str] = pk()
    report_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    generation_task_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_item_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    topic_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    script_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    storyboard_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subtitle_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    render_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    package_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_task_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    overview_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    content_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    markdown_path: Mapped[str | None] = mapped_column(String(1024))
    pdf_path: Mapped[str | None] = mapped_column(String(1024))


class SystemSetting(Base, TimestampMixin):
    __tablename__ = "system_setting"
    __table_args__ = (Index("idx_system_setting_group", "setting_group"),)

    id: Mapped[str] = pk()
    setting_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    setting_name: Mapped[str] = mapped_column(String(128), nullable=False)
    setting_group: Mapped[str] = mapped_column(String(64), nullable=False)
    setting_value_json: Mapped[dict[str, Any] | list[Any] | str | int | bool | None] = mapped_column(JSON)
    value_type: Mapped[str] = mapped_column(String(32), default="json", nullable=False)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scope: Mapped[str] = mapped_column(String(32), default="global", nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    updated_by: Mapped[str | None] = mapped_column(String(ID_LENGTH))
