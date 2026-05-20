#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:18
# @File     : package.py
# @Desc     : Publish package endpoints.

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.assets import CreatePackageRequest
from app.schemas.auth import CurrentUser
from app.services import asset_service
from app.utils.response import page_response, success

router = APIRouter()


@router.post("/create_package")
def create_package(
    payload: CreatePackageRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("package:manage")),
) -> dict:
    package = asset_service.create_package(db, payload, current_user.id)
    return success({"package_id": package.id, "status": package.package_status, "download_url": f"/api/v1/package/download_package/{package.id}"})


@router.get("/get_package_list")
def get_package_list(
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("package:view")),
) -> dict:
    items, total = asset_service.list_packages(db, keyword, page, page_size)
    return page_response(items, total, page, page_size)


@router.get("/get_package_detail/{package_id}")
def get_package_detail(
    package_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("package:view")),
) -> dict:
    return success(asset_service.get_package_detail(db, package_id))


@router.get("/download_package/{package_id}")
def download_package(
    package_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("file:download")),
) -> FileResponse:
    path = asset_service.get_download_path(db, "package", package_id)
    return FileResponse(path, filename=path.name, media_type="application/zip")
