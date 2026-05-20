#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:18
# @File     : monitor.py
# @Desc     : Monitor endpoints.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.auth import CurrentUser
from app.schemas.monitor import ChangeMonitorStatusRequest, CreateMonitorRequest, UpdateMonitorRequest
from app.services import monitor_service
from app.utils.response import page_response, success

router = APIRouter()


@router.post("/create_monitor")
def create_monitor(
    payload: CreateMonitorRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("monitor:manage")),
) -> dict:
    monitor = monitor_service.create_monitor(db, payload, current_user.id)
    return success({"monitor_id": monitor.id, "status": monitor.status})


@router.get("/get_monitor_list")
def get_monitor_list(
    status: str | None = None,
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("monitor:manage")),
) -> dict:
    items, total = monitor_service.list_monitors(db, status, keyword, page, page_size)
    return page_response(items, total, page, page_size)


@router.get("/get_monitor_detail/{monitor_id}")
def get_monitor_detail(
    monitor_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("monitor:manage")),
) -> dict:
    return success(monitor_service.get_monitor(db, monitor_id))


@router.post("/update_monitor")
def update_monitor(
    payload: UpdateMonitorRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("monitor:manage")),
) -> dict:
    return success(monitor_service.update_monitor(db, payload, current_user.id))


@router.post("/change_monitor_status")
def change_monitor_status(
    payload: ChangeMonitorStatusRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("monitor:manage")),
) -> dict:
    return success(monitor_service.change_status(db, payload.monitor_id, payload.status, current_user.id))


@router.get("/get_daily_summary_list")
def get_daily_summary_list(
    monitor_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("monitor:manage")),
) -> dict:
    items, total = monitor_service.list_daily_summaries(db, monitor_id, start_date, end_date, page, page_size)
    return page_response(items, total, page, page_size)
