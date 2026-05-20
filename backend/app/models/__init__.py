#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:38
# @File     : __init__.py
# @Desc     : Import all ORM models for Alembic discovery.

from app.models.entities import (
    AuditLog,
    CardAsset,
    ContentVersion,
    CoverAsset,
    DailyReport,
    DownloadAsset,
    GenerationTask,
    MonitorTask,
    Permission,
    PublishPackage,
    PublishRecord,
    RenderTask,
    ReviewRecord,
    Role,
    RolePermission,
    Script,
    SourceItem,
    SourceSummary,
    Storyboard,
    Subtitle,
    SystemSetting,
    TaskLog,
    Topic,
    User,
    VideoAsset,
)

__all__ = [
    "AuditLog",
    "CardAsset",
    "ContentVersion",
    "CoverAsset",
    "DailyReport",
    "DownloadAsset",
    "GenerationTask",
    "MonitorTask",
    "Permission",
    "PublishPackage",
    "PublishRecord",
    "RenderTask",
    "ReviewRecord",
    "Role",
    "RolePermission",
    "Script",
    "SourceItem",
    "SourceSummary",
    "Storyboard",
    "Subtitle",
    "SystemSetting",
    "TaskLog",
    "Topic",
    "User",
    "VideoAsset",
]
