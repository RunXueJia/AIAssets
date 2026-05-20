#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:45
# @File     : assets.py
# @Desc     : Render, package, publish and setting schemas.

from typing import Any

from pydantic import BaseModel, Field


class CreateRenderTaskRequest(BaseModel):
    script_id: str = Field(min_length=1, max_length=32)
    template_id: str = Field(default="default_vertical", max_length=64)
    start_mode: str = Field(default="now", max_length=32)


class RetryRenderRequest(BaseModel):
    render_task_id: str = Field(min_length=1, max_length=32)


class CreatePackageRequest(BaseModel):
    script_id: str = Field(min_length=1, max_length=32)
    video_id: str | None = Field(default=None, max_length=32)
    platforms: list[str] = Field(default_factory=list)


class CreatePublishRecordRequest(BaseModel):
    package_id: str = Field(min_length=1, max_length=32)
    platform: str = Field(min_length=1, max_length=64)
    platform_url: str | None = Field(default=None, max_length=1024)
    published_at: str | None = Field(default=None, max_length=32)
    status: str = Field(default="published", max_length=32)
    remark: str | None = None


class UpdatePublishRecordRequest(BaseModel):
    record_id: str = Field(min_length=1, max_length=32)
    platform_url: str | None = Field(default=None, max_length=1024)
    published_at: str | None = Field(default=None, max_length=32)
    status: str = Field(default="published", max_length=32)
    remark: str | None = None


class UpdateSettingRequest(BaseModel):
    default_count: int | None = Field(default=None, ge=1, le=20)
    default_fetch_limit: int | None = Field(default=None, ge=1, le=100)
    enabled_columns: list[str] | None = None
    model_provider: str | None = Field(default=None, max_length=64)
    model_base_url: str | None = Field(default=None, max_length=512)
    model_api_key: str | None = Field(default=None, max_length=512)
    model_name: str | None = Field(default=None, max_length=128)
    storage_type: str | None = Field(default=None, max_length=32)
    extra: dict[str, Any] | None = None
