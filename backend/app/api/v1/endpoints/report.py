#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:18
# @File     : report.py
# @Desc     : Daily report endpoints.

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.auth import CurrentUser
from app.services import asset_service
from app.utils.response import page_response, success

router = APIRouter()


@router.get("/get_daily_report_list")
def get_daily_report_list(
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("report:view")),
) -> dict:
    asset_service.get_or_create_report(db)
    items, total = asset_service.list_reports(db, start_date, end_date, page, page_size)
    return page_response(items, total, page, page_size)


@router.get("/get_daily_report_detail/{report_id}")
def get_daily_report_detail(
    report_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("report:view")),
) -> dict:
    return success(asset_service.report_detail(db, report_id))


@router.get("/export_daily_report/{report_id}")
def export_daily_report(
    report_id: str,
    format: str = "markdown",
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("report:view")),
) -> PlainTextResponse:
    detail = asset_service.report_detail(db, report_id)
    suffix = "md" if format == "markdown" else "txt"
    return PlainTextResponse(
        detail["markdown"],
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={report_id}.{suffix}"},
    )
