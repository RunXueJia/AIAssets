#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:18
# @File     : publish.py
# @Desc     : Publish record endpoints.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.assets import CreatePublishRecordRequest, UpdatePublishRecordRequest
from app.schemas.auth import CurrentUser
from app.services import asset_service
from app.utils.response import page_response, success

router = APIRouter()


@router.post("/create_record")
def create_record(
    payload: CreatePublishRecordRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("publish:manage")),
) -> dict:
    record = asset_service.create_publish_record(db, payload, current_user.id)
    return success({"record_id": record.id, "status": record.status})


@router.post("/update_record")
def update_record(
    payload: UpdatePublishRecordRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("publish:manage")),
) -> dict:
    data = payload.model_dump(exclude={"record_id"})
    return success(asset_service.update_publish_record(db, payload.record_id, data, current_user.id))


@router.get("/get_record_list")
def get_record_list(
    package_id: str | None = None,
    platform: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("publish:manage")),
) -> dict:
    items, total = asset_service.list_publish_records(db, package_id, platform, status, page, page_size)
    return page_response(items, total, page, page_size)
