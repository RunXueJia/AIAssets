#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:12
# @File     : auth.py
# @Desc     : Authentication endpoints.

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.auth import CurrentUser, LoginRequest
from app.services.auth_service import login
from app.utils.response import success

router = APIRouter()


@router.post("/login")
def login_endpoint(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    result = login(db, payload.username, payload.password, request.client.host if request.client else None)
    return success(result.model_dump())


@router.post("/logout")
def logout_endpoint(_: CurrentUser = Depends(get_current_user)) -> dict:
    return success(True)


@router.get("/me")
def me_endpoint(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    return success(current_user.model_dump())
