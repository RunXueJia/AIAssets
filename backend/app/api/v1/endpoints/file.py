#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:18
# @File     : file.py
# @Desc     : File preview and download endpoints.

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.auth import CurrentUser
from app.services import asset_service

router = APIRouter()


@router.get("/preview_video/{video_id}")
def preview_video(
    video_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("file:download")),
) -> FileResponse:
    path = asset_service.get_download_path(db, "video", video_id)
    return FileResponse(path, filename=path.name, media_type="video/mp4")


@router.get("/download_video/{video_id}")
def download_video(
    video_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("file:download")),
) -> FileResponse:
    path = asset_service.get_download_path(db, "video", video_id)
    return FileResponse(path, filename=path.name, media_type="video/mp4")


@router.get("/preview_cover/{cover_id}")
def preview_cover(cover_id: str, _: CurrentUser = Depends(require_permission("file:download"))) -> dict:
    return {"code": 40400, "message": f"封面文件暂未生成：{cover_id}", "data": None}


@router.get("/download_cover/{cover_id}")
def download_cover(cover_id: str, _: CurrentUser = Depends(require_permission("file:download"))) -> dict:
    return {"code": 40400, "message": f"封面文件暂未生成：{cover_id}", "data": None}


@router.get("/download_asset/{asset_id}")
def download_asset(asset_id: str, _: CurrentUser = Depends(require_permission("file:download"))) -> dict:
    return {"code": 40400, "message": f"资产文件暂未生成：{asset_id}", "data": None}
