#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:45
# @File     : generation.py
# @Desc     : Generation task schemas.

from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import GENERATION_FULL


class CreateGenerationTaskRequest(BaseModel):
    direction: str = Field(min_length=1, max_length=255)
    topic: str | None = Field(default=None, max_length=255)
    audience: str | None = Field(default=None, max_length=255)
    count: int = Field(default=5, ge=1, le=20)
    column: str = Field(default="auto", max_length=64)
    generation_type: str = Field(default=GENERATION_FULL, max_length=64)
    start_mode: str = Field(default="now", max_length=32)


class CancelTaskRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=32)


class RetryTaskRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=32)
    retry_from_stage: str | None = Field(default=None, max_length=64)


class MarkSourceStatusRequest(BaseModel):
    source_id: str = Field(min_length=1, max_length=32)
    status: str = Field(min_length=1, max_length=32)
    reason: str | None = Field(default=None, max_length=255)


class ChangeTopicStatusRequest(BaseModel):
    topic_id: str = Field(min_length=1, max_length=32)
    status: str = Field(min_length=1, max_length=32)
    reason: str | None = Field(default=None, max_length=255)


class GenerateScriptRequest(BaseModel):
    topic_id: str = Field(min_length=1, max_length=32)
    start_mode: str = Field(default="now", max_length=32)


class UpdateScriptRequest(BaseModel):
    script_id: str = Field(min_length=1, max_length=32)
    title: str | None = Field(default=None, max_length=255)
    hook: str | None = None
    pain_point: str | None = None
    method: str | None = None
    steps: list[str] | None = None
    example: str | None = None
    summary: str | None = None
    cta: str | None = None
    platform_title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    tags: list[str] | None = None
    cover_text: str | None = Field(default=None, max_length=255)
    pinned_comment: str | None = None


class StoryboardItemRequest(BaseModel):
    id: str | None = Field(default=None, max_length=32)
    shot_no: int = Field(ge=1, le=30)
    duration_seconds: int = Field(ge=1, le=120)
    voiceover: str = Field(min_length=1)
    subtitle: str = Field(min_length=1)
    visual_type: str = Field(min_length=1, max_length=64)
    material_suggestion: str | None = None
    motion_suggestion: str | None = None
    scene_note: str | None = None


class UpdateStoryboardRequest(BaseModel):
    script_id: str = Field(min_length=1, max_length=32)
    items: list[StoryboardItemRequest]


class SubtitleItemRequest(BaseModel):
    id: str | None = Field(default=None, max_length=32)
    line_no: int | None = Field(default=None, ge=1, le=500)
    start_time: str | None = Field(default=None, max_length=32)
    end_time: str | None = Field(default=None, max_length=32)
    start_time_ms: int | None = Field(default=None, ge=0)
    end_time_ms: int | None = Field(default=None, ge=0)
    text: str = Field(min_length=1)
    speaker: str | None = Field(default=None, max_length=64)
    style_name: str | None = Field(default=None, max_length=64)


class UpdateSubtitleRequest(BaseModel):
    script_id: str = Field(min_length=1, max_length=32)
    items: list[SubtitleItemRequest]


class ReviewApproveRequest(BaseModel):
    content_id: str = Field(min_length=1, max_length=32)
    content_type: str = Field(default="script", max_length=32)
    comment: str | None = None


class ReviewApproveWithEditRequest(BaseModel):
    content_id: str = Field(min_length=1, max_length=32)
    content_type: str = Field(default="script", max_length=32)
    edited_payload: dict[str, Any] = Field(default_factory=dict)
    comment: str | None = None


class ReviewRejectRequest(BaseModel):
    content_id: str = Field(min_length=1, max_length=32)
    content_type: str = Field(default="script", max_length=32)
    reason: str = Field(min_length=1)


class ReviewRegenerateRequest(BaseModel):
    content_id: str = Field(min_length=1, max_length=32)
    content_type: str = Field(default="script", max_length=32)
    reason: str | None = None
