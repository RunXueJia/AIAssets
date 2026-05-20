#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:12
# @File     : script.py
# @Desc     : Script, storyboard and subtitle endpoints.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.auth import CurrentUser
from app.schemas.generation import UpdateScriptRequest, UpdateStoryboardRequest, UpdateSubtitleRequest
from app.services import generation_service
from app.utils.response import success

router = APIRouter()
storyboard_router = APIRouter()
subtitle_router = APIRouter()


@router.get("/get_script_detail/{script_id}")
def get_script_detail(
    script_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("script:view")),
) -> dict:
    return success(generation_service.get_script_detail(db, script_id))


@router.post("/update_script")
def update_script(
    payload: UpdateScriptRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("script:manage")),
) -> dict:
    return success(generation_service.update_script(db, payload, current_user.id))


@storyboard_router.post("/update_storyboard")
def update_storyboard(
    payload: UpdateStoryboardRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("script:manage")),
) -> dict:
    return success(generation_service.update_storyboard(db, payload.script_id, payload.items, current_user.id))


@subtitle_router.post("/update_subtitle")
def update_subtitle(
    payload: UpdateSubtitleRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("script:manage")),
) -> dict:
    return success(generation_service.update_subtitle(db, payload.script_id, payload.items, current_user.id))
