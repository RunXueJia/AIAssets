#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:18
# @File     : dashboard.py
# @Desc     : Dashboard endpoints.

from datetime import date as date_type

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.auth import CurrentUser
from app.services import asset_service
from app.utils.response import success

router = APIRouter()


@router.get("/get_overview")
def get_overview(
    date: str | None = None,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("dashboard:view")),
) -> dict:
    target_date = date_type.fromisoformat(date) if date else None
    return success(asset_service.dashboard_overview(db, target_date))


@router.get("/get_trend")
def get_trend(
    range: str = "7d",
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("dashboard:view")),
) -> dict:
    return success(asset_service.dashboard_trend(db, range))
