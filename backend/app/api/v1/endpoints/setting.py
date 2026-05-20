#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:18
# @File     : setting.py
# @Desc     : System setting endpoints.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.assets import UpdateSettingRequest
from app.schemas.auth import CurrentUser
from app.services import asset_service
from app.utils.response import success

router = APIRouter()


@router.get("/get_setting")
def get_setting(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("dashboard:view")),
) -> dict:
    return success(asset_service.get_settings_data(db))


@router.post("/update_setting")
def update_setting(
    payload: UpdateSettingRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("*")),
) -> dict:
    return success(asset_service.update_settings(db, payload, current_user.id))
