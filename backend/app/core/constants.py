#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:35
# @File     : constants.py
# @Desc     : Stable enum values used by the backend.

TASK_PENDING = "pending"
TASK_RUNNING = "running"
TASK_SUCCESS = "success"
TASK_FAILED = "failed"
TASK_CANCELLED = "cancelled"
TASK_RETRYING = "retrying"

CONTENT_GENERATING = "generating"
CONTENT_PENDING_REVIEW = "pending_review"
CONTENT_APPROVED = "approved"
CONTENT_APPROVED_WITH_EDIT = "approved_with_edit"
CONTENT_REJECTED = "rejected"
CONTENT_REGENERATING = "regenerating"
CONTENT_PENDING_RENDER = "pending_render"
CONTENT_RENDERING = "rendering"
CONTENT_RENDER_FAILED = "render_failed"
CONTENT_RENDERED = "rendered"
CONTENT_EXPORTED = "exported"
CONTENT_PUBLISHED = "published"
CONTENT_OFFLINE = "offline"

SOURCE_USABLE = "usable"
SOURCE_NOT_SUITABLE = "not_suitable"
SOURCE_UNCERTAIN = "uncertain"

MONITOR_ENABLED = "enabled"
MONITOR_PAUSED = "paused"
MONITOR_DELETED = "deleted"

GENERATION_TOPICS_ONLY = "topics_only"
GENERATION_TOPICS_AND_SCRIPT = "topics_and_script"
GENERATION_FULL = "full_script_storyboard"

STAGE_CREATE_TASK = "create_task"
STAGE_FETCH_SOURCES = "fetch_sources"
STAGE_SUMMARIZE_SOURCES = "summarize_sources"
STAGE_GENERATE_TOPICS = "generate_topics"
STAGE_GENERATE_SCRIPT = "generate_script"
STAGE_GENERATE_STORYBOARD = "generate_storyboard"
STAGE_GENERATE_SUBTITLE = "generate_subtitle"
STAGE_COMPLETED = "completed"

STAGE_NAMES = {
    STAGE_CREATE_TASK: "正在创建任务",
    STAGE_FETCH_SOURCES: "正在抓取相关内容",
    STAGE_SUMMARIZE_SOURCES: "正在整理素材汇总",
    STAGE_GENERATE_TOPICS: "正在生成选题",
    STAGE_GENERATE_SCRIPT: "正在生成脚本",
    STAGE_GENERATE_STORYBOARD: "正在生成分镜",
    STAGE_GENERATE_SUBTITLE: "正在生成字幕",
    STAGE_COMPLETED: "生成完成",
}

DEFAULT_COLUMNS = [
    {"value": "one_minute_ai_office", "label": "一分钟 AI 办公", "enabled": True},
    {"value": "less_overtime", "label": "今天少加班一小时", "enabled": True},
    {"value": "boss_ai", "label": "老板也能听懂的 AI", "enabled": True},
    {"value": "ordinary_ai_toolbox", "label": "普通人 AI 工具箱", "enabled": False},
    {"value": "ai_pitfall_guide", "label": "AI 避坑指南", "enabled": False},
]

ROLE_PERMISSIONS = {
    "admin": ["*"],
    "operation_manager": [
        "dashboard:view",
        "generation:create",
        "generation:view",
        "monitor:manage",
        "package:view",
        "report:view",
    ],
    "content_editor": ["generation:view", "source:view", "topic:manage", "script:manage", "review:manage"],
    "video_operator": ["render:manage", "package:manage", "publish:manage", "file:download"],
    "viewer": ["dashboard:view", "generation:view", "source:view", "topic:view", "script:view", "report:view"],
}
