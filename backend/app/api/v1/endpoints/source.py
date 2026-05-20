#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:12
# @File     : source.py
# @Desc     : Source material endpoints.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.auth import CurrentUser
from app.schemas.generation import MarkSourceStatusRequest
from app.services import generation_service
from app.utils.response import page_response, success

router = APIRouter()


@router.get("/get_source_list")
def get_source_list(
    task_id: str | None = None,
    summary_id: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("source:view")),
) -> dict:
    items, total = generation_service.list_sources(db, task_id, summary_id, status, page, page_size)
    return page_response(items, total, page, page_size)


@router.get("/get_summary_detail/{summary_id}")
def get_summary_detail(
    summary_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("source:view")),
) -> dict:
    return success(generation_service.get_summary_detail(db, summary_id))


@router.post("/mark_source_status")
def mark_source_status(
    payload: MarkSourceStatusRequest,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("source:view")),
) -> dict:
    return success(generation_service.mark_source_status(db, payload.source_id, payload.status, payload.reason))
