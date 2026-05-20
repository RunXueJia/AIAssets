#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:45
# @File     : monitor.py
# @Desc     : Monitor task schemas.

from pydantic import BaseModel, Field


class CreateMonitorRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=255)
    audience: str | None = Field(default=None, max_length=255)
    schedule_time: str = Field(default="09:00", max_length=16)
    fetch_limit: int = Field(default=20, ge=1, le=100)
    auto_generate_topics: bool = True


class UpdateMonitorRequest(CreateMonitorRequest):
    monitor_id: str = Field(min_length=1, max_length=32)


class ChangeMonitorStatusRequest(BaseModel):
    monitor_id: str = Field(min_length=1, max_length=32)
    status: str = Field(min_length=1, max_length=32)
