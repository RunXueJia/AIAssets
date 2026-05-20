#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:45
# @File     : common.py
# @Desc     : Common API schemas.

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T | None = None


class PageData(BaseModel):
    items: list[Any]
    total: int
    page: int = 1
    page_size: int = 20


class IdRequest(BaseModel):
    id: str = Field(min_length=1, max_length=32)
