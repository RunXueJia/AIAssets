#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:12
# @File     : review.py
# @Desc     : Review endpoints.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.schemas.auth import CurrentUser
from app.schemas.generation import (
    ReviewApproveRequest,
    ReviewApproveWithEditRequest,
    ReviewRegenerateRequest,
    ReviewRejectRequest,
)
from app.services import review_service
from app.utils.response import page_response, success

router = APIRouter()


@router.get("/get_review_list")
def get_review_list(
    status: str | None = None,
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission("review:manage")),
) -> dict:
    items, total = review_service.list_reviews(db, status, keyword, page, page_size)
    return page_response(items, total, page, page_size)


@router.post("/approve")
def approve(
    payload: ReviewApproveRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("review:manage")),
) -> dict:
    return success(review_service.approve(db, payload.content_id, payload.content_type, payload.comment, current_user))


@router.post("/approve_with_edit")
def approve_with_edit(
    payload: ReviewApproveWithEditRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("review:manage")),
) -> dict:
    return success(
        review_service.approve_with_edit(
            db,
            payload.content_id,
            payload.content_type,
            payload.edited_payload,
            payload.comment,
            current_user,
        )
    )


@router.post("/reject")
def reject(
    payload: ReviewRejectRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("review:manage")),
) -> dict:
    return success(review_service.reject(db, payload.content_id, payload.content_type, payload.reason, current_user))


@router.post("/regenerate")
def regenerate(
    payload: ReviewRegenerateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("review:manage")),
) -> dict:
    return success(review_service.regenerate(db, payload.content_id, payload.content_type, payload.reason, current_user))
