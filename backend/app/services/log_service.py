#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:50
# @File     : log_service.py
# @Desc     : Task log helpers.

from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import TaskLog
from app.utils.id import new_id


def create_task_log(
    db: Session,
    task_type: str,
    task_id: str,
    event_type: str,
    message: str,
    stage: str | None = None,
    level: str = "info",
    generation_task_id: str | None = None,
    monitor_task_id: str | None = None,
    related_content_type: str | None = None,
    related_content_id: str | None = None,
    detail: dict[str, Any] | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> TaskLog:
    log = TaskLog(
        id=new_id("log"),
        task_type=task_type,
        task_id=task_id,
        generation_task_id=generation_task_id,
        monitor_task_id=monitor_task_id,
        related_content_type=related_content_type,
        related_content_id=related_content_id,
        event_type=event_type,
        stage=stage,
        level=level,
        message=message,
        detail_json=detail,
        error_code=error_code,
        error_message=error_message,
    )
    db.add(log)
    return log
