#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:12
# @File     : topic.py
# @Desc     : Topic endpoints.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.auth import CurrentUser
from app.schemas.generation import ChangeTopicStatusRequest, GenerateScriptRequest
from app.services import generation_service
from app.utils.response import page_response, success

router = APIRouter()


@router.get("/get_topic_list")
def get_topic_list(
    task_id: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("topic:view")),
) -> dict:
    items, total = generation_service.list_topics(db, task_id, status, keyword, page, page_size)
    return page_response(items, total, page, page_size)


@router.get("/get_topic_detail/{topic_id}")
def get_topic_detail(
    topic_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("topic:view")),
) -> dict:
    return success(generation_service.get_topic_detail(db, topic_id))


@router.post("/change_topic_status")
def change_topic_status(
    payload: ChangeTopicStatusRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("topic:manage")),
) -> dict:
    return success(generation_service.change_topic_status(db, payload.topic_id, payload.status, payload.reason, current_user.id))


@router.post("/generate_script")
def generate_script(
    payload: GenerateScriptRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("topic:manage")),
) -> dict:
    return success(generation_service.generate_script_from_topic(db, payload.topic_id, current_user.id))
