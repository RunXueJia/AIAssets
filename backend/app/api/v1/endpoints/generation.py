#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:12
# @File     : generation.py
# @Desc     : Generation task endpoints and SSE stream.

import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.db.session import get_db
from app.schemas.auth import CurrentUser
from app.schemas.generation import CancelTaskRequest, CreateGenerationTaskRequest, RetryTaskRequest
from app.services import generation_service
from app.utils.response import page_response, success

router = APIRouter()


@router.post("/create_task")
def create_task(
    payload: CreateGenerationTaskRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("generation:create")),
) -> dict:
    task = generation_service.create_generation_task(db, payload, current_user.id)
    return success({"task_id": task.id, "status": task.status, "stream_url": f"/api/v1/generation/stream/{task.id}"})


@router.get("/get_task_list")
def get_task_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("generation:view")),
) -> dict:
    items, total = generation_service.list_tasks(db, page, page_size, status, keyword)
    return page_response(items, total, page, page_size)


@router.get("/get_task_detail/{task_id}")
def get_task_detail(
    task_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("generation:view")),
) -> dict:
    return success(generation_service.get_task_detail(db, task_id))


@router.post("/cancel_task")
def cancel_task(
    payload: CancelTaskRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("generation:create")),
) -> dict:
    return success(generation_service.cancel_task(db, payload.task_id, current_user.id))


@router.post("/retry_task")
def retry_task(
    payload: RetryTaskRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("generation:create")),
) -> dict:
    return success(generation_service.retry_task(db, payload.task_id, payload.retry_from_stage, current_user.id))


@router.get("/stream/{task_id}")
def stream_task(
    task_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    logs = generation_service.get_sse_logs(db, task_id)

    def event_iter():
        for log in logs:
            data = log.detail_json or {"task_id": task_id, "message": log.message}
            data.setdefault("task_id", task_id)
            data.setdefault("message", log.message)
            yield f"event: {log.event_type}\n"
            yield "data: " + json.dumps(data, ensure_ascii=False) + "\n\n"
        yield "event: heartbeat\n"
        yield "data: " + json.dumps({"task_id": task_id, "message": "connected"}, ensure_ascii=False) + "\n\n"

    return StreamingResponse(
        event_iter(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
