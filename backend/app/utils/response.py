#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:45
# @File     : response.py
# @Desc     : API response helpers.

from typing import Any


def success(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


def page_response(items: list[dict[str, Any]], total: int, page: int, page_size: int) -> dict[str, Any]:
    return success({"items": items, "total": total, "page": page, "page_size": page_size})
