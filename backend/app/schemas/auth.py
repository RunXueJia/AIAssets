#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:45
# @File     : auth.py
# @Desc     : Authentication schemas.

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class CurrentUser(BaseModel):
    id: str
    username: str
    display_name: str
    role: str
    permissions: list[str]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: CurrentUser
