#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:18
# @File     : render.py
# @Desc     : Render endpoints.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.assets import CreateRenderTaskRequest, RetryRenderRequest
from app.schemas.auth import CurrentUser
from app.services import asset_service
from app.utils.response import page_response, success

router = APIRouter()


@router.post("/create_render_task")
def create_render_task(
    payload: CreateRenderTaskRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("render:manage")),
) -> dict:
    render = asset_service.create_render_task(db, payload, current_user.id)
    return success({"render_task_id": render.id, "status": render.status})


@router.get("/get_render_list")
def get_render_list(
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("render:manage")),
) -> dict:
    items, total = asset_service.list_renders(db, status, page, page_size)
    return page_response(items, total, page, page_size)


@router.post("/retry_render")
def retry_render(
    payload: RetryRenderRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("render:manage")),
) -> dict:
    return success(asset_service.retry_render(db, payload.render_task_id, current_user.id))


@router.get("/get_video_detail/{video_id}")
def get_video_detail(
    video_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("render:manage")),
) -> dict:
    return success(asset_service.get_video_detail(db, video_id))
